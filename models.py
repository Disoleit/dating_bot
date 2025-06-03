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

    interactions = relationship('Interactions', back_populates='user')
    user_candidates = relationship('UsersCandidates', back_populates='user')

class Candidates(Base):
    __tablename__ = 'candidates'

    id = sq.Column(sq.Integer, primary_key=True)
    vk_id = sq.Column(sq.Integer, unique=True, nullable=False)
    name = sq.Column(sq.String(length=50), nullable=False)
    age = sq.Column(sq.Integer, nullable=False)
    gender = sq.Column(sq.String(length=15), nullable=False)
    city = sq.Column(sq.String(length=50), nullable=False)

    photos = relationship('Photos', back_populates='candidate')
    interactions = relationship('Interactions', back_populates='candidate')
    user_candidates = relationship('UsersCandidates', back_populates='candidate')

class UsersCandidates(Base):

    __tablename__ = 'users_candidates'
    id = sq.Column(sq.Integer, primary_key=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey('users.id'), nullable=False)
    candidate_id = sq.Column(sq.Integer, sq.ForeignKey('candidates.id'), nullable=False)

    user = relationship('Users', back_populates='user_candidates')
    candidate = relationship('Candidates', back_populates='user_candidates')

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