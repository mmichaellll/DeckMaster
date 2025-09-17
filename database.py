from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime

engine = create_engine("sqlite:///flashcards.db", future=True)
Session = sessionmaker(bind=engine, future=True)
Base = declarative_base()


class Users(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)

    decks = relationship("Decks", back_populates="user", cascade="all, delete-orphan")
    flashcards = relationship("Flashcards", back_populates="user", cascade="all, delete-orphan")


class Flashcards(Base):
    __tablename__ = "flashcards"
    card_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.category_id"))
    tag_id = Column(Integer, ForeignKey("tags.tag_id"))
    created_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    deck_id = Column(Integer, ForeignKey("decks.deck_id"))

    user = relationship("Users", back_populates="flashcards")
    category = relationship("Categories", back_populates="flashcards")
    tag = relationship("Tags", back_populates="flashcards")
    deck = relationship("Decks", back_populates="flashcards")


class Categories(Base):
    __tablename__ = "categories"
    category_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    flashcards = relationship("Flashcards", back_populates="category")


class Decks(Base):
    __tablename__ = "decks"
    deck_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    name = Column(String, nullable=False)

    user = relationship("Users", back_populates="decks")
    flashcards = relationship("Flashcards", back_populates="deck")


class Tags(Base):
    __tablename__ = "tags"
    tag_id = Column(Integer, primary_key=True)
    tag_name = Column(String, nullable=False, unique=True)

    flashcards = relationship("Flashcards", back_populates="tag")


Base.metadata.create_all(engine)

