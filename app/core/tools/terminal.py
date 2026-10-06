import subprocess

from langchain_core.tools import tool


@tool
def terminal(command: str) -> str:
    """Execute a terminal command and return its output."""

    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return f"Error:\n{result.stderr}"

    return result.stdout