from sqlalchemy.orm import Session
from models import EmissionFactor

EMISSION_FACTORS = [
    {"fuel_type": "natural_gas", "scope": 1, "unit": "m3", "value": 2.03, "geography": "Global"},
    {"fuel_type": "natural_gas", "scope": 1, "unit": "m3", "value": 1.93, "geography": "US"},
    {"fuel_type": "diesel", "scope": 1, "unit": "liters", "value": 2.68, "geography": "Global"},
    {"fuel_type": "diesel", "scope": 1, "unit": "liters", "value": 2.70, "geography": "US"},
    {"fuel_type": "petrol", "scope": 1, "unit": "liters", "value": 2.31, "geography": "Global"},
    {"fuel_type": "petrol", "scope": 1, "unit": "liters", "value": 2.35, "geography": "US"},
    {"fuel_type": "lpg", "scope": 1, "unit": "liters", "value": 1.56, "geography": "Global"},
    {"fuel_type": "coal", "scope": 1, "unit": "kg", "value": 2.42, "geography": "Global"},
    {"fuel_type": "electricity", "scope": 2, "unit": "kWh", "value": 0.385, "geography": "US"},
    {"fuel_type": "electricity", "scope": 2, "unit": "kWh", "value": 0.212, "geography": "UK"},
    {"fuel_type": "electricity", "scope": 2, "unit": "kWh", "value": 0.255, "geography": "EU"},
    {"fuel_type": "electricity", "scope": 2, "unit": "kWh", "value": 0.708, "geography": "IN"},
    {"fuel_type": "electricity", "scope": 2, "unit": "kWh", "value": 0.475, "geography": "Global"},
    {"fuel_type": "electricity", "scope": 2, "unit": "kWh", "value": 0.350, "geography": "DE"},
]


def seed_emission_factors(db: Session):
    count = db.query(EmissionFactor).count()
    if count == 0:
        for factor_data in EMISSION_FACTORS:
            factor = EmissionFactor(**factor_data)
            db.add(factor)
        db.commit()
        print(f"Seeded {len(EMISSION_FACTORS)} emission factors.")
    else:
        print(f"EmissionFactor table already contains {count} records. Skipping seed.")
