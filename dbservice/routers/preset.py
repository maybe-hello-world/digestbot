from dbprovider.PresetDAO import preset_dao
from config import PRESETS_LIMIT
from models import Preset
from typing import List, Optional

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/", response_model=List[Preset])
async def get_presets(
        name: Optional[str] = None,
        user_id: Optional[str] = None,
        include_global: Optional[bool] = None
):
    if name is None and user_id is None and include_global is None:
        return await preset_dao.get_all_presets()

    if name is not None and user_id is None and include_global is None:
        return await preset_dao.get_preset_by_name(name)

    if name is None and include_global is not None:
        return await preset_dao.get_presets(user_id, include_global)

    raise HTTPException(status_code=400, detail="This combination of parameters is not allowed!")


@router.put("/", response_model=Preset)
async def add_or_update_preset(user_id: str, name: str, channels: List[str]):
    result = await preset_dao.add_or_update_preset(user_id, name, channels, max_user_presets_count=PRESETS_LIMIT)
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Maximum amount of presets reached. Please, remove one of existing presets"
        )

    return result


@router.delete("/", response_model=Preset)
async def delete_preset(user_id: str, name: str):
    result = await preset_dao.remove_preset(user_id, name)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Could not find preset with name {name}. Please, check name again."
        )

    return result
