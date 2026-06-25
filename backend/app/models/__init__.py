from app.models.user import User
from app.models.course import Course, Lesson, CourseProgress, CourseCollection
from app.models.gamification import Question, PracticeRecord, Badge, UserBadge, DailyTask, UserDailyTask
from app.models.note import Note
from app.models.project import Project, ProjectSubmission
from app.models.community import Post, Comment, PostLike, PostFavorite, CommentLike
from app.models.code_submission import CodeSubmission
from app.models.ai_chat_record import AIChatRecord
from app.models.review import CourseReview
from app.models.favorite import Favorite
from app.models.ai_note import AINoteTask, AINote
from app.models.pet import PetProfile, PetAdventure, PetCookieRecord, PetReward
from app.models.promotion import PromotionExam

__all__ = [
    "User",
    "Course", "Lesson", "CourseProgress", "CourseCollection",
    "Question", "PracticeRecord", "Badge", "UserBadge", "DailyTask", "UserDailyTask",
    "Note",
    "Project", "ProjectSubmission",
    "Post", "Comment", "PostLike", "PostFavorite", "CommentLike",
    "CodeSubmission",
    "AIChatRecord",
    "CourseReview",
    "Favorite",
    "AINoteTask", "AINote",
    "PetProfile", "PetAdventure", "PetCookieRecord", "PetReward",
    "PromotionExam",
]
