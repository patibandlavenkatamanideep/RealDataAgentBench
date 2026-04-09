from .generators.income_distribution import generate as generate_income
from .generators.patient_records import generate as generate_patient
from .generators.ecommerce_transactions import generate as generate_ecommerce

GENERATORS = {
    "income_distribution": generate_income,
    "patient_records": generate_patient,
    "ecommerce_transactions": generate_ecommerce,
}


def get_generator(name: str):
    if name not in GENERATORS:
        raise KeyError(f"Unknown generator: {name!r}. Available: {list(GENERATORS)}")
    return GENERATORS[name]
