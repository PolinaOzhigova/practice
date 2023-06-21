from pydantic import EmailStr
from fastapi import FastAPI
api = FastAPI()

@api.get("/")
async def index():
    return {"Message": "Hello everyone"}

@api.get("/hello")
async def index(user_name: str | None = None):
    if user_name:
        return {"Message": f"Hello {user_name}"}
    else:
        return {"Message": f"Hello anon"}

@api.post("/create_user")
async def create_user(user_name: str, user_mail: EmailStr):
    return {"user_name": user_name, "user_mail": user_mail}