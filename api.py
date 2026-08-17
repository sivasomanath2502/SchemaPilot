"""
Phase 15: FastAPI wrapping the LangGraph pipeline.

The full pipeline takes 20+ minutes on CPU, so a request/response endpoint
that blocks for that long is impractical. Instead: POST /projects starts the
graph run as a background task (Starlette runs sync functions in a thread
pool automatically, so this doesn't block the event loop or other requests),
returns a project_id immediately, and GET /projects/{id} polls for status.

Uses an in-memory dict for job storage -- fine for a local demo. The
proposal's Section 14A "application database" (persisting projects to
MySQL) is a real extension, deliberately deferred past the MVP.
"""

import threading
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from graph import build_graph

app = FastAPI(title="Agentic AI Database Architecture Advisor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compiled once at startup, reused across requests -- graph.invoke() is
# stateless per call, so this is safe to share.
_graph_app = build_graph()

JOBS: dict[str, dict] = {}
JOBS_LOCK = threading.Lock()


class ProjectRequest(BaseModel):
    requirements: str


class ProjectStatus(BaseModel):
    project_id: str
    status: str  # "running" | "done" | "error"
    result: dict | None = None
    error: str | None = None


def _run_graph_job(project_id: str, user_input: str) -> None:
    try:
        final_state = _graph_app.invoke({
            "user_input": user_input,
            "requirement": {},
            "selection": {},
            "schema": {},
            "review": {},
            "cycle_count": 0,
        })
        with JOBS_LOCK:
            JOBS[project_id]["status"] = "done"
            JOBS[project_id]["result"] = final_state
    except Exception as e:
        with JOBS_LOCK:
            JOBS[project_id]["status"] = "error"
            JOBS[project_id]["error"] = str(e)


@app.post("/projects", response_model=ProjectStatus)
def create_project(request: ProjectRequest, background_tasks: BackgroundTasks):
    project_id = str(uuid.uuid4())
    with JOBS_LOCK:
        JOBS[project_id] = {
            "status": "running",
            "result": None,
            "error": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    background_tasks.add_task(_run_graph_job, project_id, request.requirements)
    return ProjectStatus(project_id=project_id, status="running")


@app.get("/projects/{project_id}", response_model=ProjectStatus)
def get_project(project_id: str):
    with JOBS_LOCK:
        job = JOBS.get(project_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectStatus(
        project_id=project_id, status=job["status"], result=job["result"], error=job["error"]
    )


@app.get("/health")
def health():
    return {"status": "ok"}