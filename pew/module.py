from __future__ import annotations

import os
import shutil
import stat
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from textwrap import dedent

import httpx
import rich
from pygments.lexer import default
from rich.progress import Progress
from rich.prompt import Confirm, PromptBase, PromptType, InvalidResponse


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
        self.log('Installing Nix...')

        installation_path = self.PathPrompt.ask('Nix installation path [prompt.default](/usr/bin)')
        installation_path.mkdir(parents=True, exist_ok=True)
        bin_path = installation_path / 'nix'

        with Progress() as progress:
            with httpx.stream(
                method='GET',
                url='https://hydra.nixos.org/job/nix/maintenance-2.18/buildStatic.x86_64-linux/latest/download-by-type/file/binary-dist',
                follow_redirects=True,
            ) as response:
                task = progress.add_task('[cyan]Downloading nix v2.18...', total=None)
                with bin_path.open('wb') as file:
                    for chunk in response.iter_bytes():
                        file.write(chunk)
                        progress.update(task, advance=len(chunk))
            bin_path.chmod(bin_path.stat().st_mode | stat.S_IEXEC)

        if not (Path.home() / '.config/nix/nix.conf').is_file():
            self.log('Creating new nix.conf file')
            nix_conf_dir = Path.home() / '.config/nix'
            nix_conf_dir.mkdir(parents=True, exist_ok=True)
            with (nix_conf_dir / 'nix.conf').open('w') as file:
                file.write(dedent('''
                    extra-experimental-features = nix-command flakes
                    ssl-cert-file = /etc/pki/tls/cert.pem
                    sandbox = false
                ''').lstrip())

        self.log(f'[green]Successfully installed nix to [yellow]{bin_path}')

    def hook(self, command: list[str]) -> list[str] | None:
        if shutil.which('nix') is None:
            self.log('nix not found')
            if command[0] == 'nix':
                if Confirm.ask('Attempt automatic Nix installation?', default=True):
                    self._install_nix()
            else:
                self.log('Run [yellow][dim]pew[/] nix[/] to install')
                return command

        if command[0] == 'nix':
            return command

        result = subprocess.run(['nix', 'search', '--json', 'nixpkgs#' + command[0]], capture_output=True)
        if result.returncode:
            self.log(result.stderr.decode())

        self.log('[green]Command match found in nixpkgs!')
        if Confirm.ask(f'Run [yellow][dim]nixpkgs#[/]{command[0]}[/]?', default=True):
            return ['nix', 'run', 'nixpkgs#' + command[0], '--', *command[1:]]

        return command


def get_modules() -> tuple[Module, ...]:
    return SameDirExecutable(), Nix()
