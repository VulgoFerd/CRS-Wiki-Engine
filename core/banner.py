from rich.console import Console
from rich.panel import Panel

from .version import NAME, VERSION

console = Console()


def show_banner():

    console.print()

    console.print(
        Panel.fit(
            f"[cyan]{NAME}[/]\n[white]Version {VERSION}[/]",
            border_style="bright_blue"
        )
    )

    console.print()