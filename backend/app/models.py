from datetime import datetime
from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base


class Exam(Base):
    __tablename__ = "exams"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    total_marks: Mapped[float] = mapped_column(Float, default=0)
    marking_scheme: Mapped[str] = mapped_column(Text)  # answer key / rubric, free text
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    submissions = relationship("Submission", back_populates="exam", cascade="all, delete-orphan")


class Submission(Base):
    __tablename__ = "submissions"
    id: Mapped[int] = mapped_column(primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id"), index=True)
    student_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|processing|done|failed
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    total: Mapped[float | None] = mapped_column(Float, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    exam = relationship("Exam", back_populates="submissions")
    pages = relationship("Page", back_populates="submission", order_by="Page.idx", cascade="all, delete-orphan")


class Page(Base):
    __tablename__ = "pages"
    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), index=True)
    idx: Mapped[int] = mapped_column(Integer)
    original_path: Mapped[str] = mapped_column(String(500))
    cropped_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    annotated_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    submission = relationship("Submission", back_populates="pages")
