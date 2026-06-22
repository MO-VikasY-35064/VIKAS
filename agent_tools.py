"""
agent_tools.py
==============
Helper utilities used by the DataAutomationAgent.

Functions:
    detect_file_type       — Detect CSV vs Excel from file extension.
    parse_command          — Parse a raw CLI string into (action, args).
    validate_workflow_config — Validate a workflow JSON config dict.
    format_summary_table   — Pretty-print a summary dictionary as a table.
"""

import os
from typing import Any

try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False


# ------------------------------------------------------------------ #
#  File type detection                                                 #
# ------------------------------------------------------------------ #

def detect_file_type(filepath: str) -> str:
    """
    Detect whether a file is CSV or Excel based on its extension.

    Args:
        filepath: Path to the file.

    Returns:
        'csv', 'excel', or 'unknown'.
    """
    ext = os.path.splitext(filepath)[-1].lower()
    if ext == ".csv":
        return "csv"
    elif ext in (".xlsx", ".xls", ".xlsm"):
        return "excel"
    return "unknown"


# ------------------------------------------------------------------ #
#  Command parser                                                      #
# ------------------------------------------------------------------ #

def parse_command(user_input: str) -> tuple:
    """
    Parse a raw CLI input string into an action keyword and argument list.

    Handles quoted strings so paths with spaces remain intact.

    Args:
        user_input: Raw string from the user (e.g., 'load "my data.csv"').

    Returns:
        Tuple of (action: str, args: list[str]).
        Returns ('', []) for empty input.

    Examples:
        >>> parse_command('load data.csv')
        ('load', ['data.csv'])
        >>> parse_command('pivot Region,Product Sales --aggfunc sum')
        ('pivot', ['Region,Product', 'Sales', '--aggfunc', 'sum'])
    """
    user_input = user_input.strip()
    if not user_input:
        return ("", [])

    tokens = []
    current = []
    in_quote = False
    quote_char = None

    for char in user_input:
        if char in ('"', "'") and not in_quote:
            in_quote = True
            quote_char = char
        elif char == quote_char and in_quote:
            in_quote = False
            quote_char = None
        elif char == " " and not in_quote:
            if current:
                tokens.append("".join(current))
                current = []
        else:
            current.append(char)

    if current:
        tokens.append("".join(current))

    if not tokens:
        return ("", [])

    action = tokens[0].lower()
    args = tokens[1:]
    return (action, args)


# ------------------------------------------------------------------ #
#  Workflow config validator                                           #
# ------------------------------------------------------------------ #

VALID_ACTIONS = {"load", "clean", "summary", "pivot", "export"}

ACTION_REQUIRED_FIELDS = {
    "load": ["filepath"],
    "clean": [],
    "summary": [],
    "pivot": ["index", "values"],
    "export": ["output"],
}


def validate_workflow_config(config: dict) -> list:
    """
    Validate a workflow config dictionary against the expected schema.

    Args:
        config: Parsed JSON config dict.

    Returns:
        List of error strings. Empty list means the config is valid.
    """
    errors = []

    if not isinstance(config, dict):
        return ["Config must be a JSON object."]

    if "steps" not in config:
        errors.append("Config is missing required key: 'steps'.")
        return errors

    if not isinstance(config["steps"], list):
        errors.append("'steps' must be a list.")
        return errors

    if len(config["steps"]) == 0:
        errors.append("'steps' list is empty — nothing to execute.")

    for i, step in enumerate(config["steps"], 1):
        if not isinstance(step, dict):
            errors.append(f"Step {i}: must be a JSON object.")
            continue

        action = step.get("action", "").lower()
        if not action:
            errors.append(f"Step {i}: missing 'action' field.")
            continue

        if action not in VALID_ACTIONS:
            errors.append(f"Step {i}: unknown action '{action}'. Valid: {sorted(VALID_ACTIONS)}.")
            continue

        for field in ACTION_REQUIRED_FIELDS.get(action, []):
            if field not in step:
                errors.append(f"Step {i} (action='{action}'): missing required field '{field}'.")

    return errors


# ------------------------------------------------------------------ #
#  Summary table formatter                                            #
# ------------------------------------------------------------------ #

def format_summary_table(summary: Any) -> str:
    """
    Format a summary object (dict, DataFrame, or string) as a readable table.

    Args:
        summary: Output from DataProcessor.get_summary() — could be a dict,
                 a pandas DataFrame, or any object with a __str__ method.

    Returns:
        A formatted string suitable for printing to the terminal.
    """
    # Pandas DataFrame
    try:
        import pandas as pd
        if isinstance(summary, pd.DataFrame):
            if HAS_TABULATE:
                return tabulate(summary, headers="keys", tablefmt="rounded_outline", floatfmt=".2f")
            return summary.to_string()
    except ImportError:
        pass

    # Plain dict
    if isinstance(summary, dict):
        rows = [[k, v] for k, v in summary.items()]
        if HAS_TABULATE:
            return tabulate(rows, headers=["Metric", "Value"], tablefmt="rounded_outline")
        return "\n".join(f"  {k}: {v}" for k, v in summary.items())

    # Fallback — just stringify
    return str(summary)
