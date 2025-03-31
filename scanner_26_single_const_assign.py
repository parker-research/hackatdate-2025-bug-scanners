"""If a wire/reg/logic/output exists, in a Verilog design, it's rare that it will be assigned a single constant value.

We will flag any such cases.
"""

import pyslang
import argparse
from typing import Literal
from collections.abc import Iterator
import re
import json

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


VERILOG_TYPE_LITERAL_t = Literal[
    "logic", "wire", "input reg", "input wire", "output reg", "output wire", "reg"
]


def extract_declared_identifiers(
    verilog: str,
) -> dict[
    VERILOG_TYPE_LITERAL_t,
    list[str],
]:
    """Extract declared identifiers from a Verilog snippet."""
    verilog = clean_verilog_comments(verilog)

    output: dict[VERILOG_TYPE_LITERAL_t, list[str]] = {}

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

        assert isinstance(var_type, str)
        assert var_type in (
            "logic",
            "wire",
            "input reg",
            "input wire",
            "output reg",
            "output wire",
            "reg",
        )

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


def find_all_single_constant_assignments_in_verilog(
    verilog: str,
) -> list[tuple[str, str]]:
    """Find all identifiers with single constant assignments."""
    verilog = clean_verilog_comments(verilog)
    identifiers = extract_declared_identifiers(verilog)

    # Tuple of (identifier name, identifier type)
    results: list[tuple[str, str]] = []

    for var_type, var_list in identifiers.items():
        for identifier in var_list:
            count = count_constant_assignments_to_identifier(verilog, identifier)
            if count == 1:
                results.append((identifier, var_type))

    return results


def find_all_single_constant_assignments_in_project(
    project_folder_path: Path,
) -> Iterator[tuple[str, str, str]]:
    """Find all identifiers with single constant assignments in a project folder.

    Returns a list of tuples containing the identifier name, type, and relative file path.
    """

    for file_path in list(project_folder_path.rglob("*.v")) + list(
        project_folder_path.rglob("*.sv")
    ):
        verilog = file_path.read_text()
        single_constant_assignments = find_all_single_constant_assignments_in_verilog(
            verilog
        )
        for identifier, var_type in single_constant_assignments:
            yield (
                identifier,
                var_type,
                file_path.relative_to(project_folder_path).as_posix(),
            )


def main():
    # Create an arg parser with one argument: project folder path.
    parser = argparse.ArgumentParser(
        description="Find single constant assignments in Verilog files."
    )
    parser.add_argument(
        "project_folder_path",
        type=str,
        help="Path to the project folder containing Verilog files.",
    )
    parser.add_argument(
        "-o",
        "--output-jsonl",
        type=str,
        help="Path to the output JSONL file.",
        dest="output_jsonl_path",
    )
    args = parser.parse_args()
    project_folder_path = Path(args.project_folder_path)
    if not project_folder_path.is_dir():
        raise ValueError(f"{project_folder_path} is not a valid directory.")
    if not project_folder_path.exists():
        raise ValueError(f"{project_folder_path} does not exist.")

    if args.output_jsonl_path:
        output_jsonl_path: Path | None = Path(args.output_jsonl_path)
    else:
        output_jsonl_path = None

    # Find all single constant assignments in the project folder.
    results: list[tuple[str, str, str]] = []
    for (
        identifier,
        var_type,
        file_path,
    ) in find_all_single_constant_assignments_in_project(project_folder_path):
        print(f"Identifier: {identifier}, Type: {var_type}, File: {file_path}")
        results.append((identifier, var_type, file_path))

        if output_jsonl_path:
            result_row = {
                "identifier": identifier,
                "type": var_type,
                "file": file_path,
            }
            with open(output_jsonl_path, "a") as jsonl_file:
                jsonl_file.write(json.dumps(result_row) + "\n")

    print(f"Found {len(results)} single constant assignments.")


if __name__ == "__main__":
    main()
