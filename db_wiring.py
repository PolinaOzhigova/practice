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
