import os
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import async_session
from app.models.course import Course, Lesson
from app.models.ai_note import AINoteTask, AINote
from app.services.llm_service import generate_ai_notes
from app.services.speech_service import transcribe_audio
from app.services.video_service import extract_audio
from app.services.download_service import (
    download_bilibili_video,
    find_existing_video,
    get_video_duration,
    cleanup_temp_files,
)

STATUS_MESSAGES = {
    "not_started": "未开始",
    "queued": "排队中",
    "downloading": "正在获取视频",
    "extracting_audio": "正在提取音频",
    "transcribing": "正在语音转文字",
    "summarizing": "正在生成AI笔记",
    "completed": "解析完成",
    "failed": "解析失败",
}

PIPELINE_STAGES = [
    ("queued", 0, 0.5),
    ("downloading", 10, 2),
    ("extracting_audio", 30, 2),
    ("transcribing", 55, 2),
    ("summarizing", 80, 2),
]


async def run_ai_note_pipeline(task_id: int, course_id: int, lesson_id: int | None = None, bvid_override: str | None = None, page_override: int | None = None):
    """Background pipeline: download B站 video → extract audio → transcribe → AI notes."""
    async with async_session() as db:
        video_path = None
        audio_path = None
        try:
            # Fetch course + lesson info
            result = await db.execute(select(Course).where(Course.id == course_id))
            course = result.scalar_one_or_none()
            course_title = course.title if course else f"课程#{course_id}"

            lesson = None
            bilibili_page = page_override or None
            effective_bvid = bvid_override or (course.bvid if course else None)
            if lesson_id:
                lr = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
                lesson = lr.scalar_one_or_none()
                if lesson:
                    if not bilibili_page:
                        bilibili_page = lesson.bilibili_page
                    course_title = f"{course_title} - {lesson.title}" if course else lesson.title

            # File paths keyed by task_id to avoid collisions
            video_path = f"temp/video/c{course_id}_l{lesson_id or 0}_p{bilibili_page or 1}_t{task_id}.mp4"
            audio_path = f"temp/audio/c{course_id}_l{lesson_id or 0}_p{bilibili_page or 1}_t{task_id}.wav"
            transcript = ""

            # Walk through pipeline stages
            for status, progress, duration in PIPELINE_STAGES:
                if status == "downloading":
                    await _update_task(db, task_id, status, progress, STATUS_MESSAGES[status])

                    # Check if video already exists for this lesson
                    existing = find_existing_video(course_id, lesson_id, bilibili_page)
                    if existing:
                        import shutil
                        os.makedirs(os.path.dirname(video_path), exist_ok=True)
                        if existing != video_path:
                            shutil.copy2(existing, video_path)
                    elif effective_bvid and bilibili_page:
                        # Construct B站 single-P URL and download
                        bv_url = f"https://www.bilibili.com/video/{effective_bvid}?p={bilibili_page}"
                        download_bilibili_video(
                            video_url=bv_url,
                            task_id=task_id,
                            course_id=course_id,
                            lesson_id=lesson_id,
                            page=bilibili_page,
                        )
                    else:
                        # No B站 BV ID or no page — skip download, keep mock flow
                        await asyncio.sleep(duration)

                elif status == "extracting_audio":
                    await _update_task(db, task_id, status, progress, STATUS_MESSAGES[status])

                    if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
                        extract_audio(video_path, audio_path)
                    else:
                        # No video — skip extraction, transcribe will use mock
                        pass

                elif status == "transcribing":
                    await _update_task(db, task_id, status, progress, STATUS_MESSAGES[status])
                    transcript = await transcribe_audio(audio_path)

                elif status == "summarizing":
                    await _update_task(db, task_id, status, progress, STATUS_MESSAGES[status])
                    video_duration_sec = get_video_duration(video_path) if video_path and os.path.exists(video_path) else 0.0
                    note_data = await generate_ai_notes(course_title, transcript, video_duration_sec)

                else:
                    await _update_task(db, task_id, status, progress, STATUS_MESSAGES[status])
                    await asyncio.sleep(duration)

            # Save AI note with lesson_id and bvid/page for flexible lookup
            note = AINote(
                course_id=course_id,
                lesson_id=lesson_id,
                bvid=effective_bvid,
                bilibili_page=bilibili_page,
                task_id=task_id,
                summary=note_data["summary"],
                notes=note_data["notes"],
                highlights=note_data["highlights"],
                transcript=note_data.get("transcript", transcript),
                errors=note_data["errors"],
                suggestions=note_data["suggestions"],
                source_type="ai_generated",
            )
            db.add(note)

            # Mark task completed
            task = await db.get(AINoteTask, task_id)
            if task:
                task.status = "completed"
                task.progress = 100
                task.message = "AI 笔记已生成，可查看课程简介、知识点笔记、视频看点和易错提醒。"
                task.finished_at = datetime.utcnow()

            await db.commit()

        except Exception as e:
            await db.rollback()
            try:
                await _update_task(db, task_id, "failed", 0, "AI 笔记生成失败，请稍后重试。", str(e))
                await db.commit()
            except Exception:
                pass
        finally:
            # Cleanup temp video and audio, keep DB records
            cleanup_temp_files(task_id)


async def _update_task(db: AsyncSession, task_id: int, status: str, progress: int, message: str, error: str = None):
    task = await db.get(AINoteTask, task_id)
    if task:
        task.status = status
        task.progress = progress
        task.message = message
        if error:
            task.error_message = error
        await db.commit()
