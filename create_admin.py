from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from auth import create_user
import os
DB_URL = os.environ.get('DATABASE_URL','postgresql://postgres:postgres@db:5432/skyshield')
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)
if __name__ == '__main__':
    s = Session()
    username = os.environ.get('ADMIN_USER','admin')
    password = os.environ.get('ADMIN_PASS','password')
    create_user(s, username, password, role='admin')
    print('created admin user')
