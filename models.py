from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(50), default='viewer')

class Camera(Base):
    __tablename__ = 'cameras'
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    source = Column(String(512), nullable=False)
    enabled = Column(Integer, default=1)
    infer_interval = Column(Float, default=0.5)
    conf_threshold = Column(Float, default=0.45)

class Incident(Base):
    __tablename__ = 'incidents'
    id = Column(Integer, primary_key=True)
    camera_id = Column(Integer, ForeignKey('cameras.id'))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    label = Column(String(128))
    conf = Column(Float)
    track_id = Column(Integer, default=-1)
    thumbnail_path = Column(String(512))
    extra = Column(Text)

    camera = relationship('Camera')
