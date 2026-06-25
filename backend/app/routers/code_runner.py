import subprocess
import tempfile
import os

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, field_validator

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.code_submission import CodeSubmission
from app.schemas.common import api_response

router = APIRouter()

FORBIDDEN_IMPORTS = {"os", "subprocess", "sys", "shutil", "importlib", "__builtins__", "ctypes", "socket", "requests", "urllib"}

FORBIDDEN_FUNCS = {"open", "exec", "eval", "compile", "__import__", "input"}

TIMEOUT_SECONDS = 5
MAX_CODE_LENGTH = 5000


class CodeRunRequest(BaseModel):
    code: str

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str):
        if len(v) > MAX_CODE_LENGTH:
            raise ValueError(f"代码长度不能超过 {MAX_CODE_LENGTH} 字符")
        code_lower = v.lower()
        for kw in FORBIDDEN_IMPORTS:
            if f"import {kw}" in code_lower or f"from {kw}" in code_lower:
                raise ValueError(f"禁止导入模块: {kw}")
        for kw in FORBIDDEN_FUNCS:
            if kw in code_lower:
                raise ValueError(f"禁止使用: {kw}")
        return v


@router.post("/run")
async def run_code(
    req: CodeRunRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute Python code in a subprocess sandbox. Returns stdout + stderr."""
    code = req.code
    if not code.strip():
        return api_response(400, "代码不能为空")

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            tmp_path = f.name

        proc = subprocess.run(
            ["python", tmp_path],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            cwd=tempfile.gettempdir(),
        )

        stdout = proc.stdout[:5000] if proc.stdout else ""
        stderr = proc.stderr[:5000] if proc.stderr else ""
        return_code = proc.returncode

    except subprocess.TimeoutExpired:
        stdout, stderr, return_code = "", f"代码执行超时（>{TIMEOUT_SECONDS}秒）", -1
    except Exception as e:
        stdout, stderr, return_code = "", f"执行异常: {str(e)}", -1
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    result_text = stdout + ("\n" + stderr if stderr else "")
    db.add(CodeSubmission(
        user_id=user.id, code=code, language="python",
        run_result=result_text[:5000],
        is_correct=(return_code == 0),
    ))
    await db.commit()

    return api_response(data={
        "stdout": stdout,
        "stderr": stderr,
        "return_code": return_code,
    })
