import os
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, Depends, Form, Query
from pydantic import EmailStr, BaseModel
from typing import List
from loguru import logger

from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey, func
from sqlalchemy.orm import sessionmaker, relationship, joinedload, declarative_base
from sqlalchemy.orm import Session

api = FastAPI()

logger.add("./logs/info.log", retention="1 week")

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
    date_start = Column(Date)
    date_end = Column(Date)
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

# Создаем модель данных для объекта FileUpload
class FileUploadData(BaseModel):
    id: int
    filename: str
    file_path: str
    date_start: str
    date_end: str
    data_type: str
    user_id: int

# Загрузка файла и сохранение в базе данных
@api.post("/upload/")
async def upload_file(
    file: UploadFile = File(...),
    date_start: str = Form(...),
    date_end: str = Form(...),
    data_type: str = Form(...),
    email: EmailStr = Form(...),
    db: Session = Depends(get_db)
):
    logger.info("Uploading a file")
    file_path = f"uploads/{file.filename}"
    
    # Проверяем, существует ли файл
    if os.path.exists(file_path):
        logger.error("File is already exsist")
        return {"message": "Файл уже загружен"}
    
    # Создаем директорию "uploads", если она не существует
    os.makedirs("uploads", exist_ok=True)
    
    # Сохраняем файл на сервере
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # Преобразуем строку даты в объект типа date
    date_start_obj = datetime.strptime(date_start, "%d.%m.%Y").date()
    date_end_obj = datetime.strptime(date_end, "%d.%m.%Y").date()
    
    # Ищем пользователя по email в базе данных
    user = db.query(User).filter(User.email == email).first()
    
    # Если пользователя нет, то создаем нового
    if not user:
        logger.info("Creating a user")
        user = User(email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Записываем информацию о файле в базу данных
    db_file = FileUpload(
        filename=file.filename,
        file_path=file_path,
        date_start=date_start_obj,
        date_end=date_end_obj,
        data_type=data_type,
        user_id=user.id
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    logger.info("File successfully uploaded")
    return {"message": "Файл успешно загружен"}

# Создание пользователя
@api.post("/users/")
async def create_user(email: EmailStr = Form(...), db: Session = Depends(get_db)):
    logger.info("Creating a user")
    
    user = User(email=email)
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"User {user} created successfully")

    return {"message": "Пользователь успешно создан", "user_id": user.id}

@api.get("/search_by_date/", response_model=List[FileUploadData])
async def get_data_by_date(
    date_start: str = Query(..., description="Дата начала в формате дд.мм.гггг"),
    date_end: str = Query(..., description="Дата окончания в формате дд.мм.гггг"),
    db: Session = Depends(get_db)
):
    # Преобразуем строки дат в объекты типа date
    date_start_obj = datetime.strptime(date_start, "%d.%m.%Y").date()
    date_end_obj = datetime.strptime(date_end, "%d.%m.%Y").date()

    # Запрос к базе данных для поиска данных в указанном диапазоне дат
    data = db.query(FileUpload).filter(
        FileUpload.date_start >= date_start_obj,
        FileUpload.date_end <= date_end_obj
    ).options(joinedload(FileUpload.user)).all()

    # Преобразование результатов запроса в список объектов FileUploadData
    result = []
    for item in data:
        file_upload_data = FileUploadData(
            id=item.id,
            filename=item.filename,
            file_path=item.file_path,
            date_start=item.date_start.strftime("%d.%m.%Y"),
            date_end=item.date_end.strftime("%d.%m.%Y"),
            data_type=item.data_type,
            user_id=item.user_id
        )
        result.append(file_upload_data)

    return result

# Получение последних загруженных данных для каждого пользователя
@api.get("/latest_data/")
async def get_latest_data(db: Session = Depends(get_db)):
    subquery = db.query(FileUpload.user_id, func.max(FileUpload.id).label("latest_id")).group_by(FileUpload.user_id).subquery()
    latest_data = db.query(FileUpload).join(subquery, FileUpload.id == subquery.c.latest_id).all()
    return latest_data

# Обработка данных по пользователю
@api.get("/make_picture/{user_id}")
async def process_data(user_id: int, db: Session = Depends(get_db)):
    # Обработка данных для пользователя с указанным user_id
    # В этом эндпоинте можно реализовать необходимую логику обработки данных
    return {"message": f"Обработка данных для пользователя с ID: {user_id}"}