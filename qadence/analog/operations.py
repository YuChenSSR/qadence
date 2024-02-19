from __future__ import annotations

from sympy import cos, sin, sqrt

from qadence.blocks import add
from qadence.operations import HamEvo, N, X, Y
from qadence.parameters import Parameter, ParamMap
from qadence.qubit_support import QubitSupport
from qadence.register import Register
from qadence.types import PI, OpName, TParameter

from .hamiltonian_terms import rydberg_interaction_hamiltonian, rydberg_pattern_hamiltonian

ANALOGDRIVE = "AnalogDrive"  # Temporary, can be added to OpName later


class AnalogInteraction(HamEvo):
    """Evolution of the Rydberg interaction Hamiltonian."""

    name = OpName.ANALOGINTERACTION

    def __init__(
        self,
        register: Register,
        duration: TParameter,
        add_pattern: bool = True,
    ):
        self.add_pattern = add_pattern
        self.duration = Parameter(duration)

        generator = rydberg_interaction_hamiltonian(register)

        generator_pattern = rydberg_pattern_hamiltonian(register)

        if add_pattern and generator_pattern is not None:
            generator = generator + generator_pattern

        super().__init__(generator, parameter=self.duration / 1000)

        self.parameters = ParamMap(parameter=self.duration / 1000, duration=self.duration)


class AnalogDrive(HamEvo):
    """Evolution of the Rydberg drive Hamiltonian with background interaction."""

    name = ANALOGDRIVE  # type: ignore [assignment]

    def __init__(
        self,
        register: Register,
        duration: TParameter,
        omega: TParameter,
        delta: TParameter,
        phase: TParameter = 0,
        qubit_support: QubitSupport | tuple | None = None,
        add_pattern: bool = True,
    ):
        self.add_pattern = add_pattern
        self.duration = Parameter(duration)

        if omega == 0 and delta == 0:
            raise ValueError("Parameters omega and delta cannot both be 0.")

        if qubit_support is None:
            qubit_support = tuple(register.nodes)

        omega, delta, phase = Parameter(omega), Parameter(delta), Parameter(phase)

        x_terms = (omega / 2) * add(cos(phase) * X(i) for i in qubit_support)
        y_terms = (omega / 2) * add(sin(phase) * Y(i) for i in qubit_support)
        n_terms = delta * add(N(i) for i in qubit_support)

        generator_interaction = rydberg_interaction_hamiltonian(register)

        generator = x_terms - y_terms - n_terms + generator_interaction

        generator_pattern = rydberg_pattern_hamiltonian(register)

        if add_pattern and generator_pattern is not None:
            generator = generator + generator_pattern

        super().__init__(generator, self.duration / 1000)

        h_norm = sqrt(omega**2 + delta**2)
        alpha = self.duration * h_norm / 1000
        self.parameters = ParamMap(
            parameter=self.duration / 1000,  # Placeholder
            duration=self.duration,
            alpha=alpha,
            omega=omega,
            delta=delta,
            phase=phase,
            h_norm=h_norm,
        )


class AnalogRX(AnalogDrive):
    """Analog X rotation."""

    name = OpName.ANALOGRX

    def __init__(
        self,
        register: Register,
        angle: TParameter,
        qubit_support: QubitSupport | tuple | None = None,
        add_pattern: bool = True,
    ):
        self.alpha = Parameter(angle)
        omega, delta, phase = PI, 0, 0

        super().__init__(
            register, self.alpha / omega * 1000, omega, delta, phase, qubit_support, add_pattern
        )


class AnalogRY(AnalogDrive):
    """Analog Y rotation."""

    name = OpName.ANALOGRY

    def __init__(
        self,
        register: Register,
        angle: TParameter,
        qubit_support: QubitSupport | tuple | None = None,
        add_pattern: bool = True,
    ):
        self.alpha = Parameter(angle)
        omega, delta, phase = PI, 0, -PI / 2

        super().__init__(
            register, self.alpha / omega * 1000, omega, delta, phase, qubit_support, add_pattern
        )


class AnalogRZ(AnalogDrive):
    """Analog Z rotation."""

    name = OpName.ANALOGRZ

    def __init__(
        self,
        register: Register,
        angle: TParameter,
        qubit_support: QubitSupport | tuple | None = None,
        add_pattern: bool = True,
    ):
        self.alpha = Parameter(angle)
        omega, delta, phase = 0, PI, 0

        super().__init__(
            register, self.alpha / delta * 1000, omega, delta, phase, qubit_support, add_pattern
        )