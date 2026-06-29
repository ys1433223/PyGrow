"""
Promotion exam service — question selection, AI generation, grading, and feedback.

Priority chain (spec §三):
  1. Core questions in current rank range from learned chapters
  2. Recently wrong questions' knowledge_tags
  3. Weak tags (accuracy < 60%)
  4. High AI-hint-usage tags
  5. Wrong but not yet re-corrected questions
  6. AI-generated questions (fallback only)
"""
import json
import logging
import random
from collections import defaultdict
from datetime import date, timedelta

import httpx
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.config import settings
from app.models.gamification import Question, PracticeRecord
from app.models.user import User
from app.models.course import CourseProgress, Lesson
from app.models.promotion import PromotionExam
from app.services.gamification import RANK_TIERS, MAJOR_LEVELS, get_rank_index, get_next_rank

logger = logging.getLogger(__name__)

EXAM_QUESTION_COUNT = 10
RECENT_DAYS = 30

# Composition targets (spec §六)
COMPOSITION = {"core": 0.60, "weak_wrong": 0.25, "comprehensive": 0.15}
DIFFICULTY_MIX = {"easy": 0.40, "medium": 0.50, "hard": 0.10}


# ---------------------------------------------------------------------------
# Stage → rank mapping helpers
# ---------------------------------------------------------------------------

def _get_stage_for_rank(rank_name: str) -> str:
    """Return 初级/中级/高级 for a rank name."""
    for stage, ranks in MAJOR_LEVELS.items():
        if rank_name in ranks:
            return stage
    return "初级"


def _get_ranks_in_stage(stage: str) -> list:
    """Return all rank names in a stage."""
    return MAJOR_LEVELS.get(stage, ["萌新小白", "勤学学徒", "达标选手"])


def _get_allowed_stages(current_rank: str) -> list:
    """Return stages the student can draw questions from.
    Students can draw from their current stage only (no cross-stage)."""
    return [_get_stage_for_rank(current_rank)]


# ---------------------------------------------------------------------------
# Learned scope analysis (spec §二)
# ---------------------------------------------------------------------------

async def get_learned_scope(db: AsyncSession, user_id: int) -> dict:
    """Determine what a student has learned from multiple signals.

    Returns:
        learned_tags: set of knowledge_tags the student has encountered
        learned_chapters: set of chapter_nums with any progress
        current_stage: 初级/中级/高级 based on current_rank
        allowed_stages: stages allowed for question selection
        completed_question_ids: set of question IDs already answered
        weak_tags: {tag: accuracy} for tags below 60%
        wrong_tags: {tag: count} for recently wrong tags
        high_hint_tags: {tag: hint_count} for tags with high AI hint usage
    """
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        return {}
    current_rank = user.current_rank or "萌新小白"
    current_stage = _get_stage_for_rank(current_rank)

    # 1. Learned knowledge_tags from PracticeRecord
    result = await db.execute(
        select(PracticeRecord, Question.knowledge_tag, Question.chapter_num)
        .join(Question, PracticeRecord.question_id == Question.id)
        .where(PracticeRecord.user_id == user_id)
        .order_by(PracticeRecord.created_at.desc())
    )
    rows = result.all()

    learned_tags = set()
    completed_question_ids = set()
    tag_stats = defaultdict(lambda: {"correct": 0, "total": 0, "hints": 0, "wrong_recent": 0})
    cutoff = date.today() - timedelta(days=RECENT_DAYS)

    for rec, tag, ch_num in rows:
        tag = tag or ""
        learned_tags.add(tag)
        completed_question_ids.add(rec.question_id)
        s = tag_stats[tag]
        s["total"] += 1
        s["hints"] += rec.hints_used or 0
        if rec.is_correct:
            s["correct"] += 1
        else:
            if rec.created_at and rec.created_at.date() >= cutoff:
                s["wrong_recent"] += 1

    weak_tags = {}
    wrong_tags = {}
    high_hint_tags = {}
    for tag, s in tag_stats.items():
        if s["total"] > 0:
            acc = s["correct"] / s["total"]
            if acc < 0.6:
                weak_tags[tag] = acc
        if s["wrong_recent"] > 0:
            wrong_tags[tag] = s["wrong_recent"]
        if s["hints"] >= 3:
            high_hint_tags[tag] = s["hints"]

    # 2. Learned chapters from CourseProgress
    result = await db.execute(
        select(CourseProgress).where(
            CourseProgress.user_id == user_id,
            CourseProgress.progress_percent > 0,
        )
    )
    progresses = result.scalars().all()
    learned_chapters = set()
    for cp in progresses:
        # Get lessons for this course
        lessons_result = await db.execute(
            select(Lesson.chapter).where(Lesson.course_id == cp.course_id)
        )
        chapters = lessons_result.scalars().all()
        for ch in chapters:
            # Extract chapter number from "第X章：xxx" or "Chapter X"
            learned_chapters.add(ch)

    # 3. Active course chapter nums
    chapter_nums_result = await db.execute(
        select(Question.chapter_num)
        .where(Question.knowledge_tag.in_(learned_tags) if learned_tags else True)
        .where(Question.chapter_num.isnot(None))
    )
    learned_chapter_nums = set()
    for (cn,) in chapter_nums_result.all():
        if cn:
            learned_chapter_nums.add(cn)

    return {
        "learned_tags": learned_tags,
        "learned_chapter_nums": learned_chapter_nums,
        "current_stage": current_stage,
        "current_rank": current_rank,
        "allowed_stages": _get_allowed_stages(current_rank),
        "completed_question_ids": completed_question_ids,
        "weak_tags": weak_tags,
        "wrong_tags": wrong_tags,
        "high_hint_tags": high_hint_tags,
        "total_records": len(rows),
    }


# ---------------------------------------------------------------------------
# Question selection (spec §三, §四)
# ---------------------------------------------------------------------------

def _pick_diverse(items: list, count: int) -> list:
    """Pick items with tag diversity — avoid picking all from same tag."""
    if len(items) <= count:
        return list(items)
    # Shuffle then take count, preferring tag diversity
    by_tag = defaultdict(list)
    for item in items:
        tag = item.get("knowledge_tag", "")
        by_tag[tag].append(item)
    selected = []
    tags = list(by_tag.keys())
    random.shuffle(tags)
    while len(selected) < count and tags:
        for tag in list(tags):
            if by_tag[tag]:
                selected.append(by_tag[tag].pop())
                if len(selected) >= count:
                    break
            else:
                tags.remove(tag)
    return selected[:count]


async def select_promotion_questions(
    db: AsyncSession, user_id: int, count: int = EXAM_QUESTION_COUNT
) -> dict:
    """Select promotion exam questions following the priority chain."""
    scope = await get_learned_scope(db, user_id)
    if not scope:
        return {"questions": [], "source_breakdown": {}, "total": 0}

    learned_tags = scope["learned_tags"]
    current_stage = scope["current_stage"]
    allowed_stages = scope["allowed_stages"]
    completed_ids = scope["completed_question_ids"]
    weak_tags = scope["weak_tags"]
    wrong_tags = scope["wrong_tags"]
    high_hint_tags = scope["high_hint_tags"]
    current_rank = scope["current_rank"]

    # For very new students (lowest rank, few records), skip hard questions
    rank_index = get_rank_index(current_rank)
    skip_hard = rank_index <= 1  # 萌新小白 or 勤学学徒 → no hard

    # ---- Exclude questions from previous promotion exams ----
    past_exam_result = await db.execute(
        select(PromotionExam).where(
            PromotionExam.user_id == user_id,
            PromotionExam.status == "completed",
        )
    )
    past_exams = past_exam_result.scalars().all()
    past_exam_question_ids = set()
    for exam in past_exams:
        if exam.questions:
            for q in exam.questions:
                qid = q.get("id") or q.get("question_id")
                if qid:
                    past_exam_question_ids.add(qid)

    # Merge with completed practice question IDs
    all_excluded_ids = completed_ids | past_exam_question_ids

    selected = []
    used_ids = set()
    source_breakdown = defaultdict(int)
    reasons = {}  # question_id → reason

    # ---- Fetch candidate pool ----
    # All questions in allowed stages
    result = await db.execute(
        select(Question).where(Question.stage.in_(allowed_stages))
    )
    all_candidates = result.scalars().all()

    # Filter to learned scope only
    candidates = [
        q for q in all_candidates
        if (q.knowledge_tag or "") in learned_tags
    ]
    # Exclude questions already used in past promotion exams
    candidates = [q for q in candidates if q.id not in past_exam_question_ids]
    if not candidates:
        # Fallback: use all questions in stage (new student with no records)
        candidates = [q for q in all_candidates if q.stage in allowed_stages and q.id not in past_exam_question_ids]

    # Exclude hard for new students
    if skip_hard:
        candidates = [q for q in candidates if q.difficulty != "hard"]

    # ---- Priority-based candidate pools ----
    core_pool = []       # Priority 1: learned scope core questions
    wrong_pool = []      # Priority 2: recently wrong tag questions
    weak_pool = []       # Priority 3: weak tag questions
    hint_pool = []       # Priority 4: high hint tag questions
    redo_pool = []       # Priority 5: wrong but not re-corrected
    unused_pool = []     # Unused questions (not done yet)

    for q in candidates:
        tag = q.knowledge_tag or ""
        q_dict = {
            "id": q.id, "question_id": q.question_id,
            "title": q.title, "content": q.content, "type": q.type,
            "options": q.options, "answer": q.answer, "analysis": q.analysis,
            "knowledge_point": q.knowledge_point, "knowledge_tag": tag,
            "knowledge_type": q.knowledge_type, "difficulty": q.difficulty,
            "stage": q.stage, "chapter_num": q.chapter_num,
            "test_cases": q.test_cases, "starter_code": q.starter_code,
            "score": q.score or 5, "source": q.source or "question_bank",
        }

        is_new = q.id not in completed_ids

        if tag in wrong_tags and wrong_tags[tag] > 0:
            wrong_pool.append({**q_dict, "_pick_reason": "命中最近错题知识点"})
        if tag in weak_tags:
            weak_pool.append({**q_dict, "_pick_reason": f"该知识点正确率仅{weak_tags[tag]:.0%}"})
        if tag in high_hint_tags:
            hint_pool.append({**q_dict, "_pick_reason": "AI提示使用较多，需加强"})

        if is_new:
            unused_pool.append({**q_dict, "_pick_reason": "新题，未做过"})
        else:
            core_pool.append({**q_dict, "_pick_reason": "已学章节核心题"})

    # Deduplicate by question id
    def dedup(items):
        seen = set()
        out = []
        for item in items:
            if item["id"] not in seen:
                seen.add(item["id"])
                out.append(item)
        return out

    wrong_pool = dedup(wrong_pool)
    weak_pool = dedup(weak_pool)
    hint_pool = dedup(hint_pool)
    core_pool = dedup(core_pool)
    unused_pool = dedup(unused_pool)

    # ---- Select by priority ----
    counts = {
        "core": max(1, int(count * COMPOSITION["core"])),         # 6
        "weak_wrong": max(1, int(count * COMPOSITION["weak_wrong"])),  # 3
        "comprehensive": max(0, int(count * COMPOSITION["comprehensive"])),  # 1-2
    }

    # Priority 1: Core (unused first, then core pool)
    core_selected = _pick_diverse(unused_pool, counts["core"])
    if len(core_selected) < counts["core"]:
        remaining = [c for c in core_pool if c["id"] not in {x["id"] for x in core_selected}]
        core_selected += _pick_diverse(remaining, counts["core"] - len(core_selected))
    for q in core_selected:
        reasons[q["question_id"]] = q.pop("_pick_reason", "核心题")
        source_breakdown[q["source"]] += 1
    selected.extend(core_selected)

    # Priority 2-5: Wrong/weak/hint
    wrong_weak = _pick_diverse(wrong_pool + weak_pool + hint_pool, counts["weak_wrong"])
    for q in wrong_weak:
        if q["id"] not in {x["id"] for x in selected}:
            reasons[q["question_id"]] = q.pop("_pick_reason", "薄弱巩固题")
            source_breakdown[q["source"]] += 1
            selected.append(q)

    # Priority 6: Comprehensive (slightly harder, same stage)
    comprehensive_candidates = [q for q in candidates
        if q.difficulty in ("medium", "hard") and q.id not in {x["id"] for x in selected}]
    comp_dicts = [
        {"id": q.id, "question_id": q.question_id, "title": q.title, "content": q.content,
         "type": q.type, "options": q.options, "answer": q.answer, "analysis": q.analysis,
         "knowledge_point": q.knowledge_point, "knowledge_tag": q.knowledge_tag or "",
         "knowledge_type": q.knowledge_type, "difficulty": q.difficulty,
         "stage": q.stage, "chapter_num": q.chapter_num,
         "test_cases": q.test_cases, "starter_code": q.starter_code,
         "score": q.score or 5, "source": q.source or "question_bank",
         "_pick_reason": "综合应用题"}
        for q in comprehensive_candidates
    ]
    comp_selected = _pick_diverse(comp_dicts, counts["comprehensive"])
    for q in comp_selected:
        if q["id"] not in {x["id"] for x in selected}:
            reasons[q["question_id"]] = q.pop("_pick_reason", "综合应用题")
            source_breakdown[q["source"]] += 1
            selected.append(q)

    # ---- Fill remaining with unused pool ----
    remaining_needed = count - len(selected)
    if remaining_needed > 0:
        fill_pool = [u for u in unused_pool if u["id"] not in {x["id"] for x in selected}]
        fill = _pick_diverse(fill_pool, remaining_needed)
        for q in fill:
            reasons[q["question_id"]] = q.pop("_pick_reason", "补充题")
            source_breakdown[q["source"]] += 1
        selected.extend(fill)

    # ---- Still not enough → AI generation (Priority 6, spec §五) ----
    still_needed = count - len(selected)
    ai_generated = []
    if still_needed > 0:
        # Determine which weak tags to generate for
        gen_tags = list(weak_tags.keys())[:still_needed] if weak_tags else list(learned_tags)[:still_needed]
        if not gen_tags:
            gen_tags = list(learned_tags)[:still_needed] if learned_tags else ["Python基础"]
        for tag in gen_tags[:still_needed]:
            try:
                ai_q = await generate_ai_promotion_question(db, tag, "medium", list(learned_tags))
                if ai_q:
                    ai_generated.append(ai_q)
                    reasons[ai_q["question_id"]] = "AI生成补充题（题库不足）"
                    source_breakdown["ai_generated_promotion"] += 1
            except Exception:
                pass

        selected.extend(ai_generated)

    # ---- Final fill with random stage-appropriate questions (absolute last resort) ----
    if len(selected) < count:
        all_stage = [q for q in candidates if q.id not in {x["id"] for x in selected}]
        random.shuffle(all_stage)
        for q in all_stage[:count - len(selected)]:
            q_dict = {
                "id": q.id, "question_id": q.question_id, "title": q.title,
                "content": q.content, "type": q.type, "options": q.options,
                "answer": q.answer, "analysis": q.analysis,
                "knowledge_point": q.knowledge_point,
                "knowledge_tag": q.knowledge_tag or "",
                "knowledge_type": q.knowledge_type, "difficulty": q.difficulty,
                "stage": q.stage, "chapter_num": q.chapter_num,
                "test_cases": q.test_cases, "starter_code": q.starter_code,
                "score": q.score or 5, "source": q.source or "question_bank",
            }
            reasons[q_dict["question_id"]] = "随机补充题"
            source_breakdown[q_dict["source"]] += 1
            selected.append(q_dict)

    # ---- Build final question list with metadata ----
    questions = []
    for i, q in enumerate(selected[:count]):
        questions.append({
            "index": i + 1,
            "question_id": q["question_id"],
            "title": q["title"],
            "content": q["content"],
            "type": q["type"],
            "options": q["options"],
            "answer": q.get("answer", ""),
            "analysis": q.get("analysis", ""),
            "knowledge_point": q.get("knowledge_point", ""),
            "knowledge_tag": q.get("knowledge_tag", ""),
            "difficulty": q.get("difficulty", "medium"),
            "stage": q.get("stage", current_stage),
            "score": q.get("score", 5),
            "source": q.get("source", "question_bank"),
            "reason": reasons.get(q["question_id"], ""),
            "test_cases": q.get("test_cases"),
            "starter_code": q.get("starter_code"),
        })

    return {
        "questions": questions,
        "total": len(questions),
        "source_breakdown": dict(source_breakdown),
        "learned_scope": {
            "learned_tags": list(learned_tags),
            "current_stage": current_stage,
            "current_rank": current_rank,
            "total_records": scope["total_records"],
        },
    }


# ---------------------------------------------------------------------------
# AI question generation (spec §五)
# ---------------------------------------------------------------------------

AI_PROMOTION_PROMPT = """你是一个Python教学专家。请基于以下知识点生成一道晋级赛题目。

知识点：{knowledge_tag}
难度：{difficulty}
已学知识点范围：{learned_tags}
当前段位阶段：{stage}

重要约束：
1. 只能基于已学知识点范围出题，不允许超纲
2. 难度必须匹配当前段位
3. 题目类型从: single_choice, multiple_choice, fill_blank, judge, short_answer, code 中选择

返回严格JSON格式（不要在JSON外加任何文字）：
{{
  "title": "题目标题（简洁描述）",
  "content": "题目内容（完整的题目描述）",
  "type": "题目类型",
  "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"],
  "answer": "正确答案",
  "analysis": "详细解析",
  "knowledge_point": "对应的知识点名称",
  "difficulty": "难度",
  "starter_code": "代码题的起始代码（非代码题填null）",
  "test_cases": [{{"input": "输入", "expected": "期望输出"}}]
}}"""


async def generate_ai_promotion_question(
    db: AsyncSession,
    knowledge_tag: str,
    difficulty: str,
    learned_tags: list,
) -> dict | None:
    """Generate a promotion exam question via DeepSeek API and save to DB."""
    api_key = settings.ai_api_key or settings.deepseek_api_key
    if not api_key:
        logger.warning("No AI API key configured, skipping promotion AI generation")
        return None

    prompt = AI_PROMOTION_PROMPT.format(
        knowledge_tag=knowledge_tag,
        difficulty=difficulty,
        learned_tags=", ".join(learned_tags),
        stage="初级/中级",  # conservative
    )

    try:
        url = f"{settings.ai_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.ai_model_name,
            "messages": [
                {"role": "system", "content": "你是一个Python编程教学专家，专门生成高质量的编程练习题。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 1500,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()

        # Strip markdown fences
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:]) if len(lines) > 1 else content
        if content.endswith("```"):
            content = content[:-3].strip()

        q_data = json.loads(content)
    except Exception as e:
        logger.warning(f"AI promotion question generation failed: {e}")
        return None

    # Save to DB
    try:
        new_q = Question(
            question_id=None,  # Will be auto-ID
            title=q_data.get("title", f"{knowledge_tag} 晋级赛题"),
            content=q_data.get("content", ""),
            type=q_data.get("type", "single_choice"),
            options=q_data.get("options"),
            answer=str(q_data.get("answer", "")),
            analysis=q_data.get("analysis", ""),
            knowledge_point=q_data.get("knowledge_point", knowledge_tag),
            knowledge_tag=knowledge_tag,
            knowledge_type="application",
            difficulty=q_data.get("difficulty", difficulty),
            level=difficulty,
            stage="初级",
            chapter_num=0,
            test_cases=q_data.get("test_cases"),
            starter_code=q_data.get("starter_code"),
            score=5,
            source="ai_generated_promotion",
        )
        db.add(new_q)
        await db.flush()
        await db.refresh(new_q)

        return {
            "id": new_q.id,
            "question_id": new_q.id,
            "title": new_q.title,
            "content": new_q.content,
            "type": new_q.type,
            "options": new_q.options,
            "answer": new_q.answer,
            "analysis": new_q.analysis,
            "knowledge_point": new_q.knowledge_point,
            "knowledge_tag": new_q.knowledge_tag,
            "difficulty": new_q.difficulty,
            "stage": new_q.stage,
            "score": new_q.score,
            "source": "ai_generated_promotion",
            "test_cases": new_q.test_cases,
            "starter_code": new_q.starter_code,
        }
    except Exception as e:
        logger.error(f"Failed to save AI-generated promotion question: {e}")
        # Return unsaved question data as fallback
        return {
            "id": -1,
            "question_id": -1,
            "title": q_data.get("title", "AI生成题"),
            "content": q_data.get("content", ""),
            "type": q_data.get("type", "single_choice"),
            "options": q_data.get("options"),
            "answer": str(q_data.get("answer", "")),
            "analysis": q_data.get("analysis", ""),
            "knowledge_point": q_data.get("knowledge_point", knowledge_tag),
            "knowledge_tag": knowledge_tag,
            "difficulty": q_data.get("difficulty", difficulty),
            "stage": "初级",
            "score": 5,
            "source": "ai_generated_promotion",
            "test_cases": q_data.get("test_cases"),
            "starter_code": q_data.get("starter_code"),
        }


# ---------------------------------------------------------------------------
# Grading (spec §七)
# ---------------------------------------------------------------------------

def grade_promotion_exam(
    questions: list, answers: dict, exam: PromotionExam
) -> dict:
    """Grade a completed promotion exam. Returns result dict."""
    total_score = 0
    max_score = 0
    core_correct = 0
    core_total = 0
    wrong_tags = defaultdict(int)
    correct_tags = defaultdict(int)
    graded = []

    for q in questions:
        q_id = str(q.get("question_id", q.get("id", "")))
        user_answer = answers.get(q_id, "")
        correct_answer = str(q.get("answer", "")).strip()
        q_score = q.get("score", 5)
        max_score += q_score
        tag = q.get("knowledge_tag", "")

        # Simple answer comparison
        is_correct = _is_answer_correct(user_answer, correct_answer, q.get("type", ""))

        if is_correct:
            total_score += q_score
            correct_tags[tag] += 1
            # Core questions (not AI generated, from question bank)
            source = q.get("source", "question_bank")
            if source in ("question_bank", "wrong_question"):
                core_correct += 1
                core_total += 1
        else:
            wrong_tags[tag] += 1
            source = q.get("source", "question_bank")
            if source in ("question_bank", "wrong_question"):
                core_total += 1

        # Normalize multi-select answer display: "ABC" → "A,B,C"
        display_answer = correct_answer
        if q.get("type") == "multiple_choice" and correct_answer and "," not in correct_answer:
            display_answer = ",".join(c for c in correct_answer.replace(" ", "").upper() if c)
        graded.append({
            "question_id": q_id,
            "user_answer": user_answer,
            "correct_answer": display_answer,
            "is_correct": is_correct,
            "score_awarded": q_score if is_correct else 0,
            "knowledge_tag": tag,
            "analysis": q.get("analysis", ""),
        })

    # Calculate score out of 100
    score_pct = round(total_score / max_score * 100) if max_score > 0 else 0
    core_rate = round(core_correct / core_total * 100) if core_total > 0 else 100
    passed = score_pct >= 80 and core_rate >= 70

    # Update exam record
    exam.answers = graded
    exam.score = score_pct
    exam.core_correct_rate = core_rate
    exam.passed = passed
    exam.status = "completed"
    exam.completed_at = func.now()

    if not passed:
        # Build weakness feedback
        weak_tags_list = sorted(wrong_tags.items(), key=lambda x: -x[1])
        exam.weakness_tags = [t for t, _ in weak_tags_list]
        exam.feedback = _build_failure_feedback(weak_tags_list, questions)

    return {
        "passed": passed,
        "score": score_pct,
        "max_score": max_score,
        "core_correct_rate": core_rate,
        "graded_questions": graded,
        "weakness_tags": exam.weakness_tags,
        "feedback": exam.feedback,
    }


def _is_answer_correct(user_answer: str, correct: str, q_type: str) -> bool:
    """Compare user answer to correct answer with normalization."""
    ua = (user_answer or "").strip().upper()
    ca = correct.strip().upper()

    if q_type == "code":
        # Code questions can't be reliably auto-graded without execution.
        # Accept any non-empty answer; reference answer shown for self-comparison.
        return bool(ua)
    if q_type == "fill_blank":
        return ua == ca
    if q_type == "multiple_choice":
        # Multi-select: compare sorted answers
        ua_set = set(ua.replace(",", "").replace(" ", ""))
        ca_set = set(ca.replace(",", "").replace(" ", ""))
        return ua_set == ca_set
    # single_choice, judge, short_answer
    return ua == ca


def _build_failure_feedback(wrong_tags: list, questions: list) -> list:
    """Build feedback for failed promotion exam (spec §七)."""
    feedback = []
    for tag, count in wrong_tags[:5]:  # Top 5 weakness tags
        related_chapters = set()
        for q in questions:
            if q.get("knowledge_tag") == tag:
                ch = q.get("chapter_num", "")
                if ch:
                    related_chapters.add(str(ch))

        feedback.append({
            "tag": tag,
            "error_count": count,
            "suggestion": f"你在「{tag}」相关题目上错误较多，建议先完成薄弱知识点练习后再次挑战。",
            "recommended_chapters": list(related_chapters)[:3],
        })
    return feedback
