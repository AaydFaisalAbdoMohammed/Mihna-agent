import math
from typing import Any, Dict

class StructuralEngine:
    def assess(self, total_area: float, floors: int, live_load_kn: float = 2.0) -> Dict[str, Any]:
        dead_load = 3.5
        factored_load = (1.2 * dead_load) + (1.6 * live_load_kn)
        total_load = total_area * floors * factored_load
        columns_count = max(4, int(math.ceil(total_area / 16.0)))

        return {
            "factored_load_kn_m2": round(factored_load, 2),
            "total_gravity_load_kn": round(total_load, 2),
            "estimated_columns_count": columns_count,
            "recommended_concrete": "C30/37 (f'c = 30 MPa)",
            "is_preliminary": True
        }
