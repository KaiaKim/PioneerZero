"""
Parse raw chat input: distinguish normal chat vs slash command and tokenize.
"""
from typing import List, Tuple


def parse_input(text: str) -> Tuple[str, List[str] | None]:
    """
    Parse raw input. No leading '/' = chat; leading '/' = command.

    Returns:
        ("chat", None) for normal chat message.
        (command_name, args) for slash command. command_name is lowercased; args are remaining tokens.
    """
    if not text.startswith("/"):
        return "chat", None

    tokens = text[1:].strip().split()
    if not tokens:
        return "", []

    command = tokens[0]
    args = tokens[1:]
    # Keep command as-is for Korean/alias matching (no .lower() for 한글)
    return command, args
