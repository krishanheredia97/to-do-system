from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import enum
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Default fallback values if environment variables are not set
DEFAULT_DB_USER = "todo_app"
DEFAULT_DB_PASSWORD = "todo123"
DEFAULT_DB_HOST = "localhost"
DEFAULT_DB_PORT = "5432"
DEFAULT_DB_NAME = "todo_system"

# Build database URL from environment variables or defaults
DATABASE_URL = (
    f"postgresql://"
    f"{os.getenv('DB_USER', DEFAULT_DB_USER)}:"
    f"{os.getenv('DB_PASSWORD', DEFAULT_DB_PASSWORD)}@"
    f"{os.getenv('DB_HOST', DEFAULT_DB_HOST)}:"
    f"{os.getenv('DB_PORT', DEFAULT_DB_PORT)}/"
    f"{os.getenv('DB_NAME', DEFAULT_DB_NAME)}"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Enums for predefined tags and task states
class PredefinedTag(enum.Enum):
    URGENT = "urgent"
    RECURRING = "recurring"
    IMPORTANT = "important"
    BLOCKED = "blocked"

class TaskPhase(enum.Enum):
    PRE_EVENT = "pre_event"
    EVENT = "event"
    POST_EVENT = "post_event"

# Models
class Board(Base):
    __tablename__ = "boards"
    
    id = Column(Integer, primary_key=True)
    external_id = Column(String(5), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    settings = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    projects = relationship("Project", back_populates="board", cascade="all, delete-orphan")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    deadline = Column(DateTime)
    settings = Column(JSON, default={})
    board_id = Column(Integer, ForeignKey("boards.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    board = relationship("Board", back_populates="projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="project", cascade="all, delete-orphan")

class Owner(Base):
    __tablename__ = "owners"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    external_id = Column(String(50), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tasks = relationship("TaskOwner", back_populates="owner")

class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    is_predefined = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tasks = relationship("TaskTag", back_populates="tag")

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tasks = relationship("Task", back_populates="event")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True)
    user_input = Column(Text, nullable=False)
    deadline = Column(DateTime)
    estimated_time = Column(Integer)
    note = Column(Text)
    is_completed = Column(Boolean, default=False)
    attachment_url = Column(String(500))
    phase = Column(Enum(TaskPhase))
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    parent_task_id = Column(Integer, ForeignKey("tasks.id"))
    event_id = Column(Integer, ForeignKey("events.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    project = relationship("Project", back_populates="tasks")
    event = relationship("Event", back_populates="tasks")
    subtasks = relationship("Task", backref="parent", remote_side=[id])
    owners = relationship("TaskOwner", back_populates="task")
    tags = relationship("TaskTag", back_populates="task")

class Note(Base):
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True)
    user_input = Column(Text, nullable=False)
    attachment_url = Column(String(500))
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"))
    phase = Column(Enum(TaskPhase))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    project = relationship("Project", back_populates="notes")
    event = relationship("Event")

class TaskOwner(Base):
    __tablename__ = "task_owners"
    
    task_id = Column(Integer, ForeignKey("tasks.id"), primary_key=True)
    owner_id = Column(Integer, ForeignKey("owners.id"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    task = relationship("Task", back_populates="owners")
    owner = relationship("Owner", back_populates="tasks")

class TaskTag(Base):
    __tablename__ = "task_tags"
    
    task_id = Column(Integer, ForeignKey("tasks.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    task = relationship("Task", back_populates="tags")
    tag = relationship("Tag", back_populates="tasks")

def init_db():
    Base.metadata.create_all(engine)
    
    session = SessionLocal()
    
    # Create predefined tags if they don't exist
    for tag in PredefinedTag:
        existing_tag = session.query(Tag).filter_by(name=tag.value).first()
        if not existing_tag:
            new_tag = Tag(name=tag.value, is_predefined=True)
            session.add(new_tag)
    
    session.commit()
    session.close()

def test_connection():
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            print("Successfully connected to the database!")
            return True
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return False

if __name__ == "__main__":
    print(f"Attempting to connect to: {DATABASE_URL}")
    test_connection()
    init_db()