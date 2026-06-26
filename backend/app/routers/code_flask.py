import asyncio
import subprocess
import sys
import tempfile
import os
import shutil
import uuid
import socket
import time
from pathlib import Path

from fastapi import APIRouter, Depends, Request, Query, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.common import api_response
from app.services.auth_service import decode_token, get_user_by_id

router = APIRouter()

# ---- Constants ----
RUNTIME_DIR = Path(__file__).resolve().parent.parent.parent / "runtime" / "flask_runs"
MAX_RUNS_PER_USER = 1
RUN_TIMEOUT_SECONDS = 600  # 10 minutes
MAX_LOG_LINES = 200
PORT_RANGE_START = 15000
PORT_RANGE_END = 15999

FORBIDDEN_KEYWORDS = [
    "os.system", "os.popen", "subprocess", "socket.socket",
    "shutil.rmtree", "shutil.copy", "shutil.move",
    'open("/etc', "open('/etc", 'open("C:', "open('C:",
    'open("c:', "open('c:", "eval(", "exec(",
    "__import__(", "compile(", "ctypes",
    "pip install", "pip3 install",
    "sys.exit(", "os.remove(", "os.unlink(",
    "os.rmdir(", "os.chmod(", "os.chown",
]
FORBIDDEN_IMPORTS = {"os", "subprocess", "sys", "shutil", "ctypes", "socket", "requests"}


# ---- Request/Response schemas ----
class FlaskFile(BaseModel):
    path: str
    content: str

class FlaskStartRequest(BaseModel):
    project_id: str = ""
    files: list[FlaskFile]

    @field_validator("files")
    @classmethod
    def check_app_py(cls, v):
        if not v:
            raise ValueError("至少需要一个文件")
        has_app = any(f.path == "app.py" for f in v)
        if not has_app:
            raise ValueError("Flask 项目必须包含 app.py 文件")
        return v

class FlaskStopRequest(BaseModel):
    run_id: str


# ---- Run Manager ----
class FlaskRunManager:
    """In-memory manager for Flask run states."""

    def __init__(self):
        self._runs: dict[str, dict] = {}
        self._used_ports: set[int] = set()

    def _allocate_port(self) -> int:
        for port in range(PORT_RANGE_START, PORT_RANGE_END + 1):
            if port in self._used_ports:
                continue
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("127.0.0.1", port))
                    self._used_ports.add(port)
                    return port
            except OSError:
                continue
        raise RuntimeError("没有可用的端口")

    def _release_port(self, port: int):
        self._used_ports.discard(port)

    def _security_check(self, content: str) -> str | None:
        """Check code for dangerous operations. Returns error message or None."""
        lower = content.lower()
        for kw in FORBIDDEN_KEYWORDS:
            if kw in lower:
                return f"检测到危险操作关键字: {kw}"
        # Check imports
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                tokens = stripped.replace(",", " ").split()
                for mod in FORBIDDEN_IMPORTS:
                    if mod in tokens:
                        return f"检测到危险导入: {mod}"
        return None

    def start(self, user_id: int, files: list[FlaskFile]) -> dict:
        # 1. Check existing runs for this user
        existing = self.get_for_user(user_id)
        if existing:
            raise RuntimeError("你已有正在运行的 Flask 项目，请先停止后再启动新的。")

        # 2. Security check on app.py
        app_file = next((f for f in files if f.path == "app.py"), None)
        if not app_file:
            raise RuntimeError("必须包含 app.py 文件")

        err = self._security_check(app_file.content)
        if err:
            raise RuntimeError(f"当前代码包含不安全操作，暂不支持在线运行。({err})")

        # 3. Create run entry
        run_id = uuid.uuid4().hex[:12]
        run_dir = RUNTIME_DIR / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        port = self._allocate_port()

        # 4. Write files
        for f in files:
            file_path = run_dir / f.path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(f.content, encoding="utf-8")

        # 5. Launch subprocess
        env = os.environ.copy()
        env["FLASK_RUN_PORT"] = str(port)
        env["FLASK_RUN_HOST"] = "127.0.0.1"
        env["FLASK_APP"] = "app.py"
        env["PYTHONUNBUFFERED"] = "1"

        log_file = run_dir / ".flask_log.txt"
        log_fp = open(str(log_file), "w")

        proc = subprocess.Popen(
            [sys.executable, "-u", "-m", "flask", "--app", "app", "run", "--host", "127.0.0.1", "--port", str(port)],
            cwd=str(run_dir),
            stdout=log_fp,
            stderr=subprocess.STDOUT,
            env=env,
        )

        # 6. Store run state
        self._runs[run_id] = {
            "run_id": run_id,
            "user_id": user_id,
            "port": port,
            "proc": proc,
            "run_dir": str(run_dir),
            "log_file": str(log_file),
            "log_fp": log_fp,
            "started_at": time.time(),
            "project_id": files[0].content if False else "",
            "status": "running",
        }

        # 7. Schedule timeout cleanup
        asyncio.ensure_future(self._timeout_monitor(run_id))

        return {
            "run_id": run_id,
            "preview_url": f"/api/code/flask/proxy/{run_id}/",
            "logs": [],
        }

    async def _timeout_monitor(self, run_id: str):
        await asyncio.sleep(RUN_TIMEOUT_SECONDS)
        run = self._runs.get(run_id)
        if run and run["status"] == "running":
            self.stop(run_id)

    def stop(self, run_id: str) -> dict:
        run = self._runs.get(run_id)
        if not run:
            raise RuntimeError("运行实例不存在或已过期")

        if run["status"] != "running":
            return {"success": True, "message": "项目已停止"}

        proc: subprocess.Popen = run["proc"]
        try:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        except Exception:
            pass

        # Close log file
        try:
            run["log_fp"].close()
        except Exception:
            pass

        # Release port
        self._release_port(run["port"])

        # Cleanup temp dir
        try:
            shutil.rmtree(run["run_dir"], ignore_errors=True)
        except Exception:
            pass

        run["status"] = "stopped"
        return {"success": True, "message": "项目已停止"}

    def status(self, run_id: str) -> dict | None:
        run = self._runs.get(run_id)
        if not run:
            return None

        # Check if process is still alive
        proc: subprocess.Popen = run["proc"]
        alive = proc.poll() is None

        logs = []
        try:
            with open(run["log_file"], "r") as f:
                lines = f.readlines()
                logs = [l.rstrip() for l in lines[-MAX_LOG_LINES:]]
        except Exception:
            pass

        if not alive and run["status"] == "running":
            run["status"] = "exited"
            self._release_port(run["port"])
            try:
                run["log_fp"].close()
            except Exception:
                pass

        return {
            "status": run["status"],
            "logs": logs,
            "elapsed": round(time.time() - run["started_at"], 1),
        }

    def get_for_user(self, user_id: int) -> dict | None:
        for run in self._runs.values():
            if run["user_id"] == user_id and run["status"] == "running":
                # Double-check process is alive
                if run["proc"].poll() is not None:
                    run["status"] = "exited"
                    self._release_port(run["port"])
                    continue
                return run
        return None


flask_manager = FlaskRunManager()


# ---- API Endpoints ----
@router.post("/flask/start")
async def start_flask_project(
    req: FlaskStartRequest,
    user: User = Depends(get_current_user),
):
    """Start a Flask project in a temp directory."""
    try:
        result = flask_manager.start(user.id, req.files)
        return api_response(data=result, code=200, message="Flask 项目已启动")
    except RuntimeError as e:
        return api_response(code=400, message=str(e))
    except Exception as e:
        return api_response(code=500, message=f"启动失败: {str(e)}")


@router.post("/flask/stop")
async def stop_flask_project(
    req: FlaskStopRequest,
    user: User = Depends(get_current_user),
):
    """Stop a running Flask project."""
    try:
        result = flask_manager.stop(req.run_id)
        return api_response(data=result, code=200, message=result.get("message", "OK"))
    except RuntimeError as e:
        return api_response(code=404, message=str(e))


@router.get("/flask/status/{run_id}")
async def get_flask_status(
    run_id: str,
    user: User = Depends(get_current_user),
):
    """Get status and logs of a Flask run."""
    result = flask_manager.status(run_id)
    if result is None:
        return api_response(code=404, message="运行实例不存在或已过期")
    return api_response(data=result)


# ---- Proxy endpoint for preview ----
@router.api_route("/flask/proxy/{run_id}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
@router.api_route("/flask/proxy/{run_id}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy_flask(
    run_id: str,
    path: str = "",
    request: Request = None,
    token: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Proxy requests to the running Flask instance. Auth via header or ?token= query param."""
    # Auth: check Authorization header first, then query param (for iframe)
    auth_header = request.headers.get("Authorization", "")
    jwt_token = None
    if auth_header.startswith("Bearer "):
        jwt_token = auth_header[7:]
    elif token:
        jwt_token = token

    if not jwt_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_token(jwt_token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    run = flask_manager._runs.get(run_id)
    if not run or run["status"] != "running":
        return api_response(code=404, message="Flask 项目未运行")

    port = run["port"]
    target_url = f"http://127.0.0.1:{port}/{path}"

    # Forward query params except 'token' (auth-only, not for Flask)
    qp = dict(request.query_params)
    qp.pop("token", None)
    if qp:
        from urllib.parse import urlencode
        target_url += f"?{urlencode(qp)}"

    body = await request.body() if request.method in ("POST", "PUT", "PATCH") else None
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    headers.pop("authorization", None)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                follow_redirects=True,
            )
            return StreamingResponse(
                content=resp.iter_bytes(),
                status_code=resp.status_code,
                headers=dict(resp.headers),
            )
        except httpx.ConnectError:
            return api_response(code=502, message="Flask 服务尚未就绪，请稍后刷新")
        except httpx.TimeoutException:
            return api_response(code=504, message="Flask 请求超时")
