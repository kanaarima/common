
from __future__ import annotations

from app.common.database.objects import DBForumPost
from .wrapper import session_wrapper

from sqlalchemy.orm import Session
from typing import List

@session_wrapper
def create(
    topic_id: int,
    forum_id: int,
    user_id: int,
    content: str,
    draft: bool = False,
    edit_locked: bool = False,
    session: Session = ...
) -> DBForumPost:
    post = DBForumPost(
        topic_id=topic_id,
        forum_id=forum_id,
        user_id=user_id,
        content=content,
        draft=draft,
        edit_locked=edit_locked
    )
    session.add(post)
    session.commit()
    return post

@session_wrapper
def fetch_one(id: int, session: Session = ...) -> DBForumPost | None:
    return session.query(DBForumPost) \
        .filter(DBForumPost.id == id) \
        .first()

@session_wrapper
def fetch_all_by_topic(
    topic_id: int,
    session: Session = ...
) -> List[DBForumPost]:
    return session.query(DBForumPost) \
        .filter(DBForumPost.topic_id == topic_id) \
        .filter(DBForumPost.hidden == False) \
        .order_by(DBForumPost.id.asc()) \
        .all()

@session_wrapper
def fetch_range_by_topic(
    topic_id: int,
    range: int,
    offset: int,
    session: Session = ...
) -> List[DBForumPost]:
    return session.query(DBForumPost) \
        .filter(DBForumPost.topic_id == topic_id) \
        .filter(DBForumPost.hidden == False) \
        .order_by(DBForumPost.id.asc()) \
        .limit(range) \
        .offset(offset) \
        .all()

@session_wrapper
def fetch_initial_post(topic_id: int, session: Session = ...) -> DBForumPost | None:
    return session.query(DBForumPost) \
        .filter(DBForumPost.topic_id == topic_id) \
        .filter(DBForumPost.hidden == False) \
        .order_by(DBForumPost.id.asc()) \
        .first()

@session_wrapper
def fetch_last(topic_id: int, session: Session = ...) -> DBForumPost | None:
    return session.query(DBForumPost) \
        .filter(DBForumPost.topic_id == topic_id) \
        .filter(DBForumPost.hidden == False) \
        .order_by(DBForumPost.id.desc()) \
        .first()

@session_wrapper
def fetch_count(topic_id: int, session: Session = ...) -> int:
    return session.query(DBForumPost) \
        .filter(DBForumPost.topic_id == topic_id) \
        .filter(DBForumPost.hidden == False) \
        .count()

@session_wrapper
def update(
    post_id: int,
    updates: dict,
    session: Session = ...
) -> int:
    rows = session.query(DBForumPost) \
        .filter(DBForumPost.id == post_id) \
        .update(updates)
    session.commit()
    return rows
