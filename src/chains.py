from langchain_google_genai import ChatGoogleGenerativeAI
from src.config import MODEL_NAME
from src.prompts import get_chat_prompt_template


def get_gemini_model(temperature=0.0, json_mode=True, streaming=False):
    """Create a Gemini chat model; JSON mode is optional for compatibility retries."""
    kwargs = {"model": MODEL_NAME, "temperature": temperature, "streaming": streaming}
    if json_mode:
        kwargs["model_kwargs"] = {"response_mime_type": "application/json"}
    return ChatGoogleGenerativeAI(**kwargs)


def get_finwise_chain(json_mode=True):
    """Build a fresh chain; caller can retry with json_mode=False."""
    return get_chat_prompt_template() | get_gemini_model(json_mode=json_mode, streaming=False)


def stream_recommendations(inputs):
    llm = get_gemini_model(json_mode=False, streaming=True)
    messages = get_chat_prompt_template().format_messages(**inputs)
    for chunk in llm.stream(messages):
        content = getattr(chunk, "content", "")
        if isinstance(content, str) and content:
            yield content
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("text"):
                    yield str(part["text"])
                elif getattr(part, "text", None):
                    yield str(part.text)


def repair_finwise_response(raw_response):
    """Ask Gemini to repair a malformed response into the expected JSON schema."""
    from langchain_google_genai import ChatGoogleGenerativeAI

    repair_prompt = (
        "Convert the model response below into one valid JSON object only. "
        "Do not add markdown fences or explanations. Preserve the original financial facts; "
        "do not invent values. Ensure every field exists and arrays are arrays. "
        "The object must contain these fields: financial_summary (string), key_findings (array of 4-8 plain-English strings), "
        "financial_health_score (integer 0-100), spending_analysis (array of objects with category, observation, recommendation), "
        "risk_level (LOW, MEDIUM, or HIGH), top_priorities (array of 6-8 concise actionable strings), "
        "budget_recommendations (array), savings_strategy (array), next_month_action_plan (array). "
        "If a field is missing, use a conservative empty value rather than inventing a fact.\n\n"
        "MALFORMED RESPONSE TO REPAIR:\n" + str(raw_response)[:10000]
    )
    model = get_gemini_model(json_mode=True, temperature=0.0, streaming=False)
    response = model.invoke(repair_prompt)
    return getattr(response, "content", response)
