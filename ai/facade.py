from typing import Any, Dict, Optional
from ai.providers.gemini import GeminiProvider
from engineering.blueprint.validator import BlueprintValidator
from engineering.blueprint.guard import StrictBlueprintGuard
from engineering.architecture.engine import ArchitecturalEngine
from engineering.boq.engine import BOQEngine
from engineering.structural.preliminary import StructuralEngine
from engineering.sustainability.engine import SustainabilityEngine

class AIFacade:
    """Orchestrator الطبقة المركزية لتأطير العمليات المعقدة وتنفيذها بطلب واحد."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.provider = GeminiProvider(api_key=api_key)
        self.validator = BlueprintValidator()
        self.guard = StrictBlueprintGuard(self.provider)
        self.architecture = ArchitecturalEngine()
        self.boq = BOQEngine()
        self.structural = StructuralEngine()
        self.sustainability = SustainabilityEngine()

    def process_full_engineering_pipeline(self, file_bytes: bytes, mime_type: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        self.validator.validate(file_bytes, mime_type)
        guard_result = self.guard.inspect(file_bytes, mime_type)
        if not guard_result.get("is_valid_blueprint"):
            return {"success": False, "reason": guard_result.get("rejection_reason"), "stage": "GUARD_REJECTED"}

        area = float(metadata.get("land_area", 200.0))
        floors = int(metadata.get("floors", 1))

        arch_res = self.architecture.generate_layout(area, floors)
        boq_res = self.boq.calculate(built_area=arch_res["total_built_area_sqm"], floors=floors)
        struct_res = self.structural.assess(total_area=arch_res["total_built_area_sqm"], floors=floors)
        sust_res = self.sustainability.evaluate(total_built_area=arch_res["total_built_area_sqm"])

        return {
            "success": True,
            "security": guard_result,
            "architecture": arch_res,
            "boq": boq_res,
            "structural": struct_res,
            "sustainability": sust_res
        }
