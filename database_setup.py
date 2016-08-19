"""Set up the database schema and ORM mappings.
"""
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import datetime

Base = declarative_base()


class User(Base):

    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    email = Column(String(50), nullable=False)
    picture = Column(String(250))
    google_id = Column(String(250))
    categories = relationship('Category')
    items = relationship('Item')


class Category(Base):

    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    # Allow this entity to be serialized as JSON
    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name
        }


class Item(Base):

    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    name = Column(String(80))
    description = Column(String(500))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    date_added = Column(DateTime, default=datetime.datetime.now)

    # Allow this entity to be serialized as JSON
    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category_id': self.category_id
        }


engine = create_engine('sqlite:///catalog.db')
Base.metadata.create_all(engine)
