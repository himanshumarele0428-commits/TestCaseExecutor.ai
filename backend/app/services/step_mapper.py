"""
Direct rule-based step-to-action mapper.
Converts plain-English test steps into Playwright actions WITHOUT needing any AI/LLM.
Falls back to Groq AI only when a step doesn't match any known pattern.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Patterns ordered by specificity — first match wins
PATTERNS = [
    # "open <url>" / "navigate to <url>" / "go to <url>" / "login to <url>"
    (re.compile(r'(?:open|navigate\s+to|go\s+to|login\s+to)\s+(https?://[^\s]+)', re.IGNORECASE),
     lambda m: {"method": "goto", "url": m.group(1)}),

    # "enter '<text>' in <field>" / "type '<text>' in <field>" (quoted)
    (re.compile(r'^(?:enter|type|input)\s+["' + "'" + r'"](.+?)["' + "'" + r'"]\s+(?:in|into)\s+(?:the\s+)?(.+)', re.IGNORECASE),
     lambda m: {"method": "fill", "locator": _locator_for(m.group(2)), "text": m.group(1)}),
    (re.compile(r'^(?:fill|type)\s+(?:the\s+)?(.+?)\s+with\s+["' + "'" + r'"](.+?)["' + "'" + r'"]', re.IGNORECASE),
     lambda m: {"method": "fill", "locator": _locator_for(m.group(1)), "text": m.group(2)}),

    # "enter <field> as <value>" (field description first, then value after "as")
    (re.compile(r'^(?:enter|type|input)\s+(?:the\s+)?(.+?)\s+as\s+(.+)$', re.IGNORECASE),
     lambda m: {"method": "fill", "locator": _locator_for(m.group(1)), "text": m.group(2)}),

    # "type '<text>'" (bare, use active element)
    (re.compile(r'^(?:enter|type|input)\s+["' + "'" + r'"](.+?)["' + "'" + r'"]\s*$', re.IGNORECASE),
     lambda m: {"method": "type_text", "text": m.group(1)}),

    # "enter <value> in <field>" (unquoted, fallback)
    (re.compile(r'^(?:enter|type|input)\s+(.+?)\s+(?:in|into)\s+(?:the\s+)?(.+)$', re.IGNORECASE),
     lambda m: {"method": "fill", "locator": _locator_for(m.group(2)), "text": m.group(1)}),

    # "click <element>" / "click on <element>" / "click the <element>"
    (re.compile(r'^(?:double[-\s]?)?click\s+(?:on\s+)?(?:the\s+)?(.+)', re.IGNORECASE),
     lambda m: {"method": "dblclick" if "double" in m.string.lower() else "click", "locator": _locator_for(m.group(1))}),

    # "press <key>"
    (re.compile(r'^press\s+(.+)', re.IGNORECASE),
     lambda m: {"method": "press", "key": m.group(1).strip()}),

    # "select <option> from <dropdown>" / "choose <option> in <dropdown>"
    (re.compile(r'^(?:select|choose)\s+(?:the\s+)?(.+?)\s+(?:from|in)\s+(?:the\s+)?(.+)', re.IGNORECASE),
     lambda m: {"method": "select_option", "locator": _locator_for(m.group(2)), "option": m.group(1)}),

    # "check <checkbox>" / "tick <checkbox>"
    (re.compile(r'^(?:check|tick|enable)\s+(?:the\s+)?(.+)', re.IGNORECASE),
     lambda m: {"method": "check", "locator": _locator_for(m.group(1))}),

    # "uncheck <checkbox>"
    (re.compile(r'^uncheck\s+(?:the\s+)?(.+)', re.IGNORECASE),
     lambda m: {"method": "uncheck", "locator": _locator_for(m.group(1))}),

    # "verify <text/element> is (displayed|visible|present)" / "assert <text> appears"
    (re.compile(r'^(?:verify|assert|confirm|ensure|check)\s+(?:that\s+)?(?:the\s+)?(.+?)\s+(?:is\s+)?(?:displayed|visible|present|shown|appears)', re.IGNORECASE),
     lambda m: {"method": "assert_text_visible", "text": m.group(1).strip()}),

    # "verify page contains <text>"
    (re.compile(r'(?:verify|assert).*?(?:page\s+)?contains?\s+["' + "'" + r'"](.+?)["' + "'" + r'"]', re.IGNORECASE),
     lambda m: {"method": "assert_text_visible", "text": m.group(1)}),

    # "wait <N> seconds" / "wait for <N> seconds"
    (re.compile(r'^wait\s+(?:for\s+)?(\d+)\s*(?:seconds?|secs?|s)', re.IGNORECASE),
     lambda m: {"method": "wait_for_timeout", "ms": int(m.group(1)) * 1000}),

    # "wait for <element> to (appear|load|be visible)"
    (re.compile(r'^wait\s+(?:for\s+)?(?:the\s+)?(.+?)\s+to\s+(?:appear|load|be\s+visible)', re.IGNORECASE),
     lambda m: {"method": "wait_for_selector", "locator": _locator_for(m.group(1))}),

    # "hover over <element>"
    (re.compile(r'^(?:hover|move\s+to)\s+(?:over\s+)?(?:the\s+)?(.+)', re.IGNORECASE),
     lambda m: {"method": "hover", "locator": _locator_for(m.group(1))}),

    # "scroll to <element>"
    (re.compile(r'^scroll\s+(?:to|into)\s+(?:the\s+)?(.+)', re.IGNORECASE),
     lambda m: {"method": "scroll_into_view", "locator": _locator_for(m.group(1))}),

    # "clear <field>"
    (re.compile(r'^(?:clear|reset)\s+(?:the\s+)?(.+)', re.IGNORECASE),
     lambda m: {"method": "fill", "locator": _locator_for(m.group(1)), "text": ""}),

    # "refresh the page" / "reload"
    (re.compile(r'^(?:refresh|reload)(?:\s+(?:the\s+)?page)?', re.IGNORECASE),
     lambda _: {"method": "reload"}),

    # "go back" / "navigate back"
    (re.compile(r'^(?:go|navigate)\s+back', re.IGNORECASE),
     lambda _: {"method": "go_back"}),
]


def _normalize_field_name(text: str) -> str:
    """Normalize common field name variations to standard forms."""
    lower = text.lower().strip()
    replacements = {
        "user name": "username",
        "pass word": "password",
        "first name": "first name",
        "last name": "last name",
        "phone number": "phone",
        "zip code": "zip",
    }
    for key, val in replacements.items():
        if key in lower:
            # Swap the variation with standard form
            text_lower = text.lower()
            idx = text_lower.find(key)
            if idx >= 0:
                # Use the same casing pattern as original
                text = text[:idx] + val + text[idx + len(key):]
    return text


def _locator_for(text: str) -> dict:
    """Determine the best locator strategy for an element description."""
    text = text.strip().rstrip(".")

    # Strip leading article words
    text = re.sub(r'^(the|a|an)\s+', '', text, flags=re.IGNORECASE)

    # If it contains quotes, treat as exact text
    quoted = re.match(r'^["' + "'" + r'"](.+?)["' + "'" + r'"]$', text)
    if quoted:
        return {"strategy": "text", "value": quoted.group(1)}

    # Normalize common field name variations
    normalized = _normalize_field_name(text)

    # Check for known field types
    lower = normalized.lower()
    for field_type, strategy in [
        ("button", "role"), ("link", "role"), ("checkbox", "role"),
        ("textbox", "role"), ("combobox", "role"), ("radio", "role"),
        ("password field", "placeholder"), ("username field", "placeholder"),
        ("email field", "placeholder"), ("search field", "placeholder"),
        ("user name", "placeholder"), ("username", "placeholder"),
        ("password", "placeholder"), ("email", "placeholder"),
        ("search", "placeholder"), ("first name", "placeholder"),
        ("last name", "placeholder"), ("phone", "placeholder"),
        ("zip", "placeholder"), ("address", "placeholder"),
    ]:
        if field_type in lower:
            val = normalized.replace(" field", "").replace(" Field", "")
            if "button" in lower:
                return {"strategy": "role", "value": "button", "name": val.replace(" button", "")}
            if "link" in lower:
                return {"strategy": "role", "value": "link", "name": val.replace(" link", "")}
            if "checkbox" in lower:
                return {"strategy": "role", "value": "checkbox", "name": val.replace(" checkbox", "")}
            if "radio" in lower:
                return {"strategy": "role", "value": "radio", "name": val.replace(" radio", "")}
            return {"strategy": strategy, "value": val}

    # If text looks like a specific label (contains "field", "dropdown", "input")
    if re.search(r'(field|dropdown|input|box|menu|tab|toggle|switch)', lower):
        return {"strategy": "placeholder", "value": text}

    # Default: text-based locator
    if any(kw in lower for kw in ["button", "link", "icon", "image", "logo"]):
        return {"strategy": "role", "value": text}

    return {"strategy": "text", "value": text}


def map_step_to_action(step_description: str) -> Optional[dict]:
    """Convert a plain-English step into a Playwright action dict. Returns None if no match."""
    for pattern, handler in PATTERNS:
        match = pattern.match(step_description)
        if match:
            action = handler(match)
            logger.debug(f"Direct-mapped step '{step_description[:60]}...' → {action['method']}")
            return action

    return None


def build_execution_plan(test_cases) -> dict:
    """Build a full execution plan from parsed test cases using direct mapping.
    test_cases can be either ParsedTestCase objects or plain dicts."""
    plan_tcs = []

    for tc in test_cases:
        tc_name = tc.name if hasattr(tc, 'name') else tc.get('name', 'Unnamed')
        tc_module = tc.module if hasattr(tc, 'module') else tc.get('module')
        steps = tc.steps if hasattr(tc, 'steps') else tc.get('steps', [])

        plan_steps = []
        for i, step in enumerate(steps):
            desc = step.description if hasattr(step, 'description') else step.get('description', '')
            order = step.order if hasattr(step, 'order') else step.get('order', i + 1)

            pw_action = map_step_to_action(desc)
            if pw_action:
                plan_steps.append({
                    "order": order,
                    "description": desc,
                    "intent": _infer_intent(pw_action["method"]),
                    "target": pw_action.get("locator", {}).get("value"),
                    "value": pw_action.get("text") or pw_action.get("url"),
                    "playwright_action": pw_action,
                })
            else:
                logger.warning(f"Could not directly map step: '{desc[:80]}'")
                plan_steps.append({
                    "order": order,
                    "description": desc,
                    "intent": "UNKNOWN",
                    "target": None,
                    "value": None,
                    "playwright_action": {},
                })

        plan_tcs.append({
            "name": tc_name,
            "module": tc_module,
            "steps": plan_steps,
        })

    return {"test_cases": plan_tcs}


_INTENT_MAP = {
    "goto": "NAVIGATE", "reload": "NAVIGATE", "go_back": "NAVIGATE",
    "fill": "INPUT", "type_text": "INPUT",
    "click": "CLICK", "dblclick": "CLICK",
    "select_option": "SELECT", "check": "CHECK", "uncheck": "UNCHECK",
    "press": "PRESS_KEY", "wait_for_timeout": "WAIT", "wait_for_selector": "WAIT",
    "assert_text_visible": "VERIFY", "hover": "HOVER", "scroll_into_view": "SCROLL",
}


def _infer_intent(method: str) -> str:
    return _INTENT_MAP.get(method, "UNKNOWN")
