from typing import List

from fastapi import APIRouter, HTTPException
from dbprovider.IgnoreDAO import ignore_dao
from config import IGNORE_LIMIT

router = APIRouter()

MAX_IGNORE_REACHED = (
    "Maximum number of users to ignore for this user achieved. "
    "Please, consider removing one of your existing ignore entries to be allowed to add another one. "
    "Of ask admins to increase limits if you really hate so many people :D."
)
IGNORE_ALREADY_PRESENTED = "Specified user is already in the ignore list."
IGNORE_NOT_FOUND = "Specified user not found."
EMPTY_IDS = "Either ID of author of the request or ignored user is not specified."
PARSE_ERROR = "Database interaction error. Answer couldn't be parsed."


@router.get("/", response_model=List[str])
async def get_ignore_list(author_id: str):
    return [x['ignore_username'] for x in await ignore_dao.get_ignore_list(author_id)]


@router.get("/count", response_model=int)
async def get_total_ignored():
    return await ignore_dao.get_total_ignored()


@router.put("/")
async def add_ignore_entry(author_id: str, ignore_id: str):
    current_amount = await ignore_dao.get_ignore_list_length(author_id)

    if not (author_id.strip() and ignore_id.strip()):
        raise HTTPException(status_code=400, detail=EMPTY_IDS)

    if current_amount >= IGNORE_LIMIT:
        raise HTTPException(status_code=400, detail=MAX_IGNORE_REACHED)

    result = await ignore_dao.insert_into_ignore_list(author_id=author_id, ignore_id=ignore_id)
    if not result:
        raise HTTPException(status_code=400, detail=IGNORE_ALREADY_PRESENTED)


@router.delete("/")
async def remove_ignore_entry(author_id: str, ignore_id: str):
    if not (author_id.strip() and ignore_id.strip()):
        raise HTTPException(status_code=400, detail=EMPTY_IDS)

    result = await ignore_dao.delete_from_ignore_list(author_id=author_id, ignore_id=ignore_id)
    if not result:
        raise HTTPException(status_code=404, detail=IGNORE_NOT_FOUND)
