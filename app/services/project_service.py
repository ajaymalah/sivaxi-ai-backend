from uuid import UUID

from sqlalchemy.orm import Session

from app.models.project import Project
from app.controllers.project.dto.project import ProjectCreate, ProjectUpdate


class ProjectService:

    def __init__(self, db: Session):
        self.db = db

    def create_project(
        self,
        user_id: str,
        request: ProjectCreate,
    ) -> Project:

        project = Project(
            user_id=user_id,
            name=request.name,
            description=request.description,
        )

        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)

        return project

    def get_projects(
        self,
        user_id: str,
    ) -> list[Project]:

        return (
            self.db.query(Project)
            .filter(Project.user_id == user_id)
            .order_by(Project.created_at.desc())
            .all()
        )

    def get_project(
            self,
            user_id: str,
            project_id: UUID,
    ) -> Project | None:
        return (
            self.db.query(Project)
            .filter(
                Project.id == project_id,
                Project.user_id == user_id,
            )
            .first()
        )

    def update_project(
            self,
            user_id: str,
            project_id: UUID,
            request: ProjectUpdate,
    ) -> Project | None:

        project = (
            self.db.query(Project)
            .filter(
                Project.id == project_id,
                Project.user_id == user_id,
            )
            .first()
        )

        if project is None:
            return None

        if request.name is not None:
            project.name = request.name

        if request.description is not None:
            project.description = request.description

        self.db.commit()
        self.db.refresh(project)

        return project

    def delete_project(
            self,
            user_id: str,
            project_id: UUID,
    ) -> bool:

        project = (
            self.db.query(Project)
            .filter(
                Project.id == project_id,
                Project.user_id == user_id,
            )
            .first()
        )

        if project is None:
            return False

        self.db.delete(project)
        self.db.commit()

        return True