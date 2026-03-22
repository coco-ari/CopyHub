from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base


class ClipboardItem(Base):
    __tablename__ = "clipboard_items"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now, index=True)