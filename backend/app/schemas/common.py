from pydantic import BaseModel
from typing import Optional, Any


def api_response(code: int = 200, message: str = "success", data: Any = None) -> dict:
    return {"code": code, "message": message, "data": data}
