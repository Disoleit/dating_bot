import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Users(Base):
    __tablename__ = 'users'

    id = sq.Column(sq.Integer, primary_key=True)
    vk_id = sq.Column(sq.Integer, unique=True, nullable=False)
    name = sq.Column(sq.String(length=50), nullable=False)
    age = sq.Column(sq.Integer, nullable=False)
    gender = sq.Column(sq.String(length=15), nullable=False)
    city = sq.Column(sq.String(length=50), nullable=False)

    candidates = relationship('Candidates', back_populates='user')
    interactions = relationship('Interactions', back_populates='user')


class Candidates(Base):
    __tablename__ = 'candidates'

    id = sq.Column(sq.Integer, primary_key=True)
    vk_id = sq.Column(sq.Integer, unique=True, nullable=False)
    name = sq.Column(sq.String(length=50), nullable=False)
    age = sq.Column(sq.Integer, nullable=False)
    gender = sq.Column(sq.String(length=15), nullable=False)
    city = sq.Column(sq.String(length=50), nullable=False)
    matched_for = sq.Column(sq.Integer, sq.ForeignKey('users.id'), nullable=False)

    user = relationship('Users', back_populates='candidates')
    photos = relationship('Photos', back_populates='candidate')
    interactions = relationship('Interactions', back_populates='candidate')


class Photos(Base):
    __tablename__ = 'photos'

    id = sq.Column(sq.Integer, primary_key=True)
    candidate_id = sq.Column(sq.Integer, sq.ForeignKey('candidates.id'), nullable=False)
    first_photo = sq.Column(sq.String(length=50), nullable=False)
    second_photo = sq.Column(sq.String(length=50), nullable=False)
    third_photo = sq.Column(sq.String(length=50), nullable=False)
    account_link = sq.Column(sq.String(length=50), nullable=False)

    candidate = relationship('Candidates', back_populates='photos')


class Interactions(Base):
    __tablename__ = 'interactions'

    id = sq.Column(sq.Integer, primary_key=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey('users.id'), nullable=False)
    candidate_id = sq.Column(sq.Integer, sq.ForeignKey('candidates.id'), nullable=False)
    status = sq.Column(sq.String(length=15), nullable=False)

    user = relationship('Users', back_populates='interactions')
    candidate = relationship('Candidates', back_populates='interactions')


def create_tables(engine):
    Base.metadata.create_all(engine)