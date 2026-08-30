from engineering.shared.errors import ValidationError

class CommonValidator:
    @staticmethod
    def validate_positive_number(val: float, name: str) -> float:
        if val is None or val <= 0:
            raise ValidationError(f"Field '{name}' must be a positive number greater than 0.")
        return float(val)

    @staticmethod
    def validate_range(val: float, min_val: float, max_val: float, name: str) -> float:
        if not (min_val <= val <= max_val):
            raise ValidationError(f"Field '{name}' must be between {min_val} and {max_val}.")
        return float(val)
