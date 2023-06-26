from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import List
from fastapi import FastAPI, Depends, HTTPException

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime

SQLALCHEMY_DATABASE_URL = "sqlite:///eq_monitor.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

api = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Schema FastAPI
class UserOut(BaseModel):
    email: EmailStr
    
    class Config:
        orm_mode = True


class UserIn(UserOut):
    password: str


class File(BaseModel):
    path: str
    start_datetime: datetime
    end_datetime: datetime

class UserData(BaseModel):
    email: str
    files: List[File]

class LastUserData(BaseModel):
    email: str
    last_files: List[File]

# Model DB
class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class FileDB(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    path = Column(String)
    start_datetime = Column(DateTime)
    end_datetime = Column(DateTime)
    user_id = Column(Integer, ForeignKey("users.id"))

Base.metadata.create_all(bind=engine)

# CRUD
def create_user_db(db: Session, user: UserIn):
    fake_hashed_password = user.password + "notreallyhashed"
    db_user = UserDB(email=user.email, hashed_password=fake_hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(db: Session, email: str):
    return db.query(UserDB).filter(UserDB.email == email).first()

def create_file_db(db: Session, file: File, user_id: int):
    db_file = FileDB(
        path=file.path,
        start_datetime=file.start_datetime,
        end_datetime=file.end_datetime,
        user_id=user_id
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def get_last_user_data(db: Session, email: str):
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    
    last_files = db.query(FileDB).filter(FileDB.user_id == user.id).order_by(FileDB.id.desc()).limit(1).all()
    return LastUserData(email=user.email, last_files=last_files)

def get_data_by_date(db: Session, email: str, date: datetime):
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    
    files = db.query(FileDB).filter(
        FileDB.user_id == user.id,
        FileDB.start_datetime <= date,
        FileDB.end_datetime >= date
    ).all()
    
    return UserData(email=user.email, files=files)

# Endpoints
@api.post("/users/", response_model=UserOut)
def create_user(user: UserIn, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return create_user_db(db=db, user=user)

@api.post("/users/data/", response_model=UserData)
def upload_user_data(user_data: UserData, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, email=user_data.email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    for file_data in user_data.files:
        create_file_db(db=db, file=file_data, user_id=db_user.id)
    
    return user_data

@api.get("/users/last_data/", response_model=LastUserData)
def get_last_user_data_endpoint(email: str, db: Session = Depends(get_db)):
    user_data = get_last_user_data(db, email=email)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user_data

@api.get("/users/data_by_date/", response_model=UserData)
def get_data_by_date_endpoint(email: str, date: datetime, db: Session = Depends(get_db)):
    user_data = get_data_by_date(db, email=email, date=date)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found or no data available for the specified date")
    
    return user_data

