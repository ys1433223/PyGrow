import subprocess
import tempfile
import os
import time
import json

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

PYGROW_PRELUDE = r"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json as _pygrow_json
import base64 as _pygrow_b64
import io as _pygrow_io
import os as _pygrow_os

_pygrow_images = []
_pygrow_tables = []

try:
    import pandas as pd
except ImportError:
    pd = None

_pygrow_show_original = plt.show
def _pygrow_show(*args, **kwargs):
    for fignum in plt.get_fignums():
        fig = plt.figure(fignum)
        buf = _pygrow_io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img_b64 = _pygrow_b64.b64encode(buf.read()).decode('utf-8')
        _pygrow_images.append({
            'type': 'image/png',
            'data': 'data:image/png;base64,' + img_b64
        })
        buf.close()
    plt.close('all')
plt.show = _pygrow_show

def display(obj):
    if hasattr(obj, 'to_html'):
        try:
            html = obj.to_html(index=True, classes='pygrow-dataframe')
            shape = list(obj.shape) if hasattr(obj, 'shape') else [len(obj), 1]
            _pygrow_tables.append({
                'type': 'dataframe',
                'html': html,
                'shape': shape
            })
            print(f"[DataFrame: {shape[0]} rows x {shape[1]} columns]")
        except Exception as _e:
            print(f"[display error: {_e}]")
    else:
        print(repr(obj))
"""

PYGROW_EPILOGUE = r"""
_result_path = _pygrow_os.environ.get('PYGROW_RESULT_FILE', '')
if _result_path:
    try:
        _result = _pygrow_json.dumps({'images': _pygrow_images, 'tables': _pygrow_tables})
        with open(_result_path, 'w', encoding='utf-8') as _f:
            _f.write(_result)
    except Exception:
        pass
"""


def _build_prelude_code(user_code: str) -> str:
    """Wrap user code with PyGrow prelude (matplotlib Agg, display(), plt.show patch)
    and epilogue (write results JSON). User code is wrapped in try/except so the
    epilogue always runs even if the user code raises."""
    indented = '\n'.join('    ' + line for line in user_code.split('\n'))
    wrapped = (
        PYGROW_PRELUDE + '\n'
        + '_pygrow_error = None\n'
        + 'try:\n'
        + indented + '\n'
        + 'except Exception as _pygrow_err:\n'
        + '    import traceback\n'
        + '    traceback.print_exc()\n'
        + '    _pygrow_error = True\n'
        + PYGROW_EPILOGUE + '\n'
        + 'if _pygrow_error:\n'
        + '    import sys as _pygrow_sys\n'
        + '    _pygrow_sys.exit(1)\n'
    )
    return wrapped


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
    """Execute Python code in a subprocess sandbox.
    Returns stdout, stderr, images (matplotlib), tables (pandas DataFrame), and execution_time."""
    code = req.code
    if not code.strip():
        return api_response(400, "代码不能为空")

    result_file = tempfile.mktemp(suffix='.json')
    tmp_path = None
    start = time.time()
    images = []
    tables = []

    try:
        full_code = _build_prelude_code(code)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(full_code)
            tmp_path = f.name

        env = os.environ.copy()
        env["PYGROW_RESULT_FILE"] = result_file

        proc = subprocess.run(
            ["python", tmp_path],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            cwd=tempfile.gettempdir(),
            env=env,
        )

        stdout = proc.stdout[:5000] if proc.stdout else ""
        stderr = proc.stderr[:5000] if proc.stderr else ""
        return_code = proc.returncode

        # Read captured images/tables from the result JSON file
        try:
            with open(result_file, 'r', encoding='utf-8') as rf:
                captured = json.load(rf)
                images = captured.get('images', [])
                tables = captured.get('tables', [])
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    except subprocess.TimeoutExpired:
        stdout, stderr, return_code = "", f"代码执行超时（>{TIMEOUT_SECONDS}秒）", -1
    except Exception as e:
        stdout, stderr, return_code = "", f"执行异常: {str(e)}", -1
    finally:
        try:
            if tmp_path:
                os.unlink(tmp_path)
            os.unlink(result_file)
        except Exception:
            pass

    elapsed = time.time() - start

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
        "execution_time": round(elapsed, 3),
        "images": images,
        "tables": tables,
    })
