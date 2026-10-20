"""Arithmetic CAPTCHA built on the distorted image renderer."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from ..exceptions import ConfigurationError
from ..registry import register
from .image import ImageCaptcha

_ALLOWED_OPERATIONS = {"+", "-", "*"}


@register
class MathCaptcha(ImageCaptcha):
    """Static arithmetic expression whose numeric answer is returned."""

    name = "math"
    description = "A distorted arithmetic expression with the computed answer."
    default_size = (500, 180)
    default_format = "png"

    option_defaults = {
        **ImageCaptcha.option_defaults,
        "operations": ("+", "-", "*"),
        "min_operand": 1,
        "max_operand": 20,
        "operands": 2,
        "allow_negative": False,
    }
    option_docs = {
        **ImageCaptcha.option_docs,
        "operations": "Operations to sample from: '+', '-', and/or '*'.",
        "min_operand": "Minimum operand value (inclusive).",
        "max_operand": "Maximum operand value (inclusive).",
        "operands": "Number of operands in the expression (2-5).",
        "allow_negative": "Allow intermediate or final negative results.",
    }

    def _validate_options(self) -> None:
        super()._validate_options()
        opts = self.options
        operations = opts["operations"]
        operations = list(operations) if isinstance(operations, str) else list(operations)
        operations = [str(operation) for operation in operations]
        if not operations:
            raise ConfigurationError("operations must contain at least one operator")
        invalid = set(operations) - _ALLOWED_OPERATIONS
        if invalid:
            raise ConfigurationError(
                f"Unsupported operation(s): {', '.join(sorted(invalid))}. "
                f"Allowed: {', '.join(sorted(_ALLOWED_OPERATIONS))}"
            )
        self._operations = operations
        if not 2 <= int(opts["operands"]) <= 5:
            raise ConfigurationError("operands must be between 2 and 5")
        if int(opts["min_operand"]) < 0:
            raise ConfigurationError("min_operand must be non-negative")
        if int(opts["max_operand"]) < int(opts["min_operand"]):
            raise ConfigurationError("max_operand must be greater than or equal to min_operand")

    def _make_problem(self) -> Tuple[str, Any, Dict[str, Any]]:
        if self.config.text is not None:
            return self.config.text, None, {"custom_expression": True}

        minimum = int(self.options["min_operand"])
        maximum = int(self.options["max_operand"])
        count = int(self.options["operands"])
        allow_negative = bool(self.options["allow_negative"])

        numbers: List[int] = []
        chosen_ops: List[str] = []
        value = 0
        for _ in range(80):
            numbers = [self.rng.randint(minimum, maximum) for _ in range(count)]
            chosen_ops = [self.rng.choice(self._operations) for _ in range(count - 1)]
            value = numbers[0]
            valid = True
            for operator, number in zip(chosen_ops, numbers[1:]):
                if operator == "+":
                    value += number
                elif operator == "-":
                    if value - number < 0 and not allow_negative:
                        valid = False
                        break
                    value -= number
                else:
                    value *= number
            if valid:
                break
        else:
            # A subtraction-only configuration can be unlucky. Build a valid
            # left-to-right expression while keeping every intermediate value
            # non-negative.
            numbers = sorted(numbers, reverse=True)
            chosen_ops = []
            value = numbers[0]
            for number in numbers[1:]:
                if value - number >= 0:
                    chosen_ops.append("-")
                    value -= number
                else:
                    chosen_ops.append("+")
                    value += number

        expression = str(numbers[0])
        for operator, number in zip(chosen_ops, numbers[1:]):
            expression += f" {operator} {number}"
        expression += " = ?"
        return (
            expression,
            str(value),
            {
                "operands": numbers,
                "operations": chosen_ops,
                "expected_value": value,
            },
        )


__all__ = ["MathCaptcha"]
