from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
import asyncio

# 使用 UTC+8 时区
TZ_SHANGHAI = timezone(timedelta(hours=8))

from database import SessionLocal, engine, Base
from models import ClipboardItem

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CopyHub API", version="1.0.0")

# WebSocket 连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

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


def to_local_time(dt: datetime) -> str:
    """将 naive datetime 转换为 UTC+8 时区的 ISO 格式字符串"""
    return dt.replace(tzinfo=timezone.utc).astimezone(TZ_SHANGHAI).isoformat()


@app.get("/api/items")
def get_items():
    """获取所有剪贴板内容，按时间倒序"""
    db = SessionLocal()
    try:
        items = db.query(ClipboardItem).order_by(ClipboardItem.created_at.desc()).all()
        return [{
            "id": item.id,
            "content": item.content,
            "created_at": to_local_time(item.created_at)
        } for item in items]
    finally:
        db.close()


@app.post("/api/items")
async def create_item(item: ItemCreate):
    """新增剪贴板内容"""
    if not item.content or not item.content.strip():
        raise HTTPException(status_code=400, detail="内容不能为空")

    db = SessionLocal()
    try:
        new_item = ClipboardItem(content=item.content.strip())
        db.add(new_item)
        db.commit()
        db.refresh(new_item)

        created_at_str = to_local_time(new_item.created_at)

        # 广播新消息给所有客户端
        await manager.broadcast({
            "type": "create",
            "data": {
                "id": new_item.id,
                "content": new_item.content,
                "created_at": created_at_str
            }
        })

        return {
            "id": new_item.id,
            "content": new_item.content,
            "created_at": created_at_str
        }
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