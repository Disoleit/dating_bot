from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    vk_id = Column(Integer, unique=True, nullable=False)
    name = Column(String(50), nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(15), nullable=True)
    city_id = Column(Integer, nullable=True)
    city_title = Column(String(50), nullable=True)

    interactions = relationship('Interactions', back_populates='user')
    candidates = relationship('UsersCandidates', back_populates='user')


class Candidates(Base):
    __tablename__ = 'candidates'

    id = Column(Integer, primary_key=True)
    vk_id = Column(Integer, unique=True, nullable=False)
    name = Column(String(50), nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(15), nullable=True)
    city_id = Column(Integer, nullable=True)
    city_title = Column(String(50), nullable=True)

    photos = relationship('Photos', back_populates='candidate')
    interactions = relationship('Interactions', back_populates='candidate')
    users = relationship('UsersCandidates', back_populates='candidate')


class Photos(Base):
    __tablename__ = 'photos'

    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'), nullable=False)
    first_photo = Column(String(50), nullable=True)
    second_photo = Column(String(50), nullable=True)
    third_photo = Column(String(50), nullable=True)
    account_link = Column(String(50), nullable=False)

    candidate = relationship('Candidates', back_populates='photos')


class Interactions(Base):
    __tablename__ = 'interactions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    candidate_id = Column(Integer, ForeignKey('candidates.id'), nullable=False)
    status = Column(String(15), nullable=False)

    user = relationship('Users', back_populates='interactions')
    candidate = relationship('Candidates', back_populates='interactions')


class UsersCandidates(Base):
    __tablename__ = 'users_candidates'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    candidate_id = Column(Integer, ForeignKey('candidates.id'), nullable=False)

    user = relationship('Users', back_populates='candidates')
    candidate = relationship('Candidates', back_populates='users')