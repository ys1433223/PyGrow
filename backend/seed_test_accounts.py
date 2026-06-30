"""
Seed 5 test accounts with differentiated data profiles.

Usage:
    cd backend
    python seed_test_accounts.py

All 5 accounts use password: PyGrow123456
Each has cookies=12 for testing pet adventure.
"""

import asyncio
import random
from datetime import date, datetime, timedelta

from sqlalchemy import select, text, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session, engine, Base
from app.models.user import User
from app.models.course import Course, CourseProgress
from app.models.gamification import Question, PracticeRecord, DailyTask, UserDailyTask
from app.models.community import Post, PostLike, Comment, CommentLike
from app.models.project import Project, ProjectSubmission
from app.models.favorite import Favorite
from app.models.pet import PetProfile, PetCookieRecord
from app.models.promotion import PromotionExam
from app.services.auth_service import hash_password

# ---------------------------------------------------------------------------
# Test account definitions
# ---------------------------------------------------------------------------
TEST_ACCOUNTS = [
    {
        "id": 1001,
        "username": "test_student_01",
        "email": "test_student_01@pygrow.local",
        "nickname": "测试新生一号",
        "current_rank": "萌新小白",
        "current_exp": 100,
        "total_exp": 80,
        "rank_exp_limit": 100,
        "can_promotion_test": 1,
        "courses_completed": 0,
        "practice_total": 15,
        "practice_correct_rate": 0.55,
        "wrong_count": 7,
        "projects_done": 1,
        "project_scores": [65],
        "posts_count": 1,
        "post_likes_received": 10,
        "cookies": 12,
    },
    {
        "id": 1002,
        "username": "test_student_02",
        "email": "test_student_02@pygrow.local",
        "nickname": "勤奋学徒小亮",
        "current_rank": "勤学学徒",
        "current_exp": 200,
        "total_exp": 280,
        "rank_exp_limit": 200,
        "can_promotion_test": 1,
        "courses_completed": 1,
        "practice_total": 40,
        "practice_correct_rate": 0.60,
        "wrong_count": 16,
        "projects_done": 1,
        "project_scores": [72],
        "posts_count": 2,
        "post_likes_received": 20,
        "cookies": 12,
    },
    {
        "id": 1003,
        "username": "test_student_03",
        "email": "test_student_03@pygrow.local",
        "nickname": "稳步前进阿杰",
        "current_rank": "达标选手",
        "current_exp": 350,
        "total_exp": 600,
        "rank_exp_limit": 350,
        "can_promotion_test": 1,
        "courses_completed": 3,
        "practice_total": 80,
        "practice_correct_rate": 0.72,
        "wrong_count": 22,
        "projects_done": 2,
        "project_scores": [78, 82],
        "posts_count": 3,
        "post_likes_received": 80,
        "cookies": 12,
    },
    {
        "id": 1004,
        "username": "test_student_04",
        "email": "test_student_04@pygrow.local",
        "nickname": "薄弱突破小艺",
        "current_rank": "稳扎玩家",
        "current_exp": 550,
        "total_exp": 900,
        "rank_exp_limit": 550,
        "can_promotion_test": 1,
        "courses_completed": 2,
        "practice_total": 100,
        "practice_correct_rate": 0.48,
        "wrong_count": 52,
        "projects_done": 2,
        "project_scores": [60, 68],
        "posts_count": 1,
        "post_likes_received": 15,
        "cookies": 12,
    },
    {
        "id": 1005,
        "username": "test_student_05",
        "email": "test_student_05@pygrow.local",
        "nickname": "晋级挑战阿锋",
        "current_rank": "进阶干将",
        "current_exp": 780,
        "total_exp": 1550,
        "rank_exp_limit": 800,
        "can_promotion_test": 1,
        "courses_completed": 5,
        "practice_total": 180,
        "practice_correct_rate": 0.82,
        "wrong_count": 32,
        "projects_done": 3,
        "project_scores": [85, 90, 78],
        "posts_count": 6,
        "post_likes_received": 250,
        "cookies": 12,
    },
]

PASSWORD = "PyGrow123456"

# Knowledge tags for practice records
ALL_TAGS = [
    "Python基础", "数据类型", "运算符与表达式", "函数",
    "列表", "字典", "循环", "条件判断",
    "面向对象", "文件操作", "异常处理", "模块与包",
    "正则表达式", "编码规范", "字符串", "集合与元组",
]
WEAK_TAGS_04 = ["循环", "列表", "函数"]  # Account 4 weakness focus

# Post templates
POST_TEMPLATES = [
    ("问答专区", "Python基础", "请教一下，列表推导式和普通for循环在性能上有什么区别？什么时候应该用推导式？",
     "最近在写一个小项目，发现用列表推导式可以让代码简洁很多。但是我听说在处理大数据量的时候，生成器表达式会更好。有没有大佬能详细解释一下这两种方式的性能差异和适用场景？"),
    ("技术分享区", "经验分享", "分享一个我最近学到的Python调试技巧——使用pdb进行交互式调试",
     "之前一直用print调试，效率太低了。最近学会了pdb模块，真的太好用了！可以在命令行里逐行执行代码、查看变量值、设置断点。强烈推荐给还在用print调试的朋友们！"),
    ("资源分享", "学习资源", "推荐几个免费的Python学习网站和练习平台",
     "整理了一些我自己用过的免费Python学习资源：1) Python官方文档 2) LeetCode刷题 3) 菜鸟教程 4) B站上有很多优质的教学视频。大家还有什么好的资源推荐吗？"),
    ("我要吐槽", "其他", "学Python半年了，感觉面向对象编程真的好难理解...",
     "类、对象、继承、多态、封装...这些概念看得我头大。书上说面向对象是为了更好地组织代码，但我写的小脚本用函数就够用了，完全感受不到OOP的好处。有没有过来人分享一下经验？"),
    ("问答专区", "代码求助", "用requests爬取网页时总是返回403，加了headers也没用，怎么办？",
     "尝试爬取一个网站的数据，已经加了User-Agent头，但还是返回403 Forbidden。怀疑是网站做了反爬处理。各位大佬一般怎么解决这种问题？需要加上cookies吗？"),
    ("技术分享区", "项目展示", "我用Python写了一个自动化批量重命名工具，分享给大家",
     "功能特点：1. 支持正则表达式匹配 2. 可以预览重命名结果 3. 支持撤销操作 4. GUI界面基于tkinter。代码已经放到GitHub上了，欢迎大家提建议和PR！"),
]

# Rank EXP caps
RANK_EXP_CAPS = {
    "萌新小白": 100,
    "勤学学徒": 200,
    "达标选手": 350,
    "稳扎玩家": 550,
    "进阶干将": 800,
}


async def seed_test_accounts():
    async with async_session() as db:
        pw_hash = hash_password(PASSWORD)

        # ---- Fetch existing data for references ----
        courses_result = await db.execute(select(Course).order_by(Course.id))
        courses = courses_result.scalars().all()
        if not courses:
            print("ERROR: No courses found. Run seed.py first.")
            return

        questions_result = await db.execute(select(Question).order_by(Question.id))
        questions = questions_result.scalars().all()
        if not questions:
            print("ERROR: No questions found. Run seed.py first.")
            return

        projects_result = await db.execute(select(Project).order_by(Project.id))
        projects = projects_result.scalars().all()

        # ---- Tag → question mapping ----
        tag_questions = {}
        for q in questions:
            tag = q.knowledge_tag or ""
            if tag not in tag_questions:
                tag_questions[tag] = []
            tag_questions[tag].append(q)

        skipped_tables = []
        created_users = []

        for acct in TEST_ACCOUNTS:
            uid = acct["id"]
            uname = acct["username"]

            # ---- 1. User ----
            existing = (await db.execute(select(User).where(User.id == uid))).scalar_one_or_none()
            if existing:
                # Update existing test user
                existing.username = uname
                existing.email = acct["email"]
                existing.nickname = acct["nickname"]
                existing.password_hash = pw_hash
                existing.current_rank = acct["current_rank"]
                existing.current_exp = acct["current_exp"]
                existing.total_exp = acct["total_exp"]
                existing.rank_exp_limit = RANK_EXP_CAPS[acct["current_rank"]]
                existing.can_promotion_test = acct["can_promotion_test"]
                existing.cookies = acct["cookies"]
                existing.experience = acct["total_exp"]
                existing.points = acct["total_exp"] // 2
                existing.is_assessed = 1
                user = existing
                print(f"Updated user: {uname} (id={uid})")
            else:
                user = User(
                    id=uid,
                    username=uname,
                    password_hash=pw_hash,
                    email=acct["email"],
                    nickname=acct["nickname"],
                    current_rank=acct["current_rank"],
                    current_exp=acct["current_exp"],
                    total_exp=acct["total_exp"],
                    rank_exp_limit=RANK_EXP_CAPS[acct["current_rank"]],
                    can_promotion_test=acct["can_promotion_test"],
                    cookies=acct["cookies"],
                    experience=acct["total_exp"],
                    points=acct["total_exp"] // 2,
                    is_assessed=1,
                )
                db.add(user)
                await db.flush()
                print(f"Created user: {uname} (id={uid})")
            created_users.append(acct)

            # ---- 2. Course Progress ----
            # Remove old progress for this user
            await db.execute(text("DELETE FROM course_progress WHERE user_id = :uid"), {"uid": uid})
            completed = acct["courses_completed"]
            for i, course in enumerate(courses):
                if i < completed:
                    db.add(CourseProgress(
                        user_id=uid, course_id=course.id,
                        last_lesson_id=course.id * 100 + 20,
                        progress_percent=100.0, is_completed=True,
                    ))
                elif i < completed + 1:
                    db.add(CourseProgress(
                        user_id=uid, course_id=course.id,
                        last_lesson_id=course.id * 100 + 5,
                        progress_percent=random.uniform(30, 70), is_completed=False,
                    ))

            # ---- 3. Practice Records ----
            await db.execute(text("DELETE FROM practice_records WHERE user_id = :uid"), {"uid": uid})
            total = acct["practice_total"]
            correct_rate = acct["practice_correct_rate"]
            wrong_count_target = acct["wrong_count"]

            practice_tags = list(ALL_TAGS)
            if uid == 1004:
                # Account 4: bias toward weak tags (循环, 列表, 函数)
                practice_tags = WEAK_TAGS_04 * 4 + [t for t in ALL_TAGS if t not in WEAK_TAGS_04]

            correct_done = 0
            wrong_done = 0
            hints_used_total = 0

            for i in range(total):
                tag = random.choice(practice_tags)
                pool = tag_questions.get(tag, tag_questions.get("Python基础", []))
                if not pool:
                    continue
                q = random.choice(pool)

                is_correct = random.random() < correct_rate

                # Account 4: wrong answers on weak tags
                if uid == 1004 and tag in WEAK_TAGS_04:
                    is_correct = random.random() < 0.30  # Only 30% correct on weak tags

                if is_correct and correct_done >= total - wrong_count_target:
                    is_correct = False

                hints = 0
                if uid == 1004:
                    # Account 4: high AI hint usage
                    hints = random.choices([0, 1, 2, 3], weights=[20, 25, 30, 25])[0]
                    hints_used_total += hints
                elif random.random() < 0.15:
                    hints = random.randint(1, 2)

                if is_correct:
                    correct_done += 1
                else:
                    wrong_done += 1

                days_ago = random.randint(0, 30)
                created = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23))

                db.add(PracticeRecord(
                    user_id=uid,
                    question_id=q.id,
                    user_answer="" if is_correct else "B" if q.type == "single_choice" else "",
                    is_correct=is_correct,
                    hints_used=hints,
                    created_at=created,
                ))

            # ---- 4. Favorites (wrong question bookmarks) ----
            await db.execute(text("DELETE FROM favorites WHERE user_id = :uid"), {"uid": uid})
            fav_count = min(acct["wrong_count"], 8)
            wrong_questions = await db.execute(
                select(PracticeRecord.question_id).where(
                    PracticeRecord.user_id == uid, PracticeRecord.is_correct == False
                ).limit(fav_count)
            )
            wrong_qids = [r[0] for r in wrong_questions.all()]
            for qid in wrong_qids:
                db.add(Favorite(user_id=uid, item_type="question", item_id=str(qid), title="错题收藏"))

            # ---- 5. Project Submissions ----
            await db.execute(text("DELETE FROM project_submissions WHERE user_id = :uid"), {"uid": uid})
            if projects:
                for pi, score in enumerate(acct["project_scores"]):
                    project = projects[pi % len(projects)]
                    db.add(ProjectSubmission(
                        user_id=uid,
                        project_id=project.id,
                        code=f"# 测试项目代码\n# 账号 {uname}\nprint('Hello PyGrow!')",
                        status="reviewed",
                        total_score=score,
                        level="优秀" if score >= 90 else "良好" if score >= 75 else "达标" if score >= 60 else "需修改",
                        strengths=["代码结构清晰"],
                        problems=["部分边界条件未处理"] if score < 80 else [],
                        suggestions=["继续加油"],
                        experience_gained=score,
                        hints_used=random.randint(0, 3),
                        submitted_at=datetime.now() - timedelta(days=random.randint(1, 14)),
                    ))

            # ---- 6. Community Posts ----
            await db.execute(text("DELETE FROM posts WHERE user_id = :uid"), {"uid": uid})
            post_ids_created = []
            for pi in range(acct["posts_count"]):
                template = POST_TEMPLATES[pi % len(POST_TEMPLATES)]
                cat, tag, title, content = template
                post = Post(
                    user_id=uid,
                    title=title,
                    content=content,
                    category=cat,
                    tags=tag,
                    like_count=acct["post_likes_received"] // max(1, acct["posts_count"]),
                    comment_count=random.randint(0, 3),
                )
                db.add(post)
                await db.flush()
                post_ids_created.append(post.id)

            # ---- 7. Pet Profile ----
            try:
                existing_pet = (await db.execute(
                    select(PetProfile).where(PetProfile.user_id == uid)
                )).scalar_one_or_none()
                if existing_pet:
                    existing_pet.cookie_count = None  # cookies stored on user
                    existing_pet.pet_name = random.choice(["小Py", "代码喵", "虫虫", "派森", "灵蛇"])
                    existing_pet.pet_type = random.choice(["默认", "火凤", "水灵", "草芽"])
                    existing_pet.status = "idle"
                else:
                    db.add(PetProfile(
                        user_id=uid,
                        pet_name=random.choice(["小Py", "代码喵", "虫虫", "派森", "灵蛇"]),
                        pet_type=random.choice(["默认", "火凤", "水灵", "草芽"]),
                        status="idle",
                    ))
            except Exception as e:
                if "pet_profiles" not in str(e):
                    skipped_tables.append(f"pet_profiles ({e})")

            # ---- 8. Pet Cookie record ----
            try:
                db.add(PetCookieRecord(
                    user_id=uid,
                    source_type="initial_grant",
                    cookies=12,
                    description="测试账号初始饼干",
                ))
            except Exception as e:
                if "pet_cookie_records" not in str(e):
                    skipped_tables.append(f"pet_cookie_records ({e})")

        await db.commit()
        print("\n=== All test accounts seeded successfully ===\n")

        # ---- Verification ----
        for acct in TEST_ACCOUNTS:
            uid = acct["id"]
            user = (await db.execute(select(User).where(User.id == uid))).scalar_one_or_none()
            if user:
                pr_count = (await db.execute(
                    select(func.count()).select_from(PracticeRecord).where(PracticeRecord.user_id == uid)
                )).scalar()
                post_count = (await db.execute(
                    select(func.count()).select_from(Post).where(Post.user_id == uid)
                )).scalar()
                proj_count = (await db.execute(
                    select(func.count()).select_from(ProjectSubmission).where(ProjectSubmission.user_id == uid)
                )).scalar()
                fav_count = (await db.execute(
                    select(func.count()).select_from(Favorite).where(Favorite.user_id == uid)
                )).scalar()
                print(
                    f"  {user.username} | {user.email} | 段位:{user.current_rank} | "
                    f"饼干:{user.cookies} | 练习:{pr_count}条 | 帖子:{post_count}条 | "
                    f"项目:{proj_count}个 | 收藏:{fav_count}条"
                )
            else:
                print(f"  WARNING: User id={uid} not found!")

        if skipped_tables:
            print(f"\n跳过的表（字段不存在或表不存在）: {skipped_tables}")

        print(f"\n统一密码: {PASSWORD}")
        print("启动后端: cd backend && uvicorn app.main:app --reload")


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(init_db())
    asyncio.run(seed_test_accounts())
