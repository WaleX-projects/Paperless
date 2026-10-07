import csv
import io
from pathlib import Path
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .config import settings
from .db import Base, engine, get_db
from .models import Exam, Page, Submission
from .services import recompute, render
from .tasks import process_submission

Base.metadata.create_all(engine)
app = FastAPI(title="Exam Grader")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class ExamIn(BaseModel):
    title: str
    total_marks: float
    marking_scheme: str


class OverrideIn(BaseModel):
    awarded: float
    feedback: str | None = None


def exam_out(e: Exam):
    return {"id": e.id, "title": e.title, "total_marks": e.total_marks, "marking_scheme": e.marking_scheme}


def sub_out(s: Submission):
    return {
        "id": s.id, "exam_id": s.exam_id, "student_name": s.student_name, "status": s.status,
        "score": s.score, "total": s.total, "error": s.error,
        "questions": (s.result or {}).get("questions", []),
        "pages": [{"id": p.id, "idx": p.idx} for p in s.pages],
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


@app.post("/exams")
def create_exam(body: ExamIn, db: Session = Depends(get_db)):
    e = Exam(**body.model_dump())
    db.add(e); db.commit()
    return exam_out(e)


@app.get("/exams")
def list_exams(db: Session = Depends(get_db)):
    return [exam_out(e) for e in db.query(Exam).order_by(Exam.id.desc())]


@app.delete("/exams/{exam_id}", status_code=204)
def delete_exam(exam_id: int, db: Session = Depends(get_db)):
    e = db.get(Exam, exam_id) or HTTPException(404)
    if isinstance(e, HTTPException): raise e
    db.delete(e); db.commit()


@app.post("/exams/{exam_id}/submissions", status_code=202)
async def upload(exam_id: int, files: list[UploadFile] = File(...), student_name: str | None = Form(None),
                 db: Session = Depends(get_db)):
    if not db.get(Exam, exam_id):
        raise HTTPException(404, "Exam not found")
    if any(not (f.content_type or "").startswith("image/") for f in files):
        raise HTTPException(400, "Only image files are accepted")
    sub = Submission(exam_id=exam_id, student_name=student_name or None)
    db.add(sub); db.flush()
    folder = Path(settings.upload_dir) / str(sub.id)
    folder.mkdir(parents=True, exist_ok=True)
    for i, f in enumerate(files):
        ext = Path(f.filename or "").suffix.lower() or ".jpg"
        orig = folder / f"orig_{i}{ext}"
        orig.write_bytes(await f.read())
        db.add(Page(submission_id=sub.id, idx=i, original_path=str(orig), cropped_path=str(folder / f"crop_{i}.jpg")))
    db.commit()
    process_submission.delay(sub.id)
    return {"id": sub.id, "status": sub.status}


@app.get("/exams/{exam_id}/submissions")
def list_submissions(exam_id: int, db: Session = Depends(get_db)):
    q = db.query(Submission).filter_by(exam_id=exam_id).order_by(Submission.id.desc())
    return [sub_out(s) for s in q]


@app.get("/submissions/{sid}")
def get_submission(sid: int, db: Session = Depends(get_db)):
    s = db.get(Submission, sid)
    if not s: raise HTTPException(404)
    return sub_out(s)


@app.post("/submissions/{sid}/regrade", status_code=202)
def regrade(sid: int, db: Session = Depends(get_db)):
    s = db.get(Submission, sid)
    if not s: raise HTTPException(404)
    s.status = "pending"; db.commit()
    process_submission.delay(sid)
    return {"id": sid, "status": "pending"}


@app.patch("/submissions/{sid}/questions/{number}")
def override(sid: int, number: str, body: OverrideIn, db: Session = Depends(get_db)):
    s = db.get(Submission, sid)
    if not s or not s.result: raise HTTPException(404)
    q = next((q for q in s.result["questions"] if q["number"] == number), None)
    if not q: raise HTTPException(404, "Question not found")
    q["awarded"] = body.awarded
    if body.feedback is not None: q["feedback"] = body.feedback
    recompute(s); render(s); db.commit()
    return sub_out(s)


@app.get("/pages/{pid}/image")
def page_image(pid: int, annotated: bool = True, db: Session = Depends(get_db)):
    p = db.get(Page, pid)
    if not p: raise HTTPException(404)
    path = (annotated and p.annotated_path) or p.cropped_path
    if not path or not Path(path).exists(): path = p.original_path
    return FileResponse(path)


@app.get("/exams/{exam_id}/export.csv")
def export(exam_id: int, db: Session = Depends(get_db)):
    buf = io.StringIO(); w = csv.writer(buf)
    w.writerow(["id", "student", "status", "score", "total"])
    for s in db.query(Submission).filter_by(exam_id=exam_id):
        w.writerow([s.id, s.student_name, s.status, s.score, s.total])
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": f"attachment; filename=exam_{exam_id}.csv"})
