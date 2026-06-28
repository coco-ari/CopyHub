from sqlalchemy import Boolean, Column, Integer, String, DateTime
from datetime import datetime
import os
from database import Base

MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", "10000"))


class ClipboardItem(Base):
    __tablename__ = "clipboard_items"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String(MAX_CONTENT_LENGTH), nullable=False)
    created_at = Column(DateTime, default=datetime.now, index=True)
    is_favorite = Column(Boolean, default=False, nullable=False, index=True)
    favorited_at = Column(DateTime, nullable=True, index=True)