# from datetime import datetime
# from pydantic import BaseModel, EmailStr
# from typing import List
# from fastapi import FastAPI, Depends, HTTPException

# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker, Session
# from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime

# SQLALCHEMY_DATABASE_URL = "sqlite:///eq_monitor.db"
# engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()

# api = FastAPI()

# # Dependency
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# # Schema FastAPI
# class UserOut(BaseModel):
#     email: EmailStr
    
#     class Config:
#         orm_mode = True


# class UserIn(UserOut):
#     password: str


# class File(BaseModel):
#     path: str
#     start_datetime: datetime
#     end_datetime: datetime

# class UserData(BaseModel):
#     email: str
#     files: List[File]

# class LastUserData(BaseModel):
#     email: str
#     last_files: List[File]

# # Model DB
# class UserDB(Base):
#     __tablename__ = "users"
#     id = Column(Integer, primary_key=True, index=True)
#     email = Column(String, unique=True, index=True)
#     hashed_password = Column(String)

# class FileDB(Base):
#     __tablename__ = "files"
#     id = Column(Integer, primary_key=True, index=True)
#     path = Column(String)
#     start_datetime = Column(DateTime)
#     end_datetime = Column(DateTime)
#     user_id = Column(Integer, ForeignKey("users.id"))

# Base.metadata.create_all(bind=engine)

# # CRUD
# def create_user_db(db: Session, user: UserIn):
#     fake_hashed_password = user.password + "notreallyhashed"
#     db_user = UserDB(email=user.email, hashed_password=fake_hashed_password)
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user

# def get_user_by_email(db: Session, email: str):
#     return db.query(UserDB).filter(UserDB.email == email).first()

# def create_file_db(db: Session, file: File, user_id: int):
#     db_file = FileDB(
#         path=file.path,
#         start_datetime=file.start_datetime,
#         end_datetime=file.end_datetime,
#         user_id=user_id
#     )
#     db.add(db_file)
#     db.commit()
#     db.refresh(db_file)
#     return db_file

# def get_last_user_data(db: Session, email: str):
#     user = get_user_by_email(db, email=email)
#     if not user:
#         return None
    
#     last_files = db.query(FileDB).filter(FileDB.user_id == user.id).order_by(FileDB.id.desc()).limit(1).all()
#     return LastUserData(email=user.email, last_files=last_files)

# def get_data_by_date(db: Session, email: str, date: datetime):
#     user = get_user_by_email(db, email=email)
#     if not user:
#         return None
    
#     files = db.query(FileDB).filter(
#         FileDB.user_id == user.id,
#         FileDB.start_datetime <= date,
#         FileDB.end_datetime >= date
#     ).all()
    
#     return UserData(email=user.email, files=files)

# # Endpoints
# @api.post("/users/", response_model=UserOut)
# def create_user(user: UserIn, db: Session = Depends(get_db)):
#     db_user = get_user_by_email(db, email=user.email)
#     if db_user:
#         raise HTTPException(status_code=400, detail="Email already registered")
#     return create_user_db(db=db, user=user)

# @api.post("/users/data/", response_model=UserData)
# def upload_user_data(user_data: UserData, db: Session = Depends(get_db)):
#     db_user = get_user_by_email(db, email=user_data.email)
#     if not db_user:
#         raise HTTPException(status_code=404, detail="User not found")
    
#     for file_data in user_data.files:
#         create_file_db(db=db, file=file_data, user_id=db_user.id)
    
#     return user_data

# @api.get("/users/last_data/", response_model=LastUserData)
# def get_last_user_data_endpoint(email: str, db: Session = Depends(get_db)):
#     user_data = get_last_user_data(db, email=email)
#     if not user_data:
#         raise HTTPException(status_code=404, detail="User not found")
    
#     return user_data

# @api.get("/users/data_by_date/", response_model=UserData)
# def get_data_by_date_endpoint(email: str, date: datetime, db: Session = Depends(get_db)):
#     user_data = get_data_by_date(db, email=email, date=date)
#     if not user_data:
#         raise HTTPException(status_code=404, detail="User not found or no data available for the specified date")
    
#     return user_data

import os
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, Depends, Form
from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

api = FastAPI()

# Создаем подключение к базе данных
SQLALCHEMY_DATABASE_URL = "sqlite:///uploads.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Определяем модель таблицы для пользователей
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)

# Определяем модель таблицы для файлов
class FileUpload(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    file_path = Column(String)
    upload_date = Column(Date)
    data_type = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="files")

User.files = relationship("FileUpload", order_by=FileUpload.id, back_populates="user")

# Создаем таблицы в базе данных
Base.metadata.create_all(bind=engine)

# Функция зависимости для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Загрузка файла и сохранение в базе данных
@api.post("/upload/")
async def upload_file(
    file: UploadFile = File(...),
    upload_date: str = Form(...),
    data_type: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    file_path = f"uploads/{file.filename}"
    
    # Проверяем, существует ли файл
    if os.path.exists(file_path):
        return {"message": "Файл уже загружен"}
    
    # Создаем директорию "uploads", если она не существует
    os.makedirs("uploads", exist_ok=True)
    
    # Сохраняем файл на сервере
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # Преобразуем строку даты в объект типа date
    upload_date_obj = datetime.strptime(upload_date, "%d.%m.%Y").date()
    
    # Ищем пользователя по email в базе данных
    user = db.query(User).filter(User.email == email).first()
    
    # Если пользователя нет, то создаем нового
    if not user:
        user = User(email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Записываем информацию о файле в базу данных
    db_file = FileUpload(
        filename=file.filename,
        file_path=file_path,
        upload_date=upload_date_obj,
        data_type=data_type,
        user_id=user.id
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    return {"message": "Файл успешно загружен"}

# Создание пользователя
@api.post("/users/")
async def create_user(email: str = Form(...), db: Session = Depends(get_db)):
    user = User(email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Пользователь успешно создан", "user_id": user.id}

# Получение последних загруженных данных для каждого пользователя
@api.get("/latest_data/")
async def get_latest_data(db: Session = Depends(get_db)):
    subquery = db.query(FileUpload.user_id, db.func.max(FileUpload.id).label("latest_id")).group_by(FileUpload.user_id).subquery()
    latest_data = db.query(FileUpload).join(subquery, FileUpload.id == subquery.c.latest_id).all()
    return latest_data

# Обработка данных по пользователю
@api.get("/process_data/{user_id}")
async def process_data(user_id: int, db: Session = Depends(get_db)):
    # Обработка данных для пользователя с указанным user_id
    # В этом эндпоинте можно реализовать необходимую логику обработки данных
    return {"message": f"Обработка данных для пользователя с ID: {user_id}"}
