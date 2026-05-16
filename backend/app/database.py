import enum
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text, Boolean, JSON, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

#security Load environment variables for secrets and configuration.
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mydatabase.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class AnalyzeStatus(enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

Base = declarative_base()

from app.models.user import User

class UploadedFile(Base):
    __tablename__ = 'uploaded_files'
    id = Column(String, primary_key=True, index=True, unique=True)
    unique_name = Column(String, nullable=False)
    original_name = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    upload_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    analyses = relationship("Analyze", back_populates="file", cascade="all, delete")
    is_deleted = Column(Boolean, default=False)

class Analyze(Base):
    __tablename__ = 'analyze'
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(String, ForeignKey('uploaded_files.id', ondelete="CASCADE"), index=True)
    analyze_type = Column(String)
    result = Column(JSON)
    status = Column(Enum(AnalyzeStatus), default=AnalyzeStatus.pending)
    date_time = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    execution_time = Column(Float, default=0.0)
    file = relationship("UploadedFile", back_populates="analyses")
    suggestions = relationship("Chat_suggestion", back_populates="analyze", cascade="all, delete")
    error_message = Column(Text, nullable=True)

class Chat_suggestion(Base):
    __tablename__ = 'chatsuggestion'
    id = Column(Integer, primary_key=True, autoincrement=True)
    analyze_id = Column(Integer, ForeignKey('analyze.id', ondelete="CASCADE"), index=True)
    suggestion_text = Column(Text)
    suggestion_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    analyze = relationship("Analyze", back_populates="suggestions")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def add_uploaded_file(db, file_id, filename,original_name,file_size,file_type,file_path):
    db_file = UploadedFile(id=file_id, unique_name=filename,original_name=original_name,file_size=file_size,
                           file_type=file_type,file_path=file_path)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file 

def add_analysis_result(db, file_id, analyze_type, result,status=AnalyzeStatus.completed,execution_time = 0.0):
    db_analyze = Analyze(file_id=file_id, analyze_type=analyze_type, result=result,status=status,
                         execution_time=execution_time)
    db.add(db_analyze)
    db_analyze.execution_time = execution_time 
    db.commit()
    db.refresh(db_analyze)
    return db_analyze

def add_chat_suggestion(db, analyze_id, suggestion_text):
    db_suggestion = Chat_suggestion(analyze_id=analyze_id, suggestion_text=suggestion_text)
    db.add(db_suggestion)
    db.commit()
    db.refresh(db_suggestion)
    return db_suggestion

def get_file(db, file_id):
    return db.query(UploadedFile).filter(UploadedFile.id == file_id).first()

def get_analysis(db, file_id):
    return db.query(Analyze).filter(Analyze.file_id == file_id).order_by(Analyze.date_time.desc()).all()

def get_chat_suggestions(db, analyze_id):
    return db.query(Chat_suggestion).filter(Chat_suggestion.analyze_id == analyze_id).order_by(Chat_suggestion.suggestion_time.desc()).all()