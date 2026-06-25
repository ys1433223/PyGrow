from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class LessonOut(BaseModel):
    id: int
    title: str
    chapter: Optional[str] = None
    duration: Optional[str] = None
    bilibili_page: Optional[int] = None
    sort_order: int

    model_config = {"from_attributes": True}


class CourseOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    category_color: Optional[str] = None
    icon: Optional[str] = None
    cover_color: Optional[str] = None
    bvid: Optional[str] = None
    sort_order: int

    model_config = {"from_attributes": True}


class CourseDetailOut(CourseOut):
    lessons: List[LessonOut] = []


class ProgressUpdate(BaseModel):
    last_lesson_id: Optional[int] = None
    progress_percent: Optional[float] = None
    is_completed: Optional[bool] = None
