import json
import logging
from typing import List
from groq import Groq
from app.config import get_settings
from app.services.parser import ParsedTestCase

logger = logging.getLogger(__name__)

PLAN_SYSTEM_PROMPT = """You are a test automation agent that converts plain-English test steps into executable Playwright actions.

Given test cases with plain-English steps, generate a structured JSON execution plan.

For each step, determine:
- "intent": one of [OPEN, NAVIGATE, INPUT, CLICK, VERIFY, SELECT, CHECK, UNCHECK, PRESS_KEY, WAIT, HOVER, SCROLL]
- "target": what element to interact with (e.g., "username field", "Login button"). null for OPEN/NAVIGATE/WAIT if not applicable.
- "target_description": a human-readable description of what you're looking for
- "value": the value/URL/text to use. null if not applicable.
- "playwright_action": an object describing the exact Playwright async action:
  - For goto/navigate: {"method": "goto", "url": "..."}
  - For fill/type: {"method": "fill", "locator": {"strategy": "placeholder|label|text|role|css", "value": "..."}, "text": "..."}
  - For click: {"method": "click", "locator": {"strategy": "role|text|label|placeholder|css", "value": "...", "name": "..."}}
  - For verify: {"method": "wait_for_selector", "locator": {"strategy": "text|css|role", "value": "..."}} or {"method": "assert_text_visible", "text": "..."}
  - For select: {"method": "select_option", "locator": {"strategy": "label|placeholder|css", "value": "..."}, "option": "..."}
  - For check/uncheck: {"method": "check", "locator": {"strategy": "label|text|css", "value": "..."}} or {"method": "uncheck", "locator": {...}}
  - For press_key: {"method": "press", "key": "Enter|Escape|Tab|..."}
  - For wait: {"method": "wait_for_timeout", "ms": 2000} or {"method": "wait_for_selector", "locator": {...}}

CRITICAL RULES:
1. NEVER invent URLs, credentials, or selectors. Use ONLY what is mentioned in the steps.
2. Prefer semantic locators: role > label > placeholder > text > testid > css. NO xpath.
3. For "Enter X in Y field" → use fill with the best matching locator strategy.
4. For "Click X" → identify if X is a button, link, or generic element. Prefer getByRole.
5. For "Verify X is displayed/visible" → use assert_text_visible or wait_for_selector.
6. For "Select X from Y dropdown" → use select_option.
7. If a step is ambiguous (e.g., "Click the button" with no qualifier), set intent to "AMBIGUOUS" and note the ambiguity in the description.

Return ONLY valid JSON with this structure:
{
  "test_cases": [
    {
      "name": "Test case name",
      "module": "Optional module",
      "steps": [
        {
          "order": 1,
          "description": "original step text",
          "intent": "OPEN",
          "target": null,
          "target_description": null,
          "value": "https://example.com",
          "playwright_action": {"method": "goto", "url": "https://example.com"}
        }
      ]
    }
  ]
}"""


async def generate_execution_plan(
    test_cases: List[ParsedTestCase],
    groq_api_key: str,
    model: str | None = None,
) -> dict:
    settings = get_settings()
    model = model or settings.GROQ_MODEL
    api_key = groq_api_key or settings.GROQ_API_KEY

    if not api_key:
        raise ValueError("Groq API key is not configured. Please set it in AI Configuration.")

    client = Groq(api_key=api_key)

    test_cases_text = ""
    for i, tc in enumerate(test_cases):
        test_cases_text += f"\n## Test Case {i+1}: {tc.name}\n"
        if tc.module:
            test_cases_text += f"Module: {tc.module}\n"
        if tc.priority:
            test_cases_text += f"Priority: {tc.priority}\n"
        test_cases_text += "Steps:\n"
        for step in tc.steps:
            test_cases_text += f"{step.order}. {step.description}\n"

    user_prompt = f"""Generate an execution plan for the following test cases.

{test_cases_text}

Return ONLY the JSON plan. Do not include any explanatory text."""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": PLAN_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=4096,
        )

        content = response.choices[0].message.content
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        plan = json.loads(content)
        logger.info(f"Generated execution plan with {len(plan.get('test_cases', []))} test cases")
        return plan

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {e}")
        logger.error(f"Raw response: {content}")
        raise ValueError(f"AI returned invalid JSON. Please try again.")
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        raise


async def test_groq_connection(api_key: str, model: str | None = None) -> bool:
    settings = get_settings()
    model = model or settings.GROQ_MODEL

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Reply with just: OK"}],
        max_tokens=10,
    )
    return bool(response.choices[0].message.content)
