import hashlib, datetime
from typing import Any, Dict

class EscrowContractEngine:
    @staticmethod
    def evaluate(quality_score: float, completion_pct: float, milestone_budget: float) -> Dict[str, Any]:
        if quality_score < 75.0 or completion_pct < 100.0:
            return {"status": "FROZEN", "release_amount": 0.0, "reason": "Quality score or completion threshold not met."}

        tx_hash = hashlib.sha256(f"{datetime.datetime.utcnow()}_{milestone_budget}_ESCROW".encode()).hexdigest()
        return {"status": "RELEASED", "release_amount": milestone_budget, "tx_hash": tx_hash}
