from sqlalchemy import create_engine, Column, String, Integer, ForeignKey
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

engine = create_engine("sqlite:///flashcards.db")
Session = sessionmaker(bind=engine)
Base = declarative_base()


class Users(Base):
    __tablename__ = "users"
    user_id = Column(Integer,primary_key=True)
    username = Column(String, nullable=False,unique=True)
    password = Column(String, nullable=False)
    email = Column(String, nullable=False,unique=True)

class Flashcards(Base):
    __tablename__ = "flashcards"
    card_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    category_id = Column(String, ForeignKey("categories.category_id"))
    tag_id = Column(String, ForeignKey("tags.tag_id"))
    created_date = Column(String,nullable=False)
    deck_id = Column(Integer, ForeignKey("decks.deck_id"))

    

class Categories(Base):
    __tablename__ = "categories"
    category_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

class Decks(Base):
    __tablename__ = "decks"
    deck_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    name = Column(String, nullable=False)

class Tags(Base):
    __tablename__ = "tags"
    tag_id = Column(Integer, primary_key=True)
    tag_name = Column(String, nullable=False,unique=True)

Base.metadata.create_all(engine)

