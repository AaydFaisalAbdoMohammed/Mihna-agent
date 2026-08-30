from typing import Any, Dict
from engineering.boq.pricing import BOQPricingProvider
from engineering.shared.validation import CommonValidator

class BOQEngine:
    def calculate(self, built_area: float, floors: int = 1, region: str = "DEFAULT") -> Dict[str, Any]:
        built_area = CommonValidator.validate_positive_number(built_area, "built_area")
        prices = BOQPricingProvider.get_prices(region)

        steel_ton = built_area * 0.042
        concrete_m3 = built_area * 0.40
        blocks = built_area * 12.5

        items = [
            {"item": "Steel", "qty": round(steel_ton, 2), "unit": "Ton", "total": round(steel_ton * prices["steel_ton"], 2)},
            {"item": "Concrete", "qty": round(concrete_m3, 2), "unit": "m3", "total": round(concrete_m3 * prices["concrete_m3"], 2)},
            {"item": "Blocks", "qty": round(blocks, 0), "unit": "Pcs", "total": round(blocks * prices["blocks_unit"], 2)},
        ]
        subtotal = sum(i["total"] for i in items)
        return {"items": items, "subtotal_usd": subtotal, "contingency_10pct": round(subtotal * 0.10, 2), "total_usd": round(subtotal * 1.10, 2)}
