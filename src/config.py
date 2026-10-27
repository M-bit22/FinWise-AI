import os
from dotenv import load_dotenv

load_dotenv()

# Gemini Free API Model configuration
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

CURRENCIES = ["USD ($)", "PKR (Rs)", "EUR (€)", "GBP (£)"]
FINANCIAL_GOALS = [
    "Save money",
    "Emergency fund",
    "Pay off debt",
    "Vacation",
    "Start a business",
    "Improve budgeting",
]