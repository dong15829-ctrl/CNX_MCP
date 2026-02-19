from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from utils.logger import get_logger

logger = get_logger(__name__)

DATABASE_URL = "sqlite:///./naver_pipeline.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    logger.info("Initializing Database...")
    # Import models to register them with Base
    import models 
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully.")
