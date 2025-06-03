import sqlalchemy
from requests import session
from sqlalchemy.orm import sessionmaker


from models import create_tables, Users, Candidates, Photos, Interactions
DSN = 'postgresql://postgres:130006@localhost:5432/dating_bot'
engine = sqlalchemy.create_engine(DSN)

create_tables(engine)

Session = sessionmaker(bind=engine)
session = Session()

session.close()

