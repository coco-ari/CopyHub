from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import os

from database import SessionLocal, engine, Base
from models import ClipboardItem

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CopyHub API", version="1.0.0")

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


# 响应模型
class ItemResponse(BaseModel):
    id: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


@app.get("/api/items", response_model=list[ItemResponse])
def get_items():
    """获取所有剪贴板内容，按时间倒序"""
    db = SessionLocal()
    try:
        items = db.query(ClipboardItem).order_by(ClipboardItem.created_at.desc()).all()
        return items
    finally:
        db.close()


@app.post("/api/items", response_model=ItemResponse)
def create_item(item: ItemCreate):
    """新增剪贴板内容"""
    if not item.content or not item.content.strip():
        raise HTTPException(status_code=400, detail="内容不能为空")

    db = SessionLocal()
    try:
        new_item = ClipboardItem(content=item.content.strip())
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        return new_item
    finally:
        db.close()


@app.delete("/api/items/{item_id}")
def delete_item(item_id: int):
    """删除剪贴板内容"""
    db = SessionLocal()
    try:
        item = db.query(ClipboardItem).filter(ClipboardItem.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="内容不存在")

        db.delete(item)
        db.commit()
        return {"message": "删除成功"}
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "CopyHub API", "docs": "/docs"}