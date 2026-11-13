"""Explicit local device boundary; no physical network transport."""
from dataclasses import dataclass
from typing import Protocol
from .physics import Decoy


class Device(Protocol):
    config: Decoy
    isolated: bool

    def configure(self, config: Decoy) -> None: ...
    def isolate(self) -> None: ...


@dataclass
class SimulatedDevice:
    config: Decoy = Decoy()
    isolated: bool = False

    def configure(self, config: Decoy) -> None:
        if self.isolated:
            raise RuntimeError('Isolated device requires explicit operator recovery')
        if not isinstance(config, Decoy):
            raise TypeError('Expected validated Decoy configuration')
        self.config = config

    def isolate(self) -> None:
        self.isolated = True

    def apply(self, config: Decoy, isolated: bool) -> None:
        if isolated:
            self.isolate()
        elif self.isolated:
            raise RuntimeError('Automatic isolation release is prohibited')
        elif config != self.config:
            self.configure(config)
