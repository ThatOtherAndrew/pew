from __future__ import annotations

import os
import shutil
import stat
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

import httpx
import rich
from rich.progress import Progress
from rich.prompt import Confirm, PromptBase, InvalidResponse


class Module(ABC):
    def log(self, message: str):
        rich.print(f'[dim cyan]pew:[/] [dim magenta]{self.__class__.__name__}:[/] {message}')

    @abstractmethod
    def hook(self, command: list[str]) -> list[str] | None:
        """Hook into a command and pre-process or modify it before execution or processing.

        :param command: The input command and parameters to process.
        :return: The modified command, or None to leave the command unmodified.
        :raises SystemExit: Terminate early without any further processing or execution of the command.
        """
        pass


class SameDirExecutable(Module):
    def hook(self, command: list[str]) -> list[str] | None:
        location = Path(command[0])
        if location.absolute().parent == Path.cwd() and location.is_file() and os.access(location, os.X_OK):
            self.log('Matching executable name found in current directory')
            return ['./' + command[0], *command[1:]]


class Nix(Module):
    class PathPrompt(PromptBase[Path]):
        response_type = Path
        validate_error_message = '[prompt.invalid]Please enter a valid installation path'

        def process_response(self, value: str) -> Path:
            if not value:
                value = '/usr/bin'
            path = Path(value).expanduser().resolve()

            closest_dir = path
            while not closest_dir.is_dir():
                closest_dir = closest_dir.parent

            if not os.access(closest_dir, os.W_OK):
                raise InvalidResponse(f'[prompt.invalid]No write permissions for [yellow]{closest_dir}')

            if path == closest_dir:
                confirmation_message = f'Install to directory [yellow]{path.as_posix()}/[/]?'
            else:
                confirmation_message = (f'Create directory [yellow]{closest_dir.as_posix()}/[/]'
                                        f'[green]{path.relative_to(closest_dir).as_posix()}/[/] and install?')
            if not Confirm.ask(confirmation_message, default=True):
                raise InvalidResponse('[prompt.invalid]Installation directory selection cancelled')

            return path

    def _install_nix(self) -> None:
        self.log('Installing nix-portable...')

        installation_path = self.PathPrompt.ask('nix-portable installation path [prompt.default](/usr/bin)')
        installation_path.mkdir(parents=True, exist_ok=True)
        bin_path = installation_path / 'nix-portable'
        architecture = os.uname().machine

        with Progress() as progress:
            with httpx.stream(
                method='GET',
                url=f'https://github.com/DavHau/nix-portable/releases/latest/download/nix-portable-{architecture}',
                follow_redirects=True,
            ) as response:
                task = progress.add_task(
                    '[cyan]Downloading nix-portable...',
                    total=int(response.headers['Content-Length']),
                )
                with bin_path.open('wb') as file:
                    for chunk in response.iter_bytes():
                        file.write(chunk)
                        progress.update(task, advance=len(chunk))
            (installation_path / 'nix').symlink_to(bin_path)
            bin_path.chmod(bin_path.stat().st_mode | stat.S_IEXEC)

        self.log(f'[green]Successfully installed nix-portable to [yellow]{bin_path}')

    def hook(self, command: list[str]) -> list[str] | None:
        if shutil.which('nix') is None:
            if command[0] == 'nix':
                self.log('nix not found')
                if Confirm.ask('Attempt automatic nix-portable installation?', default=True):
                    self._install_nix()
            else:
                self.log('nix not found - run [yellow][dim]pew[/] nix[/] to install')
                return command

        if command[0] == 'nix':
            return command

        result = subprocess.run(['nix', 'search', 'nixpkgs#' + command[0], '^'], capture_output=True)
        if result.returncode:
            return command

        self.log('[green]Command match found in nixpkgs!')
        if Confirm.ask(f'Run [yellow][dim]nixpkgs#[/]{command[0]}[/]?', default=True):
            new_command = ['nix', 'run', 'nixpkgs#' + command[0]]
            if len(command) > 1:
                new_command.extend(['--', *command[1:]])
            return new_command

        return command


def get_modules() -> tuple[Module, ...]:
    return SameDirExecutable(), Nix()
