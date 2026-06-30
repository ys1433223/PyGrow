from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.routers import auth, courses, users, assessment, practice, gamification, reports, home, code_runner, code_flask, ai_mentor, projects, notes, community, leaderboard, admin, reviews, favorites, ai_notes, debug, pet, promotion
from app.database import engine, Base
from app.services.download_queue import start_worker
from sqlalchemy import text


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Migration: add source column if it doesn't exist
        try:
            await conn.run_sync(lambda c: c.execute(text(
                "ALTER TABLE questions ADD COLUMN source VARCHAR(20) DEFAULT 'question_bank'"
            )))
        except Exception:
            pass
        # Migration: add note_time_text, note_type, updated_at to notes
        for col_sql in [
            "ALTER TABLE notes ADD COLUMN time_text VARCHAR(20) DEFAULT '00:00'",
            "ALTER TABLE notes ADD COLUMN note_type VARCHAR(20) DEFAULT '重点'",
            "ALTER TABLE notes ADD COLUMN updated_at DATETIME",
        ]:
            try:
                await conn.run_sync(lambda c, s=col_sql: c.execute(text(s)))
            except Exception:
                pass
    from app.seed import seed
    import asyncio
    await seed()
    start_worker()
    yield


app = FastAPI(title="PyGrow API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount project root for static resource files (mind maps, PPTs, code samples)
_project_root = Path(__file__).resolve().parent.parent.parent
app.mount("/api/resources/static", StaticFiles(directory=str(_project_root), html=False), name="resources_static")

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/user", tags=["user"])
app.include_router(courses.router, prefix="/api/courses", tags=["courses"])
app.include_router(assessment.router, prefix="/api/assessment", tags=["assessment"])
app.include_router(practice.router, prefix="/api/practice", tags=["practice"])
app.include_router(gamification.router, prefix="/api/gamification", tags=["gamification"])
app.include_router(reports.router, prefix="/api/report", tags=["report"])
app.include_router(home.router, prefix="/api/home", tags=["home"])
app.include_router(code_runner.router, prefix="/api/code", tags=["code-runner"])
app.include_router(code_flask.router, prefix="/api/code", tags=["code-flask"])
app.include_router(ai_mentor.router, prefix="/api/ai", tags=["ai-mentor"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(notes.router, prefix="/api/notes", tags=["notes"])
app.include_router(community.router, prefix="/api/community", tags=["community"])
app.include_router(leaderboard.router, prefix="/api/leaderboard", tags=["leaderboard"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["reviews"])
app.include_router(favorites.router, prefix="/api/favorites", tags=["favorites"])
app.include_router(ai_notes.router, prefix="/api", tags=["ai-notes"])
app.include_router(debug.router, prefix="/api", tags=["debug"])
app.include_router(pet.router, prefix="/api/pet", tags=["pet"])
app.include_router(promotion.router, tags=["promotion"])
