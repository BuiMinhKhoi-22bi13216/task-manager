from typing import Any

from fastapi import APIRouter, Depends, Response

from ..dependencies import get_project_service
from ..project_service import ProjectService
from ..schemas import ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    service: ProjectService = Depends(get_project_service),
) -> list[dict[str, Any]]:
    return service.list_projects()


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int, service: ProjectService = Depends(get_project_service)
) -> dict[str, Any]:
    return service.get_project(project_id)


@router.post("", status_code=201, response_model=ProjectResponse)
def create_project(
    project: ProjectCreate, service: ProjectService = Depends(get_project_service)
) -> dict[str, Any]:
    return service.create_project(**project.model_dump())


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project: ProjectUpdate,
    service: ProjectService = Depends(get_project_service),
) -> dict[str, Any]:
    return service.update_project(project_id, project.model_dump(exclude_unset=True))


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: int, service: ProjectService = Depends(get_project_service)
) -> Response:
    service.delete_project(project_id)
    return Response(status_code=204)
