import os
import shutil
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi import FastAPI, File, UploadFile, Depends, Form, Query
import pytest

from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey, func
from sqlalchemy.orm import sessionmaker, relationship, joinedload, declarative_base
from sqlalchemy.orm import Session

from main import api, get_db, User, FileUpload, FileUploadData, Base, engine

# Создаем тестового клиента
client = TestClient(api)

# Фикстура для создания сессии базы данных
@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()

# Тест для загрузки файла
def test_upload_file(db):
    os.makedirs("uploads", exist_ok=True)

    # Данные для теста
    file_content = b"Hello, World!"
    date_start = "01.07.2023"
    date_end = "02.07.2023"
    data_type = "Test"
    email = "test@example.com"

    # Отправляем POST-запрос на загрузку файла
    response = client.post(
        "/upload/",
        files={"file": ("test_file.txt", file_content, "text/plain")},
        data={
            "date_start": date_start,
            "date_end": date_end,
            "data_type": data_type,
            "email": email,
        },
    )

    # Проверяем, что запрос выполнен успешно
    assert response.status_code == 200
    assert response.json() == {"message": "Файл успешно загружен"}

    # Проверяем, что файл загружен на сервер
    assert os.path.exists("uploads/test_file.txt")

    # Проверяем, что информация о файле добавлена в базу данных
    file_data = db.query(FileUpload).filter_by(filename="test_file.txt").first()
    assert file_data is not None
    assert file_data.date_start.strftime("%d.%m.%Y") == date_start
    assert file_data.date_end.strftime("%d.%m.%Y") == date_end
    assert file_data.data_type == data_type

# Тест для создания пользователя
def test_create_user(db):
    # Данные для теста
    email = "test2@example.com"

    # Отправляем POST-запрос на создание пользователя
    response = client.post("/users/", data={"email": email})

    # Проверяем, что запрос выполнен успешно
    assert response.status_code == 200
    assert response.json() == {
        "message": "Пользователь успешно создан",
        "user_id": 2,
    }

    # Проверяем, что пользователь добавлен в базу данных
    user = db.query(User).filter_by(email=email).first()
    assert user is not None
    assert user.id == 2

# Тест для поиска данных по дате
def test_get_data_by_date(db):
    # Данные для теста
    date_start = "01.01.2023"
    date_end = "02.01.2023"

    # Создаем тестовые данные в базе данных
    file_data_1 = FileUpload(
        filename="test_file1.txt",
        file_path="uploads/test_file1.txt",
        date_start=datetime.strptime(date_start, "%d.%m.%Y").date(),
        date_end=datetime.strptime(date_end, "%d.%m.%Y").date(),
        data_type="Test",
        user_id=1,
    )
    file_data_2 = FileUpload(
        filename="test_file2.txt",
        file_path="uploads/test_file2.txt",
        date_start=datetime.strptime(date_start, "%d.%m.%Y").date(),
        date_end=datetime.strptime(date_end, "%d.%m.%Y").date(),
        data_type="Test",
        user_id=2,
    )
    db.add(file_data_1)
    db.add(file_data_2)
    db.commit()

    # Отправляем GET-запрос на поиск данных по дате
    response = client.get(
        "/search_by_date/",
        params={"date_start": date_start, "date_end": date_end},
    )


    # Проверяем, что запрос выполнен успешно
    assert response.status_code == 200

    # Проверяем, что возвращены корректные данные
    assert response.json() == [
        {
            "id": file_data_1.id,
            "filename": "test_file1.txt",
            "file_path": "uploads/test_file1.txt",
            "date_start": date_start,
            "date_end": date_end,
            "data_type": "Test",
            "user_id": 1,
        },
        {
            "id": file_data_2.id,
            "filename": "test_file2.txt",
            "file_path": "uploads/test_file2.txt",
            "date_start": date_start,
            "date_end": date_end,
            "data_type": "Test",
            "user_id": 2,
        },
    ]

# Тест для получения последних загруженных данных для каждого пользователя
def test_get_latest_data(db):

    # Отправляем GET-запрос на получение последних загруженных данных для каждого пользователя
    response = client.get("/latest_data/")

    # Проверяем, что запрос выполнен успешно
    assert response.status_code == 200

    # Проверяем, что возвращены корректные данные
    assert response.json() == [
        {
            "filename": "test_file1.txt",
            "file_path": "uploads/test_file1.txt",
            "date_end": "2023-01-02",
            "user_id": 1,
            "date_start": "2023-01-01",
            "id": 2,
            "data_type": "Test"
        },
        {
            "filename": "test_file2.txt",
            "file_path": "uploads/test_file2.txt",
            "date_end": "2023-01-02",
            "user_id": 2,
            "date_start": "2023-01-01",
            "id": 3,
            "data_type": "Test"
        }
    ]