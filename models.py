from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.sql.functions import current_timestamp
from enum import IntEnum

Base = declarative_base()


class EventStatus(IntEnum):
  ENABLE = 0
  DELETED = 1


class Event(Base):
  id = Column(Integer, autoincrement=True, primary_key=True)
  status = Column(Integer, index=True)  # EventStatus
  hex_event_id = Column(String(64), unique=True)
  pubkey = Column(String(64), index=True)
  kind = Column(Integer, index=True)
  content = Column(Text)
  tags = Column(Text)
  signature = Column(Text)
  event_created_at = Column(DATETIME(fsp=3))
  received_at = Column(DATETIME(fsp=3), server_default=current_timestamp(3))

  __tablename__ = 'events'

  def __init__(self, hex_event_id, pubkey, kind, content, tags, signature, created_at):
    self.status = EventStatus.ENABLE.value
    self.hex_event_id = hex_event_id
    self.pubkey = pubkey
    self.kind = kind
    self.content = content
    self.tags = tags
    self.signature = signature
    self.event_created_at = created_at
