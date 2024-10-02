from __future__ import annotations

import importlib.metadata
import os
import sys

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .module import get_modules


def render_command(command: list[str]) -> Text:
    command_string = Text.from_markup('[dim cyan]pew:[/] ')

    command_string.append(command[0], style='bold yellow')
    for argument in command[1:]:
        style = None
        if argument.startswith('-'):
            style = 'dim'
        elif argument.isdigit():
            style = 'orange'
        elif any(ws in argument for ws in ' \r\n\t'):
            style = 'green underline'
        command_string.append(' ' + argument, style=style)

    return command_string


def main() -> None:
    console = Console(highlight=False, stderr=True)
    command = sys.argv[1:]

    if len(sys.argv) == 1:
        Console(stderr=False).print(Panel.fit(
            '🔫 [bold cyan]pew[/] [dim]-[/] the [yellow][bold]p[/]rogram [bold]e[/]xecution [bold]w[/]rapper[/]',
            subtitle='version ' + importlib.metadata.version(__package__),
            border_style='dim',
        ))
        return

    rendered_cmd = render_command(command)
    rendered_cmd.truncate(max(console.width - 10, 16), overflow='ellipsis')
    console.print(rendered_cmd)

    for module in get_modules():
        try:
            new_command = module.hook(command)
        except SystemExit as exit_exc:
            console.print('[dim cyan]pew:[/] [red]end processing[/]')
            raise exit_exc

        if new_command is not None:
            command = new_command
            rendered_cmd = render_command(command)
            rendered_cmd.truncate(max(console.width - 10, 16), overflow='ellipsis')
            console.print(rendered_cmd)

    try:
        os.execvp(command[0], command)
    except FileNotFoundError:
        console.print('[dim cyan]pew:[/] [bold red]command not found[/]')
        sys.exit(127)
