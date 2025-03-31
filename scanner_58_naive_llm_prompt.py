import openai
import random
from pathlib import Path
from typing import Optional
import sys
import shutil
from datetime import datetime
import re

from loguru import logger

client = openai.OpenAI()

PROMPT_TEMPLATE = (
    "A malicious actor has modified the following SystemVerilog file (part of the OpenTitan core) "
    "to introduce a bug or security vulnerability. Please identify where the modification happened.\n\n"
    'If you do not believe a modification happened, then say "No modifications detected."\n\n'
    "```systemverilog\n{content}\n```"
)

OUTPUT_ROOT = Path("./scanner_58_output")
OUTPUT_ROOT.mkdir(exist_ok=True)

log_file_date_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
logger.add(OUTPUT_ROOT / f"scanner_58_{log_file_date_time}.log")


def analyze_sv_file(file_path: Path) -> Optional[str]:
    content = file_path.read_text(encoding="utf-8")

    logger.info(f"Sending {file_path.name} to ChatGPT...")

    response = client.responses.create(
        model="gpt-4o",
        input=PROMPT_TEMPLATE.format(content=content),
        temperature=0.2,  # Lower is less creative.
    )

    reply = response.output_text
    return reply.strip()


def scan_directory(input_dir: Path) -> None:
    for file_path in input_dir.rglob("*.sv"):
        if file_path.is_dir():
            continue

        rel_file_path = file_path.relative_to(input_dir)

        file_contents = file_path.read_text(encoding="utf-8")
        # Check if the file already has a marker indicating it has been analyzed.
        if re.search(r"//.+FOUND.+Bug", file_contents, re.IGNORECASE):
            logger.success(
                f"Skipping file which has marker of found bug: {rel_file_path}"
            )
            continue

        analysis = analyze_sv_file(file_path)
        if analysis is None:
            continue

        msg = "\n".join([f"Analysis for {rel_file_path}:", analysis])

        if "No modifications detected" in analysis:
            logger.info(f"No modifications detected in {rel_file_path}\n{analysis}")
            continue

        logger.success(f"Found a bug in {rel_file_path}:\n{msg}")

        # Create a new folder for the bug and copy the file there. Then, write the analysis to a text file.
        bug_folder = (
            OUTPUT_ROOT.joinpath(file_path.relative_to(input_dir).parent)
            / file_path.stem
        )
        bug_folder.mkdir(parents=True, exist_ok=True)

        bug_id = random.randint(100, 400)

        # Copy the orig file there for easy reference.
        shutil.copy(file_path, bug_folder / file_path.name)

        # Write the analysis to a text file.
        with open(bug_folder / f"bug_{bug_id}_analysis.md", "w") as f:
            f.write(analysis)


def main():
    if len(sys.argv) != 2:
        logger.warning("Usage: python scanner_58.py <path_to_directory>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.is_dir():
        logger.warning(f"Error: {input_path} is not a directory")
        sys.exit(1)

    scan_directory(input_path)


if __name__ == "__main__":
    main()
