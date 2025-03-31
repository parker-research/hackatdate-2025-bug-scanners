import pyslang
import argparse
from typing import Literal
import re

from pathlib import Path


def load_input_file(file_or_string: str | Path) -> pyslang.SyntaxTree:
    """Load a file or string into a SyntaxTree object."""
    if isinstance(file_or_string, Path):
        with open(file_or_string, "r") as file:
            data = file.read()
    elif isinstance(file_or_string, str):
        data = file_or_string
    else:
        raise TypeError("Input must be a string or Path object.")

    return pyslang.SyntaxTree.fromText(data)


def extract_declared_identifiers(
    verilog: str,
) -> dict[Literal["logic", "wire", "input reg", "input wire", "output reg", "output wire", "reg"], list[str]]:
    """Extract declared identifiers from a Verilog snippet."""

    output: dict[Literal["logic", "wire", "input", "output", "reg"], list[str]] = {}

    # Regex to match declarations
    pattern = re.compile(
        r'(?P<type>input reg|input wire|output reg|output wire|wire|logic|reg)\s*'
        # r'(?:\w+\s*)?'                        # optional 'wire' or 'reg' modifier
        r'(?:\[[^\]]+\]\s*)?'                # optional bit-width like [7:0]
        r'(?P<vars>[^;]+);',                 # variables until the semicolon
        flags=re.MULTILINE
    )

    for match in pattern.finditer(verilog):
        var_type = match.group("type")
        var_list = match.group("vars")

        # Clean up and split by commas
        identifiers = [
            v.strip().split("[")[0].strip()  # remove any array declarations like [0:255]
            for v in var_list.split(",")
        ]
        if var_type not in output:
            output[var_type] = []
        output[var_type].extend(identifiers)

    return output
