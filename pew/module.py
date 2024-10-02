from __future__ import annotations

from abc import ABC, abstractmethod

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


class TestModule(Module):
    def hook(self, command: list[str]) -> list[str] | None:
        if command[0] == 'test':
            self.log('Yippee!')
        return


def get_modules() -> tuple[Module, ...]:
    return TestModule(),
