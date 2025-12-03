from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Table, Column, Integer, String, Boolean, Text, Time, Numeric, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class TableExemple(Base):
    __tablename__ = "exemple"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    

