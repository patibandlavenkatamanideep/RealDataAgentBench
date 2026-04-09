from .generators.income_distribution import generate as generate_income
from .generators.patient_records import generate as generate_patient
from .generators.ecommerce_transactions import generate as generate_ecommerce
from .generators.house_prices import generate as generate_house_prices
from .generators.employee_attrition import generate as generate_employee_attrition
from .generators.retail_sales import generate as generate_retail_sales
from .generators.credit_risk import generate as generate_credit_risk
from .generators.fraud_detection import generate as generate_fraud_detection

GENERATORS = {
    "income_distribution": generate_income,
    "patient_records": generate_patient,
    "ecommerce_transactions": generate_ecommerce,
    "house_prices": generate_house_prices,
    "employee_attrition": generate_employee_attrition,
    "retail_sales": generate_retail_sales,
    "credit_risk": generate_credit_risk,
    "fraud_detection": generate_fraud_detection,
}


def get_generator(name: str):
    if name not in GENERATORS:
        raise KeyError(f"Unknown generator: {name!r}. Available: {list(GENERATORS)}")
    return GENERATORS[name]
