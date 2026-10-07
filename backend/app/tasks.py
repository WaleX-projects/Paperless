from celery import Celery
from .ai import grade_pages
from .config import settings
from .db import SessionLocal
from .imaging import crop_paper
from .models import Submission
from .nosql import save_raw
from .services import recompute, render

celery = Celery("grader", broker=settings.redis_url, backend=settings.redis_url)


@celery.task(name="process_submission")
def process_submission(submission_id: int):
    db = SessionLocal()
    try:
        sub = db.get(Submission, submission_id)
        sub.status, sub.error = "processing", None
        db.commit()
        for p in sub.pages:
            crop_paper(p.original_path, p.cropped_path)
        result = grade_pages([p.cropped_path for p in sub.pages], sub.exam.marking_scheme, sub.exam.total_marks)
        save_raw(sub.id, result)
        sub.result = result
        if not sub.student_name and result.get("student_name"):
            sub.student_name = result["student_name"]
        recompute(sub)
        render(sub)
        sub.status = "done"
        db.commit()
    except Exception as e:
        db.rollback()
        sub = db.get(Submission, submission_id)
        sub.status, sub.error = "failed", str(e)[:500]
        db.commit()
    finally:
        db.close()
