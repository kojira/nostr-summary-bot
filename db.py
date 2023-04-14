import socket
import time
from sqlalchemy.orm import sessionmaker
from sqlalchemy import update, desc
from sqlalchemy.dialects.mysql import insert

from sqlalchemy import create_engine
import json

from models import (
    Base,
    Event,
    EventStatus,
)

from contextlib import contextmanager

import os

MYSQL_USER = os.environ.get("MYSQL_USER")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE")


def wait_db(host="db", port=3306, retries=30):
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  for x in range(retries):
    try:
      s.connect((host, port))
      s.close()
      return True
    except socket.error:
      print(f"waiting db...{x}")
      time.sleep(1)

  s.close()
  return False


host = "db"
# host = "localhost"

wait_db(host=host)

url = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{host}/{MYSQL_DATABASE}?charset=utf8mb4"
)
engine = create_engine(url, echo=False, pool_recycle=3600, pool_pre_ping=True)
Base.metadata.create_all(bind=engine)
Session = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
)


@contextmanager
def session_scope():
  session = Session()
  try:
    yield session
    session.commit()
  except:
    import sys
    import traceback
    from datetime import datetime

    exc_type, exc_value, exc_traceback = sys.exc_info()
    err_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + repr(
        traceback.format_exception(exc_type, exc_value, exc_traceback)
    )
    sys.stderr.write(err_text)
    print(err_text)
    session.rollback()
    raise
  finally:
    session.close()


def getEvents(_from, _to, kind):
  with session_scope() as session:
    query = session.query(Event).filter(Event.status == EventStatus.ENABLE.value)\
                                .filter(Event.kind == kind)\
                                .filter(Event.event_created_at >= _from)\
                                .filter(Event.event_created_at < _to)

    events = query.all()
    return events
