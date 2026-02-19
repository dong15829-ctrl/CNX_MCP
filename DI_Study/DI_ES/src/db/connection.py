import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pymysql

from src.config import DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SQLAlchemy Setup
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_recycle=3600,
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency for obtaining a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Legacy PyMySQL Connection (referencing existing code pattern)
class Database:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.connection = None
        return cls._instance

    def connect(self):
        """Establish a connection to the database."""
        try:
            self.connection = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASS,
                database=DB_NAME,
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=10
            )
            logger.info("Successfully connected to MySQL database.")
            return self.connection
        except pymysql.MySQLError as e:
            logger.error(f"Failed to connect to MySQL: {e}")
            raise

    def get_connection(self):
        """Get existing connection or create a new one."""
        if self.connection and self.connection.open:
            return self.connection
        return self.connect()

    def close(self):
        """Close the connection."""
        if self.connection and self.connection.open:
            self.connection.close()
            logger.info("Database connection closed.")

def get_db_connection():
    db = Database()
    return db.get_connection()
