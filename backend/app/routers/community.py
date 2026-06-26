import re
from collections import Counter

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from pydantic import BaseModel, field_validator

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.community import Post, Comment, PostLike, PostFavorite, CommentLike
from app.schemas.common import api_response

router = APIRouter()

PROFANITY_WORDS = [
    "fuck", "shit", "damn", "asshole", "bitch", "dick", "bastard",
    "傻逼", "操你", "日你", "他妈", "你妈", "混蛋", "白痴",
    "弱智", "脑残", "废物", "垃圾人", "狗日的", "去死",
    "草泥马", "艹你", "妈的", "特么", "尼玛", "滚蛋",
    "变态", "人渣", "贱人", "蠢货", "智障", "煞笔",
    "sb", "nmsl", "cnm", "tmd", "woc", "nmd",
]

# Honor titles based on total likes received
HONOR_TITLES = [
    (5, "冒泡新星", "text-gray-400", "border-gray-300", "bg-gray-50"),
    (40, "点赞收割机", "text-blue-600", "border-blue-300", "bg-blue-50"),
    (100, "话题制造者", "text-purple-600", "border-purple-300", "bg-purple-50"),
    (500, "镇站之宝", "text-amber-600", "border-amber-400", "bg-amber-50"),
]


def get_honor_title(total_likes: int) -> dict | None:
    """Return honor title info based on total likes received, or None."""
    title = None
    for threshold, name, text_color, border, bg in HONOR_TITLES:
        if total_likes >= threshold:
            title = {
                "name": name,
                "level": threshold,
                "text_color": text_color,
                "border": border,
                "bg": bg,
            }
    return title


async def get_user_total_likes(db: AsyncSession, user_id: int) -> int:
    """Total likes received by a user across all their posts and comments."""
    post_likes = await db.execute(
        select(func.coalesce(func.sum(Post.like_count), 0)).where(Post.user_id == user_id)
    )
    comment_likes = await db.execute(
        select(func.coalesce(func.sum(Comment.like_count), 0)).where(Comment.user_id == user_id)
    )
    return post_likes.scalar() + comment_likes.scalar()


def check_profanity(text: str) -> str | None:
    """Return the first profanity word found, or None if clean."""
    lower = text.lower()
    for w in PROFANITY_WORDS:
        if w in lower:
            return w
    return None


def validate_content_quality(text: str) -> str | None:
    """Return error message if content quality is too low, or None if OK."""
    stripped = text.strip()

    # 1. Single-character spam: same char dominates (e.g. "啊啊啊啊啊啊" or "11111111")
    if len(stripped) >= 8:
        unique = set(stripped)
        if len(unique) <= 2:
            counts = Counter(stripped)
            top_count = counts.most_common(1)[0][1]
            if top_count / len(stripped) > 0.65:
                return "内容不能是单一重复字符，请认真填写有意义的内容"

    # 2. Meaningful character count: Chinese chars, English letters, digits
    meaningful = len(re.findall(r'[一-鿿＀-￯a-zA-Z0-9]', stripped))
    if meaningful < 5:
        return "有效文字不足，请补充具体的描述或问题"

    # 3. Repeated same phrase (e.g. "好的好的好的好的")
    if len(stripped) >= 12:
        for cs in [2, 3]:
            if len(stripped) >= cs * 4:
                pattern = stripped[:cs]
                if pattern and stripped.count(pattern) * cs / len(stripped) > 0.7:
                    return "请勿重复粘贴相同内容，请认真填写"

    return None


class PostCreate(BaseModel):
    title: str
    content: str
    category: str = "问答专区"
    tags: str = ""

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError("标题不能为空")
        if len(v.strip()) < 2:
            raise ValueError("标题至少 2 个字")
        bad = check_profanity(v)
        if bad:
            raise ValueError("标题包含不文明用语，请修改后重新发布")
        return v.strip()

    @field_validator("content")
    @classmethod
    def content_validate(cls, v):
        stripped = v.strip()
        if len(stripped) < 10:
            raise ValueError("内容不少于 10 个字")
        bad = check_profanity(v)
        if bad:
            raise ValueError("内容包含不文明用语，请修改后重新发布")
        quality_err = validate_content_quality(v)
        if quality_err:
            raise ValueError(quality_err)
        return stripped


class CommentCreate(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def comment_min_length(cls, v):
        if not v.strip():
            raise ValueError("评论不能为空")
        return v.strip()


@router.get("")
async def list_posts(
    category: str = None,
    keyword: str = None,
    tag: str = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List posts with optional category filter, keyword search, and tag filter."""
    q = select(Post)
    if category:
        q = q.where(Post.category == category)
    if keyword:
        q = q.where(or_(Post.title.contains(keyword), Post.content.contains(keyword)))
    if tag:
        q = q.where(Post.tags.contains(tag))
    q = q.order_by(desc(Post.is_pinned), desc(Post.created_at))
    q = q.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(q)
    posts = result.scalars().all()

    user_ids = set(p.user_id for p in posts)
    users = {}
    honors = {}
    if user_ids:
        u_result = await db.execute(select(User).where(User.id.in_(user_ids)))
        users = {u.id: u for u in u_result.scalars().all()}
        for uid in user_ids:
            total = await get_user_total_likes(db, uid)
            honors[uid] = get_honor_title(total)

    liked = set()
    if posts:
        l_result = await db.execute(
            select(PostLike.post_id).where(PostLike.user_id == user.id, PostLike.post_id.in_([p.id for p in posts]))
        )
        liked = {r[0] for r in l_result.all()}

    items = []
    for p in posts:
        u = users.get(p.user_id)
        honor = honors.get(p.user_id)
        items.append({
            "id": p.id, "title": p.title, "content": p.content[:200],
            "category": p.category, "tags": p.tags,
            "like_count": p.like_count, "comment_count": p.comment_count,
            "is_pinned": bool(p.is_pinned),
            "created_at": str(p.created_at),
            "user_name": u.username if u else "未知",
            "user_avatar": u.avatar if u else "",
            "is_liked": p.id in liked,
            "honor_title": honor,
        })

    return api_response(data=items)


@router.get("/hot/list")
async def get_hot_posts(
    limit: int = Query(10, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
):
    """Return hot posts sorted by popularity (likes + comments). Public endpoint."""
    q = select(Post).order_by(desc(Post.like_count + Post.comment_count), desc(Post.created_at)).limit(limit)
    result = await db.execute(q)
    posts = result.scalars().all()

    user_ids = set(p.user_id for p in posts)
    users_map = {}
    if user_ids:
        u_result = await db.execute(select(User).where(User.id.in_(user_ids)))
        users_map = {u.id: u for u in u_result.scalars().all()}

    items = []
    for p in posts:
        u = users_map.get(p.user_id)
        author_name = u.username if u else '匿名用户'
        avatar = u.avatar if u else ''
        # Parse tags - stored as comma-separated string or JSON
        tags = []
        if p.tags:
            tags = [t.strip() for t in p.tags.split(',') if t.strip()]
        items.append({
            "id": p.id,
            "title": p.title,
            "content": (p.content or '')[:120],
            "category": p.category,
            "tags": tags,
            "like_count": p.like_count or 0,
            "comment_count": p.comment_count or 0,
            "author": author_name,
            "avatar": avatar,
            "is_pinned": p.is_pinned or 0,
            "created_at": str(p.created_at) if p.created_at else '',
        })
    return api_response(data=items)


@router.get("/my-posts")
async def get_my_posts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get posts created by the current user."""
    result = await db.execute(
        select(Post).where(Post.user_id == user.id).order_by(desc(Post.created_at))
    )
    posts = result.scalars().all()

    items = []
    for p in posts:
        items.append({
            "id": p.id, "title": p.title, "content": p.content[:200],
            "category": p.category, "tags": p.tags,
            "like_count": p.like_count, "comment_count": p.comment_count,
            "is_pinned": bool(p.is_pinned),
            "created_at": str(p.created_at),
            "user_name": user.username,
            "user_avatar": user.avatar or "",
        })

    return api_response(data=items)


@router.get("/{post_id}")
async def get_post_detail(
    post_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get post detail with comments."""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        return api_response(404, "帖子不存在")

    u_result = await db.execute(select(User).where(User.id == post.user_id))
    author = u_result.scalar_one_or_none()
    author_total = await get_user_total_likes(db, post.user_id)
    author_honor = get_honor_title(author_total)

    like_row = (await db.execute(
        select(PostLike).where(PostLike.user_id == user.id, PostLike.post_id == post_id)
    )).scalar_one_or_none()

    fav_row = (await db.execute(
        select(PostFavorite).where(PostFavorite.user_id == user.id, PostFavorite.post_id == post_id)
    )).scalar_one_or_none()

    c_result = await db.execute(
        select(Comment).where(Comment.post_id == post_id).order_by(Comment.created_at)
    )
    comments = c_result.scalars().all()
    c_user_ids = set(c.user_id for c in comments)
    c_users = {}
    c_honors = {}
    if c_user_ids:
        cu_result = await db.execute(select(User).where(User.id.in_(c_user_ids)))
        c_users = {u.id: u for u in cu_result.scalars().all()}
        for cid in c_user_ids:
            total = await get_user_total_likes(db, cid)
            c_honors[cid] = get_honor_title(total)

    # Get user's comment likes
    comment_liked = set()
    if comments:
        cl_result = await db.execute(
            select(CommentLike.comment_id).where(
                CommentLike.user_id == user.id,
                CommentLike.comment_id.in_([c.id for c in comments])
            )
        )
        comment_liked = {r[0] for r in cl_result.all()}

    return api_response(data={
        "id": post.id, "title": post.title, "content": post.content,
        "category": post.category, "tags": post.tags,
        "like_count": post.like_count, "comment_count": post.comment_count,
        "is_pinned": bool(post.is_pinned),
        "created_at": str(post.created_at),
        "author_name": author.username if author else "未知",
        "author_avatar": author.avatar if author else "",
        "is_liked": bool(like_row),
        "is_favorited": bool(fav_row),
        "author_honor_title": author_honor,
        "comments": [
            {
                "id": c.id, "content": c.content, "created_at": str(c.created_at),
                "user_name": c_users.get(c.user_id).username if c.user_id in c_users else "未知",
                "user_avatar": c_users.get(c.user_id).avatar if c.user_id in c_users else "",
                "like_count": c.like_count or 0,
                "is_liked": c.id in comment_liked,
                "honor_title": c_honors.get(c.user_id),
            }
            for c in comments
        ],
    })


@router.post("")
async def create_post(
    req: PostCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new post."""
    post = Post(
        user_id=user.id, title=req.title, content=req.content,
        category=req.category, tags=req.tags,
    )
    db.add(post)
    await db.commit()
    return api_response(data={"id": post.id, "message": "发布成功"})


@router.post("/{post_id}/comments")
async def add_comment(
    post_id: int,
    req: CommentCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a comment to a post."""
    p = (await db.execute(select(Post).where(Post.id == post_id))).scalar_one_or_none()
    if not p:
        return api_response(404, "帖子不存在")

    content = req.content.strip()
    bad = check_profanity(content)
    if bad:
        return api_response(400, "评论包含不文明用语，请修改后重新发布")
    quality_err = validate_content_quality(content)
    if quality_err:
        return api_response(400, quality_err)
    comment = Comment(post_id=post_id, user_id=user.id, content=content)
    db.add(comment)

    p.comment_count = (p.comment_count or 0) + 1
    await db.commit()
    return api_response(data={"id": comment.id, "message": "评论成功"})


@router.post("/{post_id}/like")
async def toggle_like(
    post_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle like on a post."""
    p = (await db.execute(select(Post).where(Post.id == post_id))).scalar_one_or_none()
    if not p:
        return api_response(404, "帖子不存在")

    existing = (await db.execute(
        select(PostLike).where(PostLike.user_id == user.id, PostLike.post_id == post_id)
    )).scalar_one_or_none()

    if existing:
        await db.delete(existing)
        p.like_count = max(0, (p.like_count or 0) - 1)
        await db.commit()
        return api_response(data={"liked": False, "like_count": p.like_count})

    db.add(PostLike(user_id=user.id, post_id=post_id))
    p.like_count = (p.like_count or 0) + 1
    await db.commit()
    return api_response(data={"liked": True, "like_count": p.like_count})


@router.post("/{post_id}/favorite")
async def toggle_favorite(
    post_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle favorite on a post."""
    p = (await db.execute(select(Post).where(Post.id == post_id))).scalar_one_or_none()
    if not p:
        return api_response(404, "帖子不存在")

    existing = (await db.execute(
        select(PostFavorite).where(PostFavorite.user_id == user.id, PostFavorite.post_id == post_id)
    )).scalar_one_or_none()

    if existing:
        await db.delete(existing)
        await db.commit()
        return api_response(data={"favorited": False})

    db.add(PostFavorite(user_id=user.id, post_id=post_id))
    await db.commit()
    return api_response(data={"favorited": True})


@router.post("/comments/{comment_id}/like")
async def toggle_comment_like(
    comment_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle like on a comment."""
    c = (await db.execute(select(Comment).where(Comment.id == comment_id))).scalar_one_or_none()
    if not c:
        return api_response(404, "评论不存在")

    existing = (await db.execute(
        select(CommentLike).where(CommentLike.user_id == user.id, CommentLike.comment_id == comment_id)
    )).scalar_one_or_none()

    if existing:
        await db.delete(existing)
        c.like_count = max(0, (c.like_count or 0) - 1)
        await db.commit()
        return api_response(data={"liked": False, "like_count": c.like_count})

    db.add(CommentLike(user_id=user.id, comment_id=comment_id))
    c.like_count = (c.like_count or 0) + 1
    await db.commit()
    return api_response(data={"liked": True, "like_count": c.like_count})


@router.delete("/{post_id}")
async def delete_post(
    post_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a post. Only the author can delete."""
    p = (await db.execute(select(Post).where(Post.id == post_id))).scalar_one_or_none()
    if not p:
        return api_response(404, "帖子不存在")
    if p.user_id != user.id:
        return api_response(403, "只能删除自己的帖子")

    # Delete related records
    await db.execute(select(Comment).where(Comment.post_id == post_id))
    comments = (await db.execute(select(Comment).where(Comment.post_id == post_id))).scalars().all()
    for c in comments:
        await db.execute(
            select(CommentLike).where(CommentLike.comment_id == c.id)
        )  # trigger load
    for c in comments:
        await db.delete(c)
    await db.execute(select(PostLike).where(PostLike.post_id == post_id))
    post_likes = (await db.execute(select(PostLike).where(PostLike.post_id == post_id))).scalars().all()
    for pl in post_likes:
        await db.delete(pl)
    post_favs = (await db.execute(select(PostFavorite).where(PostFavorite.post_id == post_id))).scalars().all()
    for pf in post_favs:
        await db.delete(pf)

    await db.delete(p)
    await db.commit()
    return api_response(data={"message": "帖子已删除"})
