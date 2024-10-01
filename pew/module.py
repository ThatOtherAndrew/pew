from __future__ import annotations

from abc import ABC, abstractmethod

import rich


class Module(ABC):
    def log(self, message: str):
        rich.print(f'[dim cyan]pew:[/] [dim magenta]{self.__class__.__name__}:[/] {message}')

    @abstractmethod
    def match(self, command: list[str]) -> bool:
        pass

    @abstractmethod
    def hook(self, command: list[str]) -> list[str] | None:
        pass


class TestModule(Module):
    def match(self, command: list[str]) -> bool:
        return command[0] == 'test'

    def hook(self, command: list[str]) -> list[str] | None:
        self.log('Yippee!')
        return


def get_modules() -> tuple[Module, ...]:
    return TestModule(),
