from dbprovider.CategoryDAO import category_dao
from config import PRESETS_LIMIT
from models import Category
from typing import List, Optional

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/", response_model=List[Category])
async def get_categories(
        name: Optional[str] = None,
        user_id: Optional[str] = None,
        include_global: Optional[bool] = None
):
    if name is None and user_id is None and include_global is None:
        return await category_dao.get_all_categories()

    if name is not None and user_id is None and include_global is None:
        return await category_dao.get_category_by_name(name)

    if name is None and include_global is not None:
        return await category_dao.get_categories(user_id, include_global)

    raise HTTPException(status_code=400, detail="This combination of parameters is not allowed!")


@router.put("/", response_model=Category)
async def add_or_update_category(user_id: str, name: str, channels: List[str]):
    result = await category_dao.add_or_update_category(user_id, name, channels, max_user_categories_count=PRESETS_LIMIT)
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Maximum amount of categories reached. Please, remove one of existing categories"
        )

    return result


@router.delete("/", response_model=Category)
async def delete_category(user_id: str, name: str):
    result = await category_dao.remove_category(user_id, name)
    if not result:
        raise HTTPException(
            status_code=400,
            detail=f"Could not find category with name {name}. Please, check name again."
        )

    return result
