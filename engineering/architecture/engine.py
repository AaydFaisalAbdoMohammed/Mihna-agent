from typing import Any, Dict
from engineering.architecture.assumptions import ArchitecturalAssumptions
from engineering.shared.validation import CommonValidator

class ArchitecturalEngine:
    def __init__(self, assumptions: ArchitecturalAssumptions = ArchitecturalAssumptions()):
        self.assumptions = assumptions

    def generate_layout(self, land_area: float, num_floors: int) -> Dict[str, Any]:
        land_area = CommonValidator.validate_positive_number(land_area, "land_area")
        num_floors = int(CommonValidator.validate_positive_number(num_floors, "num_floors"))

        floor_plate = land_area * self.assumptions.DEFAULT_SITE_COVERAGE
        total_built_area = floor_plate * num_floors
        estimated_cost = total_built_area * self.assumptions.COST_PER_SQM_BASE

        return {
            "land_area": land_area,
            "num_floors": num_floors,
            "floor_plate_sqm": round(floor_plate, 2),
            "total_built_area_sqm": round(total_built_area, 2),
            "estimated_cost_usd": round(estimated_cost, 2)
        }
