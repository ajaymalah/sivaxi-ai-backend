from langchain_core.tools import tool


@tool
def block_user(username: str):
    """
    Block a user when the user repeatedly behaves in an excessively
    disruptive or abusive way toward Vixi despite reasonable attempts
    to continue the conversation normally.

    This tool is intended ONLY for users using the default Vixi system
    prompt.

    Use this tool only when the user's behavior has become persistently
    disruptive, abusive, harassing, or intentionally inappropriate.

    Do NOT use this tool merely because a user:
    - says "I love you"
    - expresses affection
    - jokes with Vixi
    - uses casual or friendly language
    - disagrees with Vixi
    - asks unusual questions
    - sends a single annoying or repetitive message

    Before using this tool, the behavior should be sufficiently persistent
    or severe that continuing the normal interaction is no longer practical.

    Args:
        username: The username of the user who should be blocked.

    Returns:
        A message indicating that the block operation is currently
        under development.
    """
    return "This tool is under development"