from agents.pm_agent import handle_command


def execute_command(command: str) -> str:
    """
    Executes a natural language command.
    """
    return handle_command(command)
