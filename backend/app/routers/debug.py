from fastapi import APIRouter
from pydantic import BaseModel

from app.schemas.common import api_response
from app.services.download_service import download_bilibili_video, parse_bilibili_url

router = APIRouter()


class DownloadTestRequest(BaseModel):
    video_url: str
    page: int | None = None


@router.post("/debug/download-bilibili")
async def debug_download_bilibili(req: DownloadTestRequest):
    """Debug endpoint: test B站 single-P video download.

    POST body:
        video_url: B站 video URL (any format)
        page: optional page number override

    Returns:
        success: bool
        video_path: path to downloaded file
        canonical_url: the parsed canonical URL
        error_message: error string if failed
    """
    canonical = parse_bilibili_url(req.video_url, req.page)
    if not canonical:
        return api_response(400, "无法解析B站视频链接，请检查 URL 格式")

    try:
        video_path = download_bilibili_video(
            video_url=canonical,
            task_id=99999,   # debug task ID
            course_id=0,
            lesson_id=0,
            page=req.page or 1,
        )
        import os
        size_mb = os.path.getsize(video_path) / 1024 / 1024 if os.path.exists(video_path) else 0
        return api_response(data={
            "success": True,
            "video_path": video_path,
            "canonical_url": canonical,
            "size_mb": round(size_mb, 1),
        })
    except Exception as e:
        return api_response(data={
            "success": False,
            "canonical_url": canonical,
            "error_message": str(e),
        })
