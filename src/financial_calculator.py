def calculate_finances(income: float, expenses: dict, savings: float, debt: float) -> dict:
    total_expenses = sum(expenses.values())
    remaining_income = income - total_expenses
    
    # Guard against division by zero
    if income > 0:
        savings_ratio = (savings / income) * 100
        expense_ratio = (total_expenses / income) * 100
        debt_ratio = (debt / income) * 100
    else:
        savings_ratio = 0.0
        expense_ratio = 0.0
        debt_ratio = 0.0

    # Weighted 0-100 heuristic score
    # Higher savings & leftover income improve score; high expense/debt ratios lower it.
    score = 50.0
    score += min(savings_ratio * 0.5, 25.0)
    score += 15.0 if remaining_income > 0 else -20.0
    score -= min(max(expense_ratio - 50, 0) * 0.4, 30.0)
    score -= min(debt_ratio * 0.5, 20.0)
    
    preliminary_score = max(0.0, min(100.0, score))

    return {
        "total_expenses": round(total_expenses, 2),
        "remaining_income": round(remaining_income, 2),
        "savings_ratio": round(savings_ratio, 2),
        "expense_ratio": round(expense_ratio, 2),
        "preliminary_score": round(preliminary_score, 1)
    }