from typing import Any, Dict, AnyStr, List, Union
from pydantic import BaseModel

JSONObject = Dict[AnyStr, Any]
JSONArray = List[Any]
JSONStructure = Union[JSONArray, JSONObject]


class QnAAnswer(BaseModel):
    text: str
    channel_id: str
    timestamp: str
