#!/usr/bin/env python3
"""Convert a scanned piano sheet into MusicXML, PDF, MIDI, and MP3.

This script uses Audiveris to perform optical music recognition on a single-page
image or PDF and then uses music21 to generate PDF and MIDI renderings of the
resulting MusicXML file. The MIDI is further converted to MP3 using ``timidity``
and ``ffmpeg``.

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
    except subprocess.CalledProcessError as exc:
        err = exc.stderr.decode().strip() if isinstance(exc.stderr, bytes) else str(exc.stderr)
        print(f"Audiveris failed to process {input_file}:", file=sys.stderr)
        if err:
            print(err, file=sys.stderr)
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


def render_midi(xml_file: Path, output_file: Path) -> None:
    """Render ``xml_file`` to ``output_file`` as a MIDI file using music21."""
    score = converter.parse(str(xml_file))
    score.write("midi", fp=str(output_file))


def midi_to_mp3(midi_file: Path, mp3_file: Path) -> None:
    """Convert ``midi_file`` to ``mp3_file`` using timidity and ffmpeg."""
    wav_file = midi_file.with_suffix(".wav")

    if not shutil.which("timidity"):
        print(
            "timidity executable not found. Please install timidity and ensure it is on your PATH.",
            file=sys.stderr,
        )
        sys.exit(1)
    if not shutil.which("ffmpeg"):
        print(
            "ffmpeg executable not found. Please install ffmpeg and ensure it is on your PATH.",
            file=sys.stderr,
        )
        sys.exit(1)

    subprocess.run(["timidity", str(midi_file), "-Ow", "-o", str(wav_file)], check=True)
    subprocess.run(["ffmpeg", "-y", "-i", str(wav_file), str(mp3_file)], check=True)
    wav_file.unlink(missing_ok=True)


def process_files(files: Iterable[Path], output_dir: Path, review: bool = False) -> None:
    for f in files:
        xml_file = run_audiveris(f, output_dir)
        pdf_file = output_dir / f"{xml_file.stem}.pdf"
        render_pdf(xml_file, pdf_file)
        midi_file = output_dir / f"{xml_file.stem}.mid"
        render_midi(xml_file, midi_file)
        mp3_file = output_dir / f"{xml_file.stem}.mp3"
        midi_to_mp3(midi_file, mp3_file)
        print(f"Generated {xml_file}")
        print(f"Generated {pdf_file}")
        print(f"Generated {midi_file}")
        print(f"Generated {mp3_file}")
        if review:
            try:
                score = converter.parse(str(xml_file))
                score.show()
            except Exception:
                mscore_bin = shutil.which("mscore") or shutil.which("musescore")
                if mscore_bin:
                    subprocess.run([mscore_bin, str(pdf_file)], check=False)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert sheet images to MusicXML, PDF, MIDI, and MP3"
    )
    parser.add_argument("input_path", type=Path, help="Image/PDF file or directory of files")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory for generated files",
    )
    parser.add_argument(
        "--review",
        action="store_true",
        help="Open each generated score for manual review",
    )
    args = parser.parse_args()

    if args.input_path.is_dir():
        files = [f for f in args.input_path.iterdir() if f.suffix.lower() in SUPPORTED_EXTS]
    else:
        files = [args.input_path]

    process_files(files, args.output_dir, review=args.review)


if __name__ == "__main__":
    main()
