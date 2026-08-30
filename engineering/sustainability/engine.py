from typing import Any, Dict

class SustainabilityEngine:
    def evaluate(self, total_built_area: float) -> Dict[str, Any]:
        annual_kwh = total_built_area * 110.0
        solar_capacity_kwp = (annual_kwh / 365.0) / 4.5
        co2_tons = total_built_area * 0.24

        return {
            "annual_energy_kwh": round(annual_kwh, 2),
            "solar_pv_kwp_recommended": round(solar_capacity_kwp, 2),
            "co2_footprint_tons": round(co2_tons, 2),
            "insulation_rating": "XPS 50mm Recommended"
        }
