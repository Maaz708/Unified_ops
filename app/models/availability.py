from sqlalchemy import Column, Integer, String, Time, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class AvailabilityRule(Base):
    __tablename__ = "availability_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False) # 0=Monday, 6=Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Optional: Add relationship to Workspace if you have a Workspace model
    workspace = relationship("Workspace", back_populates="availability_rules")

    def __repr__(self):
        return f"<AvailabilityRule(id={self.id}, day_of_week={self.day_of_week}, start_time={self.start_time}, end_time={self.end_time})>"

class BlockedSlot(Base):
    __tablename__ = "blocked_slots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    reason = Column(String, nullable=True)

    # Optional: Add relationship to Workspace
    workspace = relationship("Workspace", back_populates="blocked_slots")

    def __repr__(self):
        return f"<BlockedSlot(id={self.id}, start_datetime={self.start_datetime}, end_datetime={self.end_datetime})>"

# You would also need a 'workspaces' table and model if you don't have one already
class Workspace(Base):
     __tablename__ = "workspaces"
     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
     name = Column(String, nullable=False)
     availability_rules = relationship("AvailabilityRule", back_populates="workspace")
     blocked_slots = relationship("BlockedSlot", back_populates="workspace")