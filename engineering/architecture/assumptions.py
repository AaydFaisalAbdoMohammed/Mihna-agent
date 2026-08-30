from dataclasses import dataclass

@dataclass(frozen=True)
class ArchitecturalAssumptions:
    DEFAULT_SITE_COVERAGE: float = 0.65
    CIRCULATION_RATIO: float = 0.15
    COST_PER_SQM_BASE: float = 350.0
