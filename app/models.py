from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    arch = Column(String)
    version = Column(String)
    imageId = Column(String)
    date = Column(Date)
    virt = Column(String)
    provider = Column(String)
    region = Column(String)
