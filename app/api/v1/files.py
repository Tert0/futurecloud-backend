import os
from typing import List

from fastapi import APIRouter, File, HTTPException
from fastapi_framework import Config, ConfigField, get_logger
import aiofiles
from aiofiles.os import mkdir
from shutil import rmtree
from pathlib import Path

router = APIRouter(prefix="/files", tags=["files"])

logger = get_logger(__name__)


class FilesConfig(Config):
    CONFIG_PATH = "config.yaml"
    CONFIG_TYPE = "yaml"

    data_path: Path = ConfigField("/data/")


@router.on_event("startup")
async def on_startup():
    if not os.path.exists(FilesConfig.data_path):  # TODO change to async
        await mkdir(FilesConfig.data_path)


async def check_file_path(base_path: Path, user_path: Path):
    if ".." in user_path.parts:  # TODO Eventually not safe against Path Traversal Vulnerabilities
        logger.warning(f"[SECURITY] Found dots in '{user_path}'")
        raise HTTPException(status_code=400, detail="Blocked Path Traversal Vulnerability")
    print(user_path, Path(os.path.relpath(user_path, "/")), user_path.is_absolute(),
          base_path / Path(os.path.relpath(user_path, "/")), base_path / user_path)
    if user_path.is_absolute():
        user_path = Path(os.path.relpath(user_path, "/"))
    if (base_path / user_path) == base_path:
        return
    if Path(base_path).absolute() not in Path(
            os.path.realpath(base_path / user_path)).absolute().parents:  # TODO change to async
        logger.warning(f"[SECURITY] Paths doesn't match. Users Path: '{base_path / user_path}' and Base "
                       f"Path: '{base_path}'")
        raise HTTPException(status_code=400, detail="Blocked Path Traversal Vulnerability")


async def path_to_relative(path: Path) -> Path:
    return Path(os.path.relpath(path, "/")) if path.is_absolute() else path


@router.post("/")
async def upload(file_path: Path, file_data: bytes = File(...)):
    await check_file_path(FilesConfig.data_path, file_path)

    file_path = await path_to_relative(file_path)

    if not (FilesConfig.data_path / file_path).parent.exists():  # TODO change to async
        (FilesConfig.data_path / file_path).parent.mkdir(parents=True)  # TODO change to async
    async with aiofiles.open(FilesConfig.data_path / file_path, "wb") as file:
        await file.write(file_data)
    return "Successfully uploaded file"


@router.delete("/")
async def delete(file_path: Path):
    await check_file_path(FilesConfig.data_path, file_path)

    file_path = FilesConfig.data_path / file_path

    if file_path.exists():  # TODO change to async
        if file_path.is_dir():  # TODO change to async
            if len(os.listdir(file_path)) == 0:  # TODO change to async
                await aiofiles.os.rmdir(file_path)
                return "Deleted folder successfully"
            rmtree(file_path)  # TODO change to async
            return "Deleted folder recursive successfully"
        elif file_path.is_file():  # TODO change to async
            await aiofiles.os.remove(file_path)
            return "Deleted file successfully"
        else:
            raise HTTPException(500, "Cant delete Path")
    else:
        raise HTTPException(404, detail="Path does not exists")


@router.get("/")
async def list_dir(path: Path = Path("/")):
    await check_file_path(FilesConfig.data_path, path)

    path = FilesConfig.data_path / await path_to_relative(path)
    try:
        items: List[str] = os.listdir(path)  # TODO change to async
        response = []
        for item in items:
            item_path: Path = path / item
            item_type = "folder" if item_path.is_dir() else ("file" if item_path.is_file() else "unknown")
            data = {"name": item, "type": item_type}
            response.append(data)
        return response
    except NotADirectoryError:
        raise HTTPException(400, "Path is not a Directory")
    except FileNotFoundError:
        raise HTTPException(400, "Path does not exists")
