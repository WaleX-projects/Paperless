# Exam Grader

## Run
Needs Redis running (`redis-server`).

Backend:
    cd backend && python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt && cp .env.example .env   # add OPENAI_API_KEY
    uvicorn app.main:app --reload            # terminal 1
    celery -A app.tasks.celery worker -l info  # terminal 2

Frontend:
    cd frontend && npm install && npm run dev   # http://localhost:5173

## Flow
Create exam (paste marking scheme) -> upload photos of one student's pages -> Celery job:
crop paper edges (OpenCV) -> GPT vision grades + returns page/x/y per question -> check/X/score drawn on image.
Teacher can override any score in the UI; annotations re-render.

## Endpoints
POST /exams, GET /exams, DELETE /exams/{id}
POST /exams/{id}/submissions (multipart: files[], student_name)
GET /exams/{id}/submissions, GET /exams/{id}/export.csv
GET /submissions/{id}, POST /submissions/{id}/regrade, PATCH /submissions/{id}/questions/{number}
GET /pages/{id}/image?annotated=true

## DBs
SQL via SQLAlchemy (SQLite default, set DATABASE_URL for Postgres). Set MONGO_URL to also keep raw AI responses in MongoDB.
