from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_models import Base

DATABASE_URL = "sqlite:///./crm.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}, # Needed for SQLite
    echo=False # Set to True to see generated SQL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """
    Initialize the database and create tables if they don't exist.
    """
    try:
        Base.metadata.create_all(bind=engine)
        print("Database initialized successfully.")
    except Exception as e:
        print(f"An error occurred during database initialization: {e}")

def get_db():
    """
    Dependency to get a DB session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
