from models import Category
from typing import List, Optional

from fastapi import APIRouter

router = APIRouter()


@router.get("/", response_model=List[Category])
async def get_categories(
        name: Optional[str] = None,
        user_id: Optional[str] = None,
        include_global: Optional[bool] = None
):
    raise NotImplementedError


def get_all_categories() -> List[Category]:
    raise NotImplementedError


def get_category_by_name(name: str) -> Category:
    raise NotImplementedError


def get_some_categories(user_id: Optional[str], include_global: bool = True) -> List[Category]:
    raise NotImplementedError


@router.put("/", response_model=Category)
async def add_or_update_category(user_id: str, name: str, channels: List[str]):
    raise NotImplementedError


@router.delete("/", response_model=Category)
async def delete_category(user_id: str, name: str):
    raise NotImplementedError
