import importlib.metadata
import subprocess
import sys
import textwrap

from rich.console import Console
from rich.panel import Panel
from rich.text import Text


def main() -> None:
    console = Console(highlight=False, stderr=True)
    max_width = max(console.width - 10, 16)
    pipe_data = None if sys.stdin.isatty() else sys.stdin.buffer.read()

    if pipe_data is None and len(sys.argv) == 1:
        Console(stderr=False).print(Panel.fit(
            '🔫 [bold cyan]pew[/] [dim]-[/] the [yellow][bold]p[/]rogram [bold]e[/]xecution [bold]w[/]rapper[/]',
            subtitle='version ' + importlib.metadata.version(__package__),
            border_style='dim',
        ))
        return

    command_string = Text.from_markup('[cyan]pew:[/] ')

    if len(sys.argv) > 1:
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
            command_string.truncate(max_width, overflow='ellipsis')
    else:
        command_string.append_text(Text.from_markup('[dim]<[italic]no command[/]>'))

    if pipe_data is not None:
        try:
            pipe_preview = textwrap.shorten(pipe_data.decode(), max_width)
        except UnicodeDecodeError:
            pipe_preview = '<[italic]binary[/]>'
        command_string.append_text(Text.from_markup(f'\n[magenta] in[/][cyan]:[/] [dim]{pipe_preview}[/dim]'))

    console.print(command_string)

    if len(sys.argv) > 1:
        if pipe_data is not None:
            completed_process = subprocess.run(sys.argv[1:], input=pipe_data)
        else:
            completed_process = subprocess.run(sys.argv[1:])

        exit(completed_process.returncode)
