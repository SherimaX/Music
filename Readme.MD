# Piano Sheet Processing Roadmap

This project converts scanned classical piano sheet music into a machine-readable format.  
The short-term goal is a backend-only pipeline that produces two artifacts:

1. **A MusicXML representation of the score.**  
2. **A PDF rendering generated from that MusicXML.**

Once this minimal pipeline works, we can extend it into a full Flask web application with an interactive music-sheet viewer.

---

## 1. Environment setup

- Python 3.8 +
- [`music21`](https://web.mit.edu/music21/)
- [`Audiveris`](https://audiveris.github.io/audiveris/) for optical music recognition
- (Later) `Flask` for a simple web API

Create a virtual environment and install **music21**:

```bash
python -m venv venv
source venv/bin/activate        # or .\venv\Scripts\activate on Windows
pip install music21
````

Audiveris is a standalone Java application; install it separately and make sure the `audiveris` command is on your `PATH`.

---

## 2. Convert image to MusicXML

1. Place a scanned image or PDF of a piano-solo piece in a working directory.
2. Run Audiveris on the file to produce a `.xml` MusicXML file:

   ```bash
   audiveris -batch input.pdf -export
   ```

   This generates `input.xml` alongside the original image/PDF.

### 2.1 Python helper script

Instead of running Audiveris manually, you can call **`convert_sheet.py`** to automate the conversion **and** the PDF rendering:

```bash
python convert_sheet.py input.pdf -o output/
```

The script accepts a single image/PDF *or* a directory of files and places the generated MusicXML and PDF files in the chosen output directory.

## Troubleshooting

If you run the helper script (or Audiveris directly) and encounter a `FileNotFoundError` or a message saying that `audiveris` cannot be located, the tool is not on your `PATH`.
Verify the installation with:

```bash
audiveris --help
```

If this command fails, adjust your `PATH` so that the Audiveris executable can be found.

---

## 3. Generate PDF with music21

Use `music21` to parse the MusicXML and render a PDF:

```python
from music21 import converter

score = converter.parse("input.xml")
# Adjust or analyze the score here if desired
score.write("musicxml.pdf", fp="output.pdf")
```

This script loads the MusicXML, optionally lets you work with the score in Python, and then writes a PDF called **`output.pdf`**.

---

## 4. Output files

After these steps you will have:

| File         | Description                              |
| ------------ | ---------------------------------------- |
| `input.xml`  | MusicXML score produced by Audiveris     |
| `output.pdf` | Rendered sheet music produced by music21 |

---

## 5. Next steps

* Wrap the pipeline in a **Flask** application so users can upload images and receive the generated files.
* Display the score in the browser with **OpenSheetMusicDisplay** and sync playback via MIDI.
* Explore alignment with real audio recordings once the basic features are stable.
