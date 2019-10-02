from sqlalchemy import Column, String, Integer, DateTime, Float, Table, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel


ChannelCategory = Table(
    "channelcategory",
    BaseModel.metadata,
    Column("channel_id", Integer, ForeignKey("channel.id")),
    Column("category_id", Integer, ForeignKey("category.id")),
)


class Message(BaseModel):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True)
    user = Column(String, nullable=False)
    text = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    reply_count = Column(Integer, nullable=False)
    reply_users_count = Column(Integer, nullable=False)
    reactions_rate = Column(Float, default=0)
    thread_length = Column(Integer, nullable=False)

    channel_id = Column(Integer, ForeignKey("channel.id"))
    channel = relationship("channel", back_populates="messages")


class Channel(BaseModel):
    __tablename__ = "channel"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)

    categories = relationship(
        "category", secondary=ChannelCategory, back_populates="channels"
    )

    messages = relationship("message", back_populates="channel")


class Category(BaseModel):
    __tablename__ = "category"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    channels = relationship(
        "channel", secondary=ChannelCategory, back_populates="categories"
    )
