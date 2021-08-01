from fastapi import APIRouter
from .v1 import users, authentication, files

api_v1_router = APIRouter()

api_v1_router.include_router(authentication.router)
api_v1_router.include_router(users.router)
api_v1_router.include_router(files.router)
