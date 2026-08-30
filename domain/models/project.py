from dataclasses import dataclass

@dataclass
class Project:
    id: str
    name: str
    owner_id: str
    land_area: float
    num_floors: int
    budget_usd: float
    status: str = "DRAFT"
