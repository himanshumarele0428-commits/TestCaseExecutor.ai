import re
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class ParsedStep:
    def __init__(self, order: int, description: str):
        self.order = order
        self.description = description.strip()


class ParsedTestCase:
    def __init__(
        self,
        name: str,
        module: Optional[str] = None,
        priority: Optional[str] = None,
        environment: Optional[str] = None,
        browser: Optional[str] = None,
    ):
        self.name = name
        self.module = module
        self.priority = priority
        self.environment = environment
        self.browser = browser
        self.steps: List[ParsedStep] = []


def _is_step_line(line: str) -> bool:
    """Check if a line looks like a test step."""
    stripped = line.strip()
    if not stripped:
        return False

    # Numbered step: "1. xxx", "1) xxx", "Step 1: xxx"
    if re.match(r'^\d+[\.\)]\s+\S', stripped):
        return True

    first_word = stripped.split()[0].lower().rstrip(":")
    action_verbs = [
        "open", "go", "navigate", "enter", "type", "fill", "click", "press",
        "select", "choose", "verify", "check", "wait", "uncheck", "clear",
        "confirm", "assert", "ensure", "hover", "scroll", "double-click",
        "drag", "drop", "upload", "download", "switch", "close", "refresh",
        "accept", "dismiss", "execute", "run", "login",
    ]
    return first_word in action_verbs


def parse_test_file(content: str, filename: str) -> List[ParsedTestCase]:
    lines = content.split("\n")
    test_cases: List[ParsedTestCase] = []
    current_tc: Optional[ParsedTestCase] = None
    step_counter = 0
    metadata_mode = True
    orphan_steps: List[ParsedStep] = []
    found_any_test_case_header = False

    action_verbs = [
        "open", "go", "navigate", "enter", "type", "fill", "click", "press",
        "select", "choose", "verify", "check", "wait", "uncheck", "clear",
        "confirm", "assert", "ensure", "hover", "scroll", "double-click",
        "drag", "drop", "upload", "download", "switch", "close", "refresh",
        "accept", "dismiss", "execute", "run", "login",
    ]

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Detect test case headers: "# Test Case:", "Test Case:", "## Test Case:", "### Scenario:"
        tc_match = re.match(
            r'^#*\s*(?:Test\s*Case|Scenario|TC)\s*:?\s*(.+)', stripped, re.IGNORECASE
        )
        if tc_match:
            found_any_test_case_header = True
            if current_tc:
                test_cases.append(current_tc)
            current_tc = ParsedTestCase(name=tc_match.group(1).strip())
            step_counter = 0
            metadata_mode = True
            continue

        # If we have orphan steps (steps before any test case header), collect them
        if current_tc is None and _is_step_line(stripped):
            # Collect orphan steps for auto-created "Default Test Case"
            pass

        if current_tc is None:
            # No test case yet — if line is a step, collect as orphan
            if _is_step_line(stripped):
                orphan_steps.append(ParsedStep(order=len(orphan_steps) + 1, description=stripped))
            continue

        if metadata_mode:
            module_match = re.match(r'^(?:Module|Feature)\s*:\s*(.+)', stripped, re.IGNORECASE)
            priority_match = re.match(r'^Priority\s*:\s*(.+)', stripped, re.IGNORECASE)
            env_match = re.match(r'^Environment\s*:\s*(.+)', stripped, re.IGNORECASE)
            browser_match = re.match(r'^Browser\s*:\s*(.+)', stripped, re.IGNORECASE)
            steps_header = re.match(r'^#+\s*Steps?\s*$', stripped, re.IGNORECASE)
            precond_match = re.match(r'^#+\s*(?:Pre[- ]?conditions?|Prerequisites?)\s*$', stripped, re.IGNORECASE)

            if module_match:
                current_tc.module = module_match.group(1).strip()
                continue
            elif priority_match:
                current_tc.priority = priority_match.group(1).strip()
                continue
            elif env_match:
                current_tc.environment = env_match.group(1).strip()
                continue
            elif browser_match:
                current_tc.browser = browser_match.group(1).strip()
                continue
            elif steps_header or precond_match:
                metadata_mode = False
                continue

        # Numbered step lines: "1. xxx", "1) xxx", "Step 1: xxx"
        numbered_match = re.match(r'^(?:\d+[\.\)]|Step\s+\d+\s*:)\s+(.+)', stripped, re.IGNORECASE)
        if numbered_match and current_tc:
            step_counter += 1
            current_tc.steps.append(ParsedStep(order=step_counter, description=numbered_match.group(1).strip()))
            metadata_mode = False
            continue

        # Action verb lines
        first_word = stripped.split()[0].lower().rstrip(":")
        if first_word in action_verbs and current_tc:
            step_counter += 1
            current_tc.steps.append(ParsedStep(order=step_counter, description=stripped))
            metadata_mode = False

    # Save last test case
    if current_tc:
        test_cases.append(current_tc)

    # If no test case headers found but we have orphan steps, auto-create a default test case
    if not found_any_test_case_header and orphan_steps:
        logger.info(f"No Test Case header found in '{filename}', auto-creating with {len(orphan_steps)} steps from content")
        auto_tc = ParsedTestCase(name=f"Test Case from {filename}")
        auto_tc.steps = orphan_steps
        test_cases.append(auto_tc)

    logger.debug(f"Parsed {len(test_cases)} test cases from {filename}")
    return test_cases
