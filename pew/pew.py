import importlib.metadata
import os
import sys

from rich.console import Console
from rich.panel import Panel
from rich.text import Text


def main() -> None:
    console = Console(highlight=False, stderr=True)
    pipe_data = None if sys.stdin.isatty() else sys.stdin.buffer.read()

    if len(sys.argv) == 1:
        Console(stderr=False).print(Panel.fit(
            '🔫 [bold cyan]pew[/] [dim]-[/] the [yellow][bold]p[/]rogram [bold]e[/]xecution [bold]w[/]rapper[/]',
            subtitle='version ' + importlib.metadata.version(__package__),
            border_style='dim',
        ))
        return

    command_string = Text.from_markup('[cyan]pew:[/] ')

    command_string.append(sys.argv[1], style='yellow')
    for argument in sys.argv[2:]:
        style = None
        if argument.startswith('-'):
            style = 'dim'
        elif argument.isdigit():
            style = 'orange'
        elif any(ws in argument for ws in ' \r\n\t'):
            style = 'green underline'
        command_string.append(' ' + argument, style=style)

    command_string.truncate(max(console.width - 10, 16), overflow='ellipsis')
    console.print(command_string)

    os.execvp(sys.argv[1], sys.argv[1:])
