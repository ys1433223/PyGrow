"""
One-shot migration to replace old courses/lessons with data synced from frontend courseData.js.
Run from backend directory: python scripts/migrate_courses.py
"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import async_session
from app.models.course import Course, Lesson
from app.models.ai_note import AINote, AINoteTask
from app.seed import COURSES_DATA


async def migrate():
    async with async_session() as db:
        # 1. Check existing courses
        from sqlalchemy import select
        result = await db.execute(select(Course))
        old_courses = result.scalars().all()
        print(f"Existing courses: {len(old_courses)}")
        for c in old_courses:
            print(f"  [{c.id}] {c.title}")

        new_count = len(COURSES_DATA)
        print(f"\nNew COURSES_DATA: {new_count} courses")
        for c in COURSES_DATA:
            print(f"  [{c['id']}] {c['title']} ({len(c['lessons'])} lessons)")

        if not old_courses:
            print("\nNo existing courses. The normal seed will handle this.")
            return

        # 2. Delete dependent records first (respect FK constraints)
        print("\nDeleting dependent records...")

        # AI notes and tasks reference courses
        ar = await db.execute(text("SELECT COUNT(*) FROM ai_notes"))
        print(f"  ai_notes: {ar.scalar()} rows")
        await db.execute(text("DELETE FROM ai_notes"))

        tr = await db.execute(text("SELECT COUNT(*) FROM ai_note_tasks"))
        print(f"  ai_note_tasks: {tr.scalar()} rows")
        await db.execute(text("DELETE FROM ai_note_tasks"))

        # Course progress
        cr = await db.execute(text("SELECT COUNT(*) FROM course_progress"))
        print(f"  course_progress: {cr.scalar()} rows")
        await db.execute(text("DELETE FROM course_progress"))

        # Course collections
        cr = await db.execute(text("SELECT COUNT(*) FROM course_collections"))
        print(f"  course_collections: {cr.scalar()} rows")
        await db.execute(text("DELETE FROM course_collections"))

        # Course reviews
        try:
            cr = await db.execute(text("SELECT COUNT(*) FROM course_reviews"))
            print(f"  course_reviews: {cr.scalar()} rows")
            await db.execute(text("DELETE FROM course_reviews"))
        except Exception as e:
            print(f"  course_reviews: skipped ({e})")

        # Lessons (FK to courses)
        lr = await db.execute(text("SELECT COUNT(*) FROM lessons"))
        print(f"  lessons: {lr.scalar()} rows")
        await db.execute(text("DELETE FROM lessons"))

        # Now delete old courses
        await db.execute(text("DELETE FROM courses"))
        print("  courses: deleted")

        await db.flush()

        # 3. Insert new courses and lessons
        print("\nInserting new courses and lessons...")
        total_lessons = 0
        for cdata in COURSES_DATA:
            lessons_data = cdata["lessons"]
            course = Course(
                id=cdata["id"],
                title=cdata["title"],
                description=cdata["description"],
                category=cdata["category"],
                category_color=cdata["category_color"],
                icon=cdata["icon"],
                cover_color=cdata["cover_color"],
                bvid=cdata["bvid"],
                sort_order=cdata["sort_order"],
            )
            db.add(course)
            await db.flush()

            for i, (chapter, title, duration, page) in enumerate(lessons_data):
                lesson = Lesson(
                    course_id=course.id,
                    chapter=chapter,
                    title=title,
                    duration=duration,
                    bilibili_page=page,
                    sort_order=i + 1,
                )
                db.add(lesson)
                total_lessons += 1

            print(f"  [{course.id}] {course.title}: {len(lessons_data)} lessons")

        await db.commit()
        print(f"\nMigration complete: {len(COURSES_DATA)} courses, {total_lessons} lessons")


if __name__ == "__main__":
    asyncio.run(migrate())
