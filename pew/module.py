from __future__ import annotations

import os
from abc import ABC, abstractmethod
from pathlib import Path

import rich


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
        if location.is_file() and os.access(location, os.X_OK):
            self.log('matching executable name found in current directory')
            return ['./' + location.resolve().relative_to(Path.cwd()).as_posix(), *command[1:]]


def get_modules() -> tuple[Module, ...]:
    return SameDirExecutable(),
