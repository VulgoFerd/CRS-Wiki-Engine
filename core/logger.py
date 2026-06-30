from rich.console import Console

console = Console()


def info(message):

    console.print(f"[green][INFO][/green] {message}")


def warning(message):

    console.print(f"[yellow][WARN][/yellow] {message}")


def error(message):

    console.print(f"[red][ERROR][/red] {message}")