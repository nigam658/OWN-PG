from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not configured")


# When SQLAlchemy needs to talk to MySQL, the engine uses these credentials to connect which is hold DATABASE_URL
if DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "mysql://", "mysql+pymysql://", 1
    )

engine = create_engine(DATABASE_URL) 

# this base tell SQLAlchemy this python class is a databasemodel, otherwise python ignore database class
Base = declarative_base()

SessionLocal = sessionmaker(
    autocommit = False,
    autoflush= False,
    bind=engine
)

# this fucntion help to talk with database with out wrtie same connection command several time
def get_db():      
    db = SessionLocal()
    try:
        yield db

    finally:
        db.close()