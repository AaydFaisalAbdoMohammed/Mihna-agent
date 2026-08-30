class EngineeringBaseException(Exception):
    """Base exception for all domain & engineering errors."""
    pass

class ValidationError(EngineeringBaseException):
    pass

class BlueprintSecurityError(EngineeringBaseException):
    pass

class AIProviderError(EngineeringBaseException):
    pass

class CalculationError(EngineeringBaseException):
    pass
