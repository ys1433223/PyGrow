from pydantic import BaseModel
from typing import Optional, List, Any


class AssessmentSubmit(BaseModel):
    answers: dict  # {question_id: answer}


class PracticeSubmit(BaseModel):
    question_id: int
    answer: str
    hints_used: int = 0


class BatchAnswer(BaseModel):
    question_id: int
    answer: str
    hints_used: int = 0


class BatchSubmit(BaseModel):
    answers: List[BatchAnswer]


class ClaimReward(BaseModel):
    task_id: int


class HintRequest(BaseModel):
    question_id: int
    question: str
    question_type: str
    difficulty: str = "medium"
    knowledge_tag: str = ""
    knowledge_type: str = ""  # concept/comparison/application/code/debug
    student_code: str = ""
    hint_level: int = 1
    hint_mode: str = ""  # concept_card/example/keyword or compare_table/judge_basis/mistake or etc.
    options: list = []  # question options [{label, text}] for fixed-answer questions
    correct_answer: str = ""  # correct answer for knowledge card / wrong-answer exclusion
