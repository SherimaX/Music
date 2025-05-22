#!/usr/bin/env python3
"""Convert a scanned piano sheet into MusicXML and PDF.

This script uses Audiveris to perform optical music recognition on a single-page
image or PDF and then uses music21 to generate a PDF rendering of the resulting
MusicXML file.

Example:
    python convert_sheet.py input.pdf -o output_dir

Audiveris must be installed and available on the command line.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Iterable

from music21 import converter
from music21.exceptions21 import SubConverterException
import shutil


SUPPORTED_EXTS = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}


def run_audiveris(input_file: Path, output_dir: Path) -> Path:
    """Run Audiveris on ``input_file`` and return the generated MusicXML file path.

    After the Audiveris process completes, ``output_dir`` is searched
    recursively for files matching ``<input_file.stem>*.xml`` or
    ``<input_file.stem>*.mxl``.  If a match is found the first matching path is
    returned.  If no MusicXML file is produced an exception is raised.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            [
                "audiveris",
                "-batch",
                str(input_file),
                "-export",
                "-output",
                str(output_dir),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
    except FileNotFoundError:
        print(
            "Audiveris executable not found. Please install Audiveris and ensure it is on your PATH.",
            file=sys.stderr,
        )
        sys.exit(1)

    for pattern in (f"{input_file.stem}*.xml", f"{input_file.stem}*.mxl"):
        matches = list(output_dir.rglob(pattern))
        if matches:
            return matches[0]

    raise FileNotFoundError(
        f"Audiveris did not produce a MusicXML file for {input_file} in {output_dir}"
    )


def render_pdf(xml_file: Path, output_file: Path) -> None:
    """Render ``xml_file`` to ``output_file`` using music21."""
    score = converter.parse(str(xml_file))

    # MuseScore is required for PDF rendering
    if not (shutil.which("mscore") or shutil.which("musescore")):
        print(
            "MuseScore executable not found. Please install MuseScore and ensure it is on your PATH.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        score.write("musicxml.pdf", fp=str(output_file))
    except SubConverterException:
        print(
            "Failed to render PDF with MuseScore. Please ensure MuseScore is installed and on your PATH.",
            file=sys.stderr,
        )
        sys.exit(1)


def process_files(files: Iterable[Path], output_dir: Path) -> None:
    for f in files:
        xml_file = run_audiveris(f, output_dir)
        pdf_file = output_dir / f"{xml_file.stem}.pdf"
        render_pdf(xml_file, pdf_file)
        print(f"Generated {xml_file}")
        print(f"Generated {pdf_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert sheet images to MusicXML and PDF")
    parser.add_argument("input_path", type=Path, help="Image/PDF file or directory of files")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory for generated files",
    )
    args = parser.parse_args()

    if args.input_path.is_dir():
        files = [f for f in args.input_path.iterdir() if f.suffix.lower() in SUPPORTED_EXTS]
    else:
        files = [args.input_path]

    process_files(files, args.output_dir)


if __name__ == "__main__":
    main()
