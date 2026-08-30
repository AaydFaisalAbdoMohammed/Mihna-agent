class BOQPricingProvider:
    REGIONAL_MULTIPLIERS = {
        "YE": 0.9,
        "SA": 1.2,
        "AE": 1.35,
        "DEFAULT": 1.0
    }

    BASE_PRICES = {
        "steel_ton": 750.0,
        "concrete_m3": 80.0,
        "blocks_unit": 0.75,
        "finishing_sqm": 45.0
    }

    @classmethod
    def get_prices(cls, region: str = "DEFAULT"):
        mult = cls.REGIONAL_MULTIPLIERS.get(region, cls.REGIONAL_MULTIPLIERS["DEFAULT"])
        return {k: round(v * mult, 2) for k, v in cls.BASE_PRICES.items()}
