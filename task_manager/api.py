from itertools import count

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Task Manager")


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    status: str = "TODO"


tasks: dict[int, dict[str, int | str]] = {}
task_ids = count(1)


@app.get("/tasks")
def list_tasks(
    status: str | None = None,
) -> list[dict[str, int | str]]:
    if status is None:
        return list(tasks.values())

    result: list[dict[str, int | str]] = []

    for task in tasks.values():
        if task["status"] == status:
            result.append(task)

    return result


@app.get("/tasks/{task_id}")
def get_task(task_id: int) -> dict[str, int | str]:
    if task_id not in tasks:
        raise HTTPException(
            status_code=404,
            detail="Khong tim thay task",
        )

    return tasks[task_id]


@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate) -> dict[str, int | str]:
    task_id = next(task_ids)

    new_task: dict[str, int | str] = {
        "id": task_id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
    }

    tasks[task_id] = new_task
    return new_task