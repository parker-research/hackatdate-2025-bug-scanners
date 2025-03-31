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


def clean_verilog_comments(verilog: str) -> str:
    # Remove comments to avoid false positives.
    verilog = re.sub(r"//.*?$", "", verilog, flags=re.MULTILINE)
    verilog = re.sub(r"/\*.*?\*/", "", verilog, flags=re.DOTALL)
    return verilog


def extract_declared_identifiers(
    verilog: str,
) -> dict[
    Literal[
        "logic", "wire", "input reg", "input wire", "output reg", "output wire", "reg"
    ],
    list[str],
]:
    """Extract declared identifiers from a Verilog snippet."""
    verilog = clean_verilog_comments(verilog)

    output: dict[Literal["logic", "wire", "input", "output", "reg"], list[str]] = {}

    # Regex to match declarations
    pattern = re.compile(
        r"(?P<type>input reg|input wire|output reg|output wire|wire|logic|reg)\s*"
        # r'(?:\w+\s*)?'                        # optional 'wire' or 'reg' modifier
        r"(?:\[[^\]]+\]\s*)?"  # optional bit-width like [7:0]
        r"(?P<vars>[^;]+);",  # variables until the semicolon
        flags=re.MULTILINE,
    )

    for match in pattern.finditer(verilog):
        var_type = match.group("type")
        var_list = match.group("vars")

        # Clean up and split by commas
        identifiers = [
            v.strip()
            .split("[")[0]
            .strip()  # remove any array declarations like [0:255]
            for v in var_list.split(",")
        ]
        if var_type not in output:
            output[var_type] = []
        output[var_type].extend(identifiers)

    return output


def count_constant_assignments_to_identifier(verilog: str, identifier: str) -> int:
    """Count constant assignments to a specific identifier in a Verilog snippet."""
    verilog = clean_verilog_comments(verilog)

    # Regex pattern to match `assign <identifier> = <constant>;`
    pattern = re.compile(
        rf"\bassign\s+{re.escape(identifier)}\s*=\s*([^\s;]+)", re.IGNORECASE
    )

    count = 0
    for match in pattern.findall(verilog):
        value = match.strip()
        # Match binary, hex, decimal, or boolean constants
        if (
            re.match(r"^[0-9]+'[bdhoBDHO][0-9a-fA-FxXzZ]+$", value)
            or re.match(r"^[01]b[01xzXZ]+$", value)
            or re.match(r"^[01]$", value)
        ):
            count += 1

    return count
