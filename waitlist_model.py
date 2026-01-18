from sqlalchemy import Column, String, DateTime
from database import Base
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

class Waitlist(Base):
    __tablename__ = "waitlist"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
