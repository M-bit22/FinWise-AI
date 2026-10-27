# FinWise AI — Dark Fintech Workspace

An educational personal-finance dashboard built with Streamlit, Python, LangChain, and Google Gemini.

## Features
- ChatGPT-inspired compact sidebar navigation with Dashboard, Budget Planner, Spending Analysis, AI Insights, and Settings.
- Dedicated Settings page with tabs for profile currency, AI analysis, app preferences, and About.
- Profile currency is included in the prompt so Gemini interprets all entered money values in the selected denomination. This does not perform live currency conversion.
- Deterministic Python calculations for monthly expenses, remaining income, savings ratio, expense ratio, and a heuristic health score.
- Plain-English dashboard explanations and fallback priorities so the dashboard remains useful if Gemini is unavailable.
- Gemini JSON response parsing, one retry without JSON mode, and an additional JSON-repair attempt.
- Raw AI diagnostics are available in AI Insights and Settings instead of interrupting the dashboard with a generic parsing message.
- Dark Matplotlib charts with clockwise-rotated x-axis labels.
- CSV export of the financial snapshot.
- Configurable in-memory or SQLite LangChain caching.

## Setup
1. Extract this ZIP.
2. Create a virtual environment (recommended).
3. Install packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and add your own Google Gemini API key:
   ```env
   GOOGLE_API_KEY=YOUR_GEMINI_API_KEY_HERE
   GEMINI_MODEL=gemini-2.5-flash
   ```
5. Run the app from the `finwise_ai` directory:
   ```bash
   streamlit run app.py
   ```

## Important notes
- The selected currency is the denomination for the amounts entered. No exchange-rate conversion is performed.
- The financial health score is a simple educational heuristic, not a validated credit score or financial-risk model.
- AI output can be incorrect; review recommendations carefully and do not treat them as certified financial, tax, or investment advice.
- Financial inputs are held in the Streamlit session; this app does not connect to a bank or execute transactions.
- Never commit `.env` or expose your API key.
