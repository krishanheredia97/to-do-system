# api.py
from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from db import SessionLocal, Task, Board, Project, Note, Event, Owner, Tag, TaskOwner, TaskTag
from fastapi.middleware.cors import CORSMiddleware
import logging
from utils.id_generator import generate_random_id

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Pydantic models for request/response
class BoardBase(BaseModel):
    name: str
    settings: dict = {}
    external_id: Optional[str] = None

    class Config:
        from_attributes = True

class BoardCreate(BoardBase):
    pass

class BoardResponse(BoardBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProjectBase(BaseModel):
    name: str
    deadline: Optional[datetime] = None
    settings: dict = {}
    board_id: int

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class TaskBase(BaseModel):
    user_input: str
    deadline: Optional[datetime] = None
    estimated_time: Optional[int] = None
    note: Optional[str] = None
    attachment_url: Optional[str] = None
    phase: Optional[str] = None
    project_id: int
    parent_task_id: Optional[int] = None
    event_id: Optional[int] = None

class TaskCreate(TaskBase):
    owner_ids: List[int] = []
    tag_ids: List[int] = []

class TaskResponse(TaskBase):
    id: int
    is_completed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class NoteBase(BaseModel):
    user_input: str
    attachment_url: Optional[str] = None
    project_id: int
    event_id: Optional[int] = None
    phase: Optional[str] = None

class NoteCreate(NoteBase):
    pass

class NoteResponse(NoteBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Todo System API")

# Update CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Board endpoints
@app.post("/boards/", response_model=BoardResponse)
def create_board(board: BoardCreate, db: Session = Depends(get_db)):
    try:
        logger.debug(f"Attempting to create board with data: {board}")
        board_data = board.dict()
        board_data['external_id'] = generate_random_id()
        db_board = Board(**board_data)
        db.add(db_board)
        db.commit()
        db.refresh(db_board)
        logger.debug(f"Successfully created board: {db_board.id}")
        return db_board
    except Exception as e:
        logger.error(f"Error creating board: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/boards/", response_model=List[BoardResponse])
def get_boards(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Board).offset(skip).limit(limit).all()

@app.get("/boards/{board_id}", response_model=BoardResponse)
def get_board(board_id: int, db: Session = Depends(get_db)):
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    return board

# Project endpoints
@app.post("/projects/", response_model=ProjectResponse)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    db_project = Project(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@app.get("/projects/", response_model=List[ProjectResponse])
def get_projects(board_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(Project)
    if board_id:
        query = query.filter(Project.board_id == board_id)
    return query.offset(skip).limit(limit).all()

# Task endpoints
@app.post("/tasks/", response_model=TaskResponse)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    # Extract owner_ids and tag_ids
    owner_ids = task.owner_ids
    tag_ids = task.tag_ids
    task_data = task.dict(exclude={'owner_ids', 'tag_ids'})
    
    # Create task
    db_task = Task(**task_data)
    db.add(db_task)
    db.commit()
    
    # Add owners
    for owner_id in owner_ids:
        task_owner = TaskOwner(task_id=db_task.id, owner_id=owner_id)
        db.add(task_owner)
    
    # Add tags
    for tag_id in tag_ids:
        task_tag = TaskTag(task_id=db_task.id, tag_id=tag_id)
        db.add(task_tag)
    
    db.commit()
    db.refresh(db_task)
    return db_task

@app.get("/tasks/", response_model=List[TaskResponse])
def get_tasks(
    project_id: Optional[int] = None,
    is_completed: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Task)
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if is_completed is not None:
        query = query.filter(Task.is_completed == is_completed)
    return query.offset(skip).limit(limit).all()

@app.put("/tasks/{task_id}/complete")
def complete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.is_completed = True
    task.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "success"}

# Note endpoints
@app.post("/notes/", response_model=NoteResponse)
def create_note(note: NoteCreate, db: Session = Depends(get_db)):
    db_note = Note(**note.dict())
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

@app.get("/notes/", response_model=List[NoteResponse])
def get_notes(project_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(Note)
    if project_id:
        query = query.filter(Note.project_id == project_id)
    return query.offset(skip).limit(limit).all()

@app.delete("/boards/{board_id}")
def delete_board(board_id: int, db: Session = Depends(get_db)):
    logger.debug(f"Attempting to delete board with ID: {board_id}")
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        logger.error(f"Board with ID {board_id} not found")
        raise HTTPException(status_code=404, detail="Board not found")
    try:
        db.delete(board)
        db.commit()
        logger.debug(f"Successfully deleted board with ID: {board_id}")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error deleting board: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/projects/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    logger.debug(f"Attempting to delete project with ID: {project_id}")
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        logger.error(f"Project with ID {project_id} not found")
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        db.delete(project)
        db.commit()
        logger.debug(f"Successfully deleted project with ID: {project_id}")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error deleting project: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"status": "success"}

@app.put("/boards/{board_id}")
def update_board(board_id: int, board: BoardCreate, db: Session = Depends(get_db)):
    db_board = db.query(Board).filter(Board.id == board_id).first()
    if not db_board:
        raise HTTPException(status_code=404, detail="Board not found")
    for key, value in board.dict().items():
        setattr(db_board, key, value)
    db.commit()
    return db_board

@app.put("/projects/{project_id}")
def update_project(project_id: int, project: ProjectCreate, db: Session = Depends(get_db)):
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    for key, value in project.dict().items():
        setattr(db_project, key, value)
    db.commit()
    return db_project