"""Serialized B站 video download queue to avoid 412 rate limiting.

Only one yt-dlp process runs at a time. Pipelines enqueue their download
request and await a Future; the single worker drains the queue sequentially
with a cooldown between downloads.
"""

import asyncio
import logging

logger = logging.getLogger(__name__)

COOLDOWN_SECONDS = 30
RETRY_DELAY_SECONDS = 60
MAX_RETRIES = 1

_queue: asyncio.Queue | None = None
_worker_task: asyncio.Task | None = None
_current_task_id: int | None = None


class DownloadRequest:
    __slots__ = ("task_id", "course_id", "lesson_id", "page", "bvid", "video_path", "future")

    def __init__(self, task_id: int, course_id: int, lesson_id: int | None,
                 page: int | None, bvid: str, video_path: str, future: asyncio.Future):
        self.task_id = task_id
        self.course_id = course_id
        self.lesson_id = lesson_id
        self.page = page
        self.bvid = bvid
        self.video_path = video_path
        self.future = future


async def _download_worker():
    """Single worker: drain queue, download one video at a time with cooldown."""
    global _current_task_id

    from app.services.download_service import download_bilibili_video, find_existing_video
    import os
    import shutil

    while True:
        req: DownloadRequest = await _queue.get()

        try:
            _current_task_id = req.task_id

            # Reuse existing video if already downloaded
            existing = find_existing_video(req.course_id, req.lesson_id, req.page)
            if existing:
                os.makedirs(os.path.dirname(req.video_path), exist_ok=True)
                if existing != req.video_path:
                    shutil.copy2(existing, req.video_path)
                req.future.set_result(req.video_path)
                _current_task_id = None
                _queue.task_done()
                await asyncio.sleep(COOLDOWN_SECONDS)
                continue

            # Download with retry on 412
            last_error = None
            for attempt in range(MAX_RETRIES + 1):
                try:
                    bv_url = f"https://www.bilibili.com/video/{req.bvid}?p={req.page}"
                    result = download_bilibili_video(
                        video_url=bv_url,
                        task_id=req.task_id,
                        course_id=req.course_id,
                        lesson_id=req.lesson_id,
                        page=req.page,
                    )
                    req.future.set_result(result)
                    break
                except Exception as e:
                    last_error = e
                    if "412" in str(e) and attempt < MAX_RETRIES:
                        logger.warning("412 for task %d, retry %d/%d after %ds",
                                       req.task_id, attempt + 1, MAX_RETRIES, RETRY_DELAY_SECONDS)
                        await asyncio.sleep(RETRY_DELAY_SECONDS)
                    else:
                        req.future.set_exception(e)
                        break

            _current_task_id = None
            _queue.task_done()
            await asyncio.sleep(COOLDOWN_SECONDS)

        except Exception as e:
            logger.error("Download worker crashed for task %d: %s", req.task_id, e)
            if not req.future.done():
                req.future.set_exception(e)
            _current_task_id = None
            _queue.task_done()


def start_worker():
    """Idempotent: start the download worker if not already running."""
    global _queue, _worker_task
    if _worker_task is None or _worker_task.done():
        _queue = asyncio.Queue()
        _worker_task = asyncio.create_task(_download_worker())
        logger.info("Download queue worker started")


async def enqueue_download(
    task_id: int,
    course_id: int,
    lesson_id: int | None,
    page: int | None,
    bvid: str,
    video_path: str,
) -> asyncio.Future:
    """Enqueue a download and return a Future that resolves when the download completes."""
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    req = DownloadRequest(
        task_id=task_id,
        course_id=course_id,
        lesson_id=lesson_id,
        page=page,
        bvid=bvid,
        video_path=video_path,
        future=future,
    )
    await _queue.put(req)
    return future


def get_queue_position(task_id: int) -> int | None:
    """Return queue position for a task.

    Returns:
        0 = currently downloading
        1+ = queued position (1 = next in line)
        None = not in queue
    """
    if _current_task_id == task_id:
        return 0
    if _queue is None:
        return None

    position = 1
    for item in list(_queue._queue):
        if isinstance(item, DownloadRequest) and item.task_id == task_id:
            return position
        if isinstance(item, DownloadRequest):
            position += 1
    return None
