import asyncio
import os
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 使用 UTC+8 时区
TZ_SHANGHAI = timezone(timedelta(hours=8))

from database import SessionLocal, engine, Base
from models import ClipboardItem


def ensure_schema():
    Base.metadata.create_all(bind=engine)
    if engine.dialect.name != "sqlite":
        return

    with engine.begin() as connection:
        columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(clipboard_items)")}
        if "is_favorite" not in columns:
            connection.exec_driver_sql(
                "ALTER TABLE clipboard_items ADD COLUMN is_favorite BOOLEAN NOT NULL DEFAULT 0"
            )
        if "favorited_at" not in columns:
            connection.exec_driver_sql(
                "ALTER TABLE clipboard_items ADD COLUMN favorited_at DATETIME"
            )


# 创建数据库表
ensure_schema()

app = FastAPI(title="CopyHub API", version="1.0.0")

MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", "10000"))
DEFAULT_ITEMS_LIMIT = int(os.getenv("DEFAULT_ITEMS_LIMIT", "100"))
MAX_ITEMS_LIMIT = int(os.getenv("MAX_ITEMS_LIMIT", "200"))
RETENTION_ITEMS = int(os.getenv("RETENTION_ITEMS", "500"))
BROADCAST_TIMEOUT_SECONDS = float(os.getenv("BROADCAST_TIMEOUT_SECONDS", "3"))

# WebSocket 连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def _send(self, connection: WebSocket, message: dict):
        try:
            await asyncio.wait_for(
                connection.send_json(message),
                timeout=BROADCAST_TIMEOUT_SECONDS,
            )
            return connection, True
        except Exception:
            return connection, False

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return

        results = await asyncio.gather(
            *(self._send(connection, message) for connection in list(self.active_connections))
        )

        for connection, ok in results:
            if not ok:
                self.disconnect(connection)

manager = ConnectionManager()

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求模型
class ItemCreate(BaseModel):
    content: str


class FavoriteUpdate(BaseModel):
    is_favorite: bool


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 连接端点"""
    await manager.connect(websocket)
    try:
        while True:
            # 保持连接，等待客户端消息（主要是心跳）
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


def to_local_time(dt: datetime) -> str:
    """将 naive datetime 转换为 UTC+8 时区的 ISO 格式字符串"""
    return dt.replace(tzinfo=timezone.utc).astimezone(TZ_SHANGHAI).isoformat()


def serialize_item(item: ClipboardItem) -> dict:
    return {
        "id": item.id,
        "content": item.content,
        "created_at": to_local_time(item.created_at),
        "is_favorite": bool(item.is_favorite),
        "favorited_at": to_local_time(item.favorited_at) if item.favorited_at else None,
    }


def normalize_content(content: str) -> str:
    if not content or not content.strip():
        raise HTTPException(status_code=400, detail="内容不能为空")

    normalized = content.strip()
    if len(normalized) > MAX_CONTENT_LENGTH:
        raise HTTPException(
            status_code=413,
            detail=f"内容不能超过 {MAX_CONTENT_LENGTH} 个字符",
        )

    return normalized


def prune_old_items(db) -> list[int]:
    if RETENTION_ITEMS <= 0:
        return []

    stale_items = (
        db.query(ClipboardItem.id)
        .filter(ClipboardItem.is_favorite.is_(False))
        .order_by(ClipboardItem.created_at.desc(), ClipboardItem.id.desc())
        .offset(RETENTION_ITEMS)
        .all()
    )
    stale_ids = [item_id for (item_id,) in stale_items]
    if stale_ids:
        db.query(ClipboardItem).filter(ClipboardItem.id.in_(stale_ids)).delete(
            synchronize_session=False
        )
        db.commit()

    return stale_ids


@app.get("/api/items")
def get_items(
    limit: int = Query(DEFAULT_ITEMS_LIMIT, ge=1, le=MAX_ITEMS_LIMIT),
    offset: int = Query(0, ge=0),
    favorites: bool = Query(False),
):
    """获取剪贴板内容，按时间倒序分页；收藏视图按收藏时间倒序。"""
    db = SessionLocal()
    try:
        query = db.query(ClipboardItem)
        if favorites:
            query = query.filter(ClipboardItem.is_favorite.is_(True)).order_by(
                ClipboardItem.favorited_at.desc(),
                ClipboardItem.created_at.desc(),
                ClipboardItem.id.desc(),
            )
        else:
            query = query.order_by(ClipboardItem.created_at.desc(), ClipboardItem.id.desc())

        items = query.offset(offset).limit(limit).all()
        return [serialize_item(item) for item in items]
    finally:
        db.close()


@app.post("/api/items")
async def create_item(item: ItemCreate):
    """新增剪贴板内容"""
    db = SessionLocal()
    try:
        new_item = ClipboardItem(content=normalize_content(item.content))
        db.add(new_item)
        db.commit()
        db.refresh(new_item)

        payload = serialize_item(new_item)
        stale_ids = prune_old_items(db)

        await manager.broadcast({"type": "create", "data": payload})
        for stale_id in stale_ids:
            await manager.broadcast({"type": "delete", "data": {"id": stale_id}})

        return payload
    finally:
        db.close()


@app.put("/api/items/{item_id}")
async def update_item(item_id: int, item: ItemCreate):
    """修改剪贴板内容"""
    db = SessionLocal()
    try:
        existing_item = db.query(ClipboardItem).filter(ClipboardItem.id == item_id).first()
        if not existing_item:
            raise HTTPException(status_code=404, detail="内容不存在")

        existing_item.content = normalize_content(item.content)
        db.commit()
        db.refresh(existing_item)

        payload = serialize_item(existing_item)
        await manager.broadcast({"type": "update", "data": payload})

        return payload
    finally:
        db.close()


@app.patch("/api/items/{item_id}/favorite")
async def update_favorite(item_id: int, favorite: FavoriteUpdate):
    """切换收藏状态"""
    db = SessionLocal()
    try:
        existing_item = db.query(ClipboardItem).filter(ClipboardItem.id == item_id).first()
        if not existing_item:
            raise HTTPException(status_code=404, detail="内容不存在")

        existing_item.is_favorite = favorite.is_favorite
        existing_item.favorited_at = datetime.now() if favorite.is_favorite else None
        db.commit()
        db.refresh(existing_item)

        payload = serialize_item(existing_item)
        await manager.broadcast({"type": "update", "data": payload})

        return payload
    finally:
        db.close()


@app.delete("/api/items/{item_id}")
async def delete_item(item_id: int):
    """删除剪贴板内容"""
    db = SessionLocal()
    try:
        item = db.query(ClipboardItem).filter(ClipboardItem.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="内容不存在")

        db.delete(item)
        db.commit()

        # 广播删除消息给所有客户端
        await manager.broadcast({
            "type": "delete",
            "data": {"id": item_id}
        })

        return {"message": "删除成功"}
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "CopyHub API", "docs": "/docs"}
