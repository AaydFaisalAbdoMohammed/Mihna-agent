from typing import Any, Dict
from ai.facade import AIFacade
from domain.models.project import Project

class ProjectAnalysisDomainService:
    def __init__(self, ai_facade: AIFacade):
        self.ai_facade = ai_facade

    def execute_full_project_intake(self, project: Project, blueprint_bytes: bytes, mime_type: str) -> Dict[str, Any]:
        metadata = {"land_area": project.land_area, "floors": project.num_floors}
        analysis_res = self.ai_facade.process_full_engineering_pipeline(blueprint_bytes, mime_type, metadata)
        return {"project_id": project.id, "analysis": analysis_res}
