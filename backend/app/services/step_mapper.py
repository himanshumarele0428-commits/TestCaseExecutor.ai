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
    # "open <url>" / "navigate to <url>" / "go to <url>"
    (re.compile(r'(?:^open|^navigate\s+to|^go\s+to)\s+(https?://[^\s]+)', re.IGNORECASE),
     lambda m, original=None: {"method": "goto", "url": m.group(1)}),

    # "Login to application <url>" / "go to URL <url>" — extract URL
    (re.compile(r'(?:login|go|navigate|open)\s+to\s+(?:application|app|site|page|url|website)\s+(https?://[^\s]+)', re.IGNORECASE),
     lambda m, original=None: {"method": "goto", "url": m.group(1)}),
    (re.compile(r'^(?:login)\s+to\s+(https?://[^\s]+)', re.IGNORECASE),
     lambda m, original=None: {"method": "goto", "url": m.group(1)}),

    # "enter '<text>' in <field>" / "type '<text>' in <field>" (quoted)
    (re.compile(r'^(?:enter|type|input)\s+["' + "'" + r'"](.+?)["' + "'" + r'"]\s+(?:in|into)\s+(?:the\s+)?(.+)', re.IGNORECASE),
     lambda m, original=None: {"method": "fill", "locator": _locator_for(m.group(2)), "text": m.group(1)}),
    (re.compile(r'^(?:fill|type)\s+(?:the\s+)?(.+?)\s+with\s+["' + "'" + r'"](.+?)["' + "'" + r'"]', re.IGNORECASE),
     lambda m, original=None: {"method": "fill", "locator": _locator_for(m.group(1)), "text": m.group(2)}),

    # "enter <field> as <value>" (field description first, then value after "as")
    (re.compile(r'^(?:enter|type|input)\s+(?:the\s+)?(.+?)\s+as\s+(.+)$', re.IGNORECASE),
     lambda m, original=None: {"method": "fill", "locator": _locator_for(m.group(1)), "text": m.group(2)}),

    # "type '<text>'" (bare, use active element)
    (re.compile(r'^(?:enter|type|input)\s+["' + "'" + r'"](.+?)["' + "'" + r'"]\s*$', re.IGNORECASE),
     lambda m, original=None: {"method": "type_text", "text": m.group(1)}),

    # "Type/Enter <field-type> <value> into <locator>" — handles "Type username student into Username field"
    # Must come BEFORE the generic "enter <value> in <field>" pattern to extract the value correctly
    (re.compile(r'^(?:enter|type|input)\s+(?:the\s+)?(username|password|email|phone|address|zip|search|name|first\s*name|last\s*name)\s+(.+?)\s+(?:in|into)\s+(?:the\s+)?(.+)$', re.IGNORECASE),
     lambda m, original=None: {"method": "fill", "locator": _locator_for(m.group(3)), "text": m.group(2)}),

    # "enter <value> in <field>" (unquoted, fallback)
    (re.compile(r'^(?:enter|type|input)\s+(.+?)\s+(?:in|into)\s+(?:the\s+)?(.+)$', re.IGNORECASE),
     lambda m, original=None: {"method": "fill", "locator": _locator_for(m.group(2)), "text": m.group(1)}),

    # "push <element>" / "submit <element>" — synonym for click
    (re.compile(r'^(?:push|submit)\s+(?:the\s+)?(.+)', re.IGNORECASE),
     lambda m, original=None: {"method": "click", "locator": _locator_for(m.group(1))}),

    # "click <element>" / "click on <element>" / "click the <element>"
    (re.compile(r'^(?:double[-\s]?)?click\s+(?:on\s+)?(?:the\s+)?(.+)', re.IGNORECASE),
     lambda m, original=None: {"method": "dblclick" if "double" in m.string.lower() else "click", "locator": _locator_for(m.group(1))}),

    # "press <key>"
    (re.compile(r'^press\s+(.+)', re.IGNORECASE),
     lambda m, original=None: {"method": "press", "key": m.group(1).strip()}),

    # "select <option> from <dropdown>" / "choose <option> in <dropdown>"
    (re.compile(r'^(?:select|choose)\s+(?:the\s+)?(.+?)\s+(?:from|in)\s+(?:the\s+)?(.+)', re.IGNORECASE),
     lambda m, original=None: {"method": "select_option", "locator": _locator_for(m.group(2)), "option": m.group(1)}),

    # "check <checkbox>" / "tick <checkbox>"
    (re.compile(r'^(?:check|tick|enable)\s+(?:the\s+)?(.+)', re.IGNORECASE),
     lambda m, original=None: {"method": "check", "locator": _locator_for(m.group(1))}),

    # "uncheck <checkbox>"
    (re.compile(r'^uncheck\s+(?:the\s+)?(.+)', re.IGNORECASE),
     lambda m, original=None: {"method": "uncheck", "locator": _locator_for(m.group(1))}),

    # "verify <text> is NOT (displayed|visible|present)" / "assert <text> does not appear"
    (re.compile(r'^(?:verify|assert|confirm|ensure|check)\s+(?:that\s+)?(?:the\s+)?(.+?)\s+(?:is\s+)?not\s+(?:displayed|visible|present|shown|appearing)', re.IGNORECASE),
     lambda m, original=None: {"method": "assert_text_not_visible", "text": m.group(1).strip()}),
    (re.compile(r'^(?:verify|assert|confirm|ensure|check)\s+(?:that\s+)?(?:the\s+)?(.+?)\s+does\s+(?:not|no)\s+(?:appear|show|display)', re.IGNORECASE),
     lambda m, original=None: {"method": "assert_text_not_visible", "text": m.group(1).strip()}),

    # "verify ... text is <text>" / "verify error message text is ..." / "verify ... contains ... text <text>"
    (re.compile(r'^(?:verify|assert|confirm|ensure|check)\s+(?:that\s+)?(?:the\s+)?(?:new\s+page\s+)?(?:error\s+message\s+)?(?:expected\s+)?(?:text|message)\s+(?:is|contains|says)\s+"?\'?\s*(.+?)\s*"?(?:\)|$)', re.IGNORECASE),
     lambda m, original=None: {"method": "assert_text_visible", "text": m.group(1).strip().strip('\'"')}),
    (re.compile(r'^(?:verify|assert|confirm|ensure|check)\s+(?:that\s+)?(?:the\s+)?(?:new\s+page\s+)?contains\s+(?:expected\s+)?text\s+(.+)', re.IGNORECASE),
     lambda m, original=None: {"method": "assert_text_visible", "text": m.group(1).strip().strip('()\'"')}),

    # "verify ... url contains <text>" (flexible: handles "Verify new page URL contains ...")
    (re.compile(r'^(?:verify|assert|confirm|check)\s+(?:that\s+)?(?:the\s+)?(?:new\s+page\s+)?url\s+(?:contains|has|includes)\s+(?:the\s+)?["' + "'" + r'"]?(.+?)["' + "'" + r'"]?$', re.IGNORECASE),
     lambda m, original=None: {"method": "assert_url_contains", "text": m.group(1).strip().strip('"\'')}),
    (re.compile(r'^(?:verify|assert|confirm|check)\s+(?:that\s+)?(?:the\s+)?(?:new\s+page\s+)?url\s+is\s+["' + "'" + r'"]?(.+?)["' + "'" + r'"]?$', re.IGNORECASE),
     lambda m, original=None: {"method": "assert_url_equals", "text": m.group(1).strip().strip('"\'')}),

    # "verify title contains <text>" / "assert page title is <text>"
    (re.compile(r'^(?:verify|assert|confirm|check)\s+(?:that\s+)?(?:the\s+)?(?:page\s+)?title\s+(?:contains|has|includes)\s+(?:the\s+)?["' + "'" + r'"]?(.+?)["' + "'" + r'"]?$', re.IGNORECASE),
     lambda m, original=None: {"method": "assert_title_contains", "text": m.group(1).strip().strip('"\'')}),
    (re.compile(r'^(?:verify|assert|confirm|check)\s+(?:that\s+)?(?:the\s+)?(?:page\s+)?title\s+is\s+["' + "'" + r'"]?(.+?)["' + "'" + r'"]?$', re.IGNORECASE),
     lambda m, original=None: {"method": "assert_title_equals", "text": m.group(1).strip().strip('"\'')}),

    # "verify the <element> is displayed/visible" — quoted element assertion
    (re.compile(r'^(?:verify|assert|confirm|ensure|check)\s+(?:that\s+)?(?:the\s+)?(["\'])(.+?)\1\s+(?:is\s+)?(?:displayed|visible|present|shown|exists)', re.IGNORECASE),
     lambda m, original=None: {"method": "assert_element_visible", "locator": _locator_for(m.group(2))}),

    # "verify <text/element> is (displayed|visible|present)" / "assert <text> appears"
    # Also match "Verify that ... is displayed", "Verify that ... is visible"
    (re.compile(r'^(?:verify|assert|confirm|ensure|check)\s+(?:that\s+)?(?:the\s+)?(.+?)\s+(?:is\s+)?(?:displayed|visible|present|shown|appears)', re.IGNORECASE),
     lambda m, original=None: {"method": "assert_text_visible", "text": m.group(1).strip()}),

    # "verify the <element> is displayed/visible" — non-quoted element assertion (fallback, doesn't require $)
    (re.compile(r'^(?:verify|assert|confirm|ensure|check)\s+(?:that\s+)?(?:the\s+)?([^"\']+?)\s+(?:is\s+)?(?:displayed|visible|present|shown|exists)\s*(?:on\s+(?:the\s+)?.*)?$', re.IGNORECASE),
     lambda m, original=None: {"method": "assert_element_visible", "locator": _locator_for(m.group(1).strip().rstrip('.'))}),

    # "verify page contains <text>"
    (re.compile(r'(?:verify|assert).*?(?:page\s+)?contains?\s+["' + "'" + r'"](.+?)["' + "'" + r'"]', re.IGNORECASE),
     lambda m, original=None: {"method": "assert_text_visible", "text": m.group(1)}),

    # "wait <N> seconds" / "wait for <N> seconds"
    (re.compile(r'^wait\s+(?:for\s+)?(\d+)\s*(?:seconds?|secs?|s)', re.IGNORECASE),
     lambda m, original=None: {"method": "wait_for_timeout", "ms": int(m.group(1)) * 1000}),

    # "wait for <element> to (appear|load|be visible)"
    (re.compile(r'^wait\s+(?:for\s+)?(?:the\s+)?(.+?)\s+to\s+(?:appear|load|be\s+visible)', re.IGNORECASE),
     lambda m, original=None: {"method": "wait_for_selector", "locator": _locator_for(m.group(1))}),

    # "hover over <element>"
    (re.compile(r'^(?:hover|move\s+to)\s+(?:over\s+)?(?:the\s+)?(.+)', re.IGNORECASE),
     lambda m, original=None: {"method": "hover", "locator": _locator_for(m.group(1))}),

    # "scroll to <element>"
    (re.compile(r'^scroll\s+(?:to|into)\s+(?:the\s+)?(.+)', re.IGNORECASE),
     lambda m, original=None: {"method": "scroll_into_view", "locator": _locator_for(m.group(1))}),

    # "clear <field>"
    (re.compile(r'^(?:clear|reset)\s+(?:the\s+)?(.+)', re.IGNORECASE),
     lambda m, original=None: {"method": "fill", "locator": _locator_for(m.group(1)), "text": ""}),

    # "refresh the page" / "reload"
    (re.compile(r'^(?:refresh|reload)(?:\s+(?:the\s+)?page)?', re.IGNORECASE),
     lambda m, original=None: {"method": "reload"}),

    # "go back" / "navigate back"
    (re.compile(r'^(?:go|navigate)\s+back', re.IGNORECASE),
     lambda m, original=None: {"method": "go_back"}),
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


def _heuristic_fallback(step_description: str) -> dict:
    """Intelligent fallback for any step that doesn't match regex patterns.
    Uses NLP heuristics: first word intent + keyword extraction to build a reasonable action."""
    desc = step_description.strip()
    desc_lower = desc.lower()
    words = desc.split()

    if not words:
        return {"method": "wait_for_timeout", "ms": 1000}

    first = words[0].lower().rstrip(":.")

    # Extract URL if present
    url_match = re.search(r'(https?://[^\s]+)', desc)
    if url_match:
        return {"method": "goto", "url": url_match.group(1)}

    # PRESS_KEY: single-word keys or "press Enter" etc.
    if first in ("press", "hit"):
        key = words[-1] if len(words) > 1 else "Enter"
        return {"method": "press", "key": key}

    # INPUT: type/enter/fill/input
    if first in ("type", "enter", "fill", "input", "write", "put", "provide"):
        # Try to split: "Type <value> into <field>" or "Enter <value> in <field>"
        into_match = re.search(r'(?:in|into)\s+(?:the\s+)?(.+?)$', desc, re.IGNORECASE)
        field = into_match.group(1) if into_match else ""
        # Extract value: everything between the verb and "in/into"
        if into_match:
            value_start = desc_lower.index(into_match.group(0).lower())
            value_before = desc[:value_start].strip()
            # Remove leading verb word
            value_words = value_before.split()
            value = " ".join(value_words[1:]) if len(value_words) > 1 else ""
        else:
            # No "in/into" — just take everything after the first word
            value = " ".join(words[1:])
            field = ""

        value = value.strip().strip("'\"")
        field = field.strip().strip("'\".:")

        if field:
            return {"method": "fill", "locator": _locator_for(field), "text": value}
        else:
            # No specific field — type into focused element
            return {"method": "type_text", "text": value}

    # CLICK: click/push/tap/hit/submit
    if first in ("click", "push", "tap", "hit", "submit", "press"):
        # Find the target: everything after the verb
        target = " ".join(words[1:]).strip()
        if not target:
            target = "button"
        # Strip "the"/"on"
        target = re.sub(r'^(?:the|on|a|an)\s+', '', target, flags=re.IGNORECASE)
        return {"method": "click", "locator": _locator_for(target)}

    # VERIFY/ASSERT
    if first in ("verify", "assert", "confirm", "ensure", "check"):
        # Check for URL patterns
        if url_match:
            return {"method": "assert_url_contains", "text": url_match.group(1)}

        # "Verify X is displayed/visible" 
        is_match = re.search(r'(.+?)\s+(?:is\s+)?(?:displayed|visible|present|shown)', desc, re.IGNORECASE)
        if is_match:
            return {"method": "assert_text_visible", "text": is_match.group(1).strip()}

        # "Verify X is not displayed"
        not_match = re.search(r'(.+?)\s+(?:is\s+)?not\s+(?:displayed|visible|present)', desc, re.IGNORECASE)
        if not_match:
            return {"method": "assert_text_not_visible", "text": not_match.group(1).strip()}

        # "Verify message/error/text X"
        msg_match = re.search(r'(?:message|text|error)\s+(?:is|contains|says|:)\s+(.+)', desc, re.IGNORECASE)
        if msg_match:
            return {"method": "assert_text_visible", "text": msg_match.group(1).strip().strip("'\"")}

        # Default: verify the whole thing after "verify that"
        rest = re.sub(r'^(?:verify|assert|confirm|ensure|check)\s+(?:that\s+)?', '', desc, flags=re.IGNORECASE).strip()
        return {"method": "assert_text_visible", "text": rest}

    # WAIT
    if first in ("wait", "pause"):
        sec_match = re.search(r'(\d+)\s*(?:seconds?|secs?|s)', desc, re.IGNORECASE)
        if sec_match:
            return {"method": "wait_for_timeout", "ms": int(sec_match.group(1)) * 1000}
        return {"method": "wait_for_timeout", "ms": 2000}

    # SELECT
    if first in ("select", "choose", "pick"):
        from_match = re.search(r'(.+?)\s+(?:from|in)\s+(?:the\s+)?(.+)', desc, re.IGNORECASE)
        if from_match:
            return {"method": "select_option", "locator": _locator_for(from_match.group(2)), "option": from_match.group(1)}
        return {"method": "select_option", "locator": _locator_for(" ".join(words[1:]).strip()), "option": ""}

    # NAVIGATE: go/navigate/open (if not already caught)
    if first in ("go", "navigate", "open", "browse"):
        if url_match:
            return {"method": "goto", "url": url_match.group(1)}
        # "Go back"
        if "back" in desc_lower:
            return {"method": "go_back"}
        return {"method": "reload"}

    # REFRESH/RELOAD
    if first in ("refresh", "reload"):
        return {"method": "reload"}

    # HOVER
    if first in ("hover", "mouseover"):
        target = " ".join(words[1:]).strip()
        target = re.sub(r'^(?:over|on|the|a|an)\s+', '', target, flags=re.IGNORECASE)
        return {"method": "hover", "locator": _locator_for(target) if target else {"strategy": "text", "value": ""}}

    # SCROLL
    if first in ("scroll", "swipe"):
        target_match = re.search(r'(?:to|down|up|into)\s+(.+?)$', desc, re.IGNORECASE)
        if target_match:
            return {"method": "scroll_into_view", "locator": _locator_for(target_match.group(1))}
        return {"method": "scroll_into_view", "locator": {"strategy": "text", "value": "body"}}

    # If starts with a URL, navigate
    if desc_lower.startswith("http://") or desc_lower.startswith("https://"):
        return {"method": "goto", "url": desc.split()[0]}

    # Last resort: try to click whatever is mentioned
    # Extract likely target (last noun phrase)
    return {"method": "click", "locator": _locator_for(desc)}


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
            if not pw_action:
                pw_action = _heuristic_fallback(desc)
                logger.info(f"Heuristic-mapped step '{desc[:60]}...' → {pw_action['method']}")

            plan_steps.append({
                "order": order,
                "description": desc,
                "intent": _infer_intent(pw_action["method"]),
                "target": pw_action.get("locator", {}).get("value"),
                "value": pw_action.get("text") or pw_action.get("url"),
                "playwright_action": pw_action,
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
    "assert_text_visible": "VERIFY", "assert_text_not_visible": "VERIFY",
    "assert_url_contains": "VERIFY", "assert_url_equals": "VERIFY",
    "assert_title_contains": "VERIFY", "assert_title_equals": "VERIFY",
    "assert_element_visible": "VERIFY",
    "hover": "HOVER", "scroll_into_view": "SCROLL",
}


def _infer_intent(method: str) -> str:
    return _INTENT_MAP.get(method, "UNKNOWN")
