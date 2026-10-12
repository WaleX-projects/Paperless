# Exam Grader

## Run with Docker Compose

Requirements: Docker with the Compose plugin and a valid OpenAI API key.

Create the backend environment file (PowerShell):

```powershell
Copy-Item backend\.env.example backend\.env
```

Edit `backend/.env` and set `OPENAI_API_KEY`, then start all services from the repository root:

```sh
docker compose up --build
```

Open the frontend at `http://localhost:8080` and the API docs at `http://localhost:8000/docs`.
Compose runs the frontend, FastAPI API, Celery worker, and Redis. SQLite data and uploaded
files persist in the `paperless_data` volume; Redis queue data persists in `redis_data`.
To stop the services, run `docker compose down`. To also erase persisted data, run
`docker compose down -v`.

For a non-local frontend URL, set `VITE_API_URL` to the public API URL before building
and add the frontend origin to `CORS_ORIGINS` in the backend environment.

## Deploy the frontend to GitHub Pages

The workflow in `.github/workflows/deploy-frontend.yml` builds and deploys the Vite app
when changes are pushed to `main`, or when run manually. In repository **Settings >
Pages**, select **GitHub Actions** as the build and deployment source. Add the repository
variable `VITE_API_URL` with the publicly reachable URL of the deployed FastAPI service;
the workflow fails instead of publishing a frontend configured to call localhost if the
variable is missing. Configure the backend's `CORS_ORIGINS` to allow the Pages site origin
(for this repository, `https://walex-projects.github.io`).

## Run
Needs Redis running (`redis-server`).

Backend:
    cd backend && python -m venv .venv && source .venv/bin/activate # for windows source .venv/Scripts/activate

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
