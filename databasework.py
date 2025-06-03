import sqlalchemy
from requests import session
from sqlalchemy.orm import sessionmaker


from models import create_tables, Users, Candidates, Photos, Interactions, UsersCandidates
DSN = 'postgresql://<username>:<password>@<host>:<port>/<database>'
engine = sqlalchemy.create_engine(DSN)

create_tables(engine)

Session = sessionmaker(bind=engine)
session = Session()

session.close()

