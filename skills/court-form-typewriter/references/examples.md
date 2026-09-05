# Court form typewriter — field map examples

## Pro Se Entry (Dakota) @ 300 DPI on tulsa_FormsProSeEntryofAppeance.pdf

```json
{
  "font_size": 48,
  "raise_px": 6,
  "font_path": "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
  "fields": [
    {"name": "plaintiff", "text": "DAKOTA FRAZIER", "x": 750, "line_y": 524},
    {"name": "defendant", "text": "JACOB ALLAN FRAZIER", "x": 830, "line_y": 811},
    {"name": "case_number", "text": "FD-____________", "x": 1575, "line_y": 607},
    {"name": "full_name", "text": "Dakota Frazier", "x": 665, "line_y": 1510},
    {"name": "address", "text": "11208 E Archer Pl, Apt 137, Tulsa, OK 74116", "x": 610, "line_y": 1604},
    {"name": "phone", "text": "918-964-9311", "x": 550, "line_y": 1888},
    {"name": "email", "text": "Dakotalynn9292@gmail.com", "x": 545, "line_y": 1982}
  ],
  "blank_zones": [
    {"name": "signature", "x1": 1098, "y1": 2720, "x2": 2544, "y2": 2765, "max_added": 50}
  ]
}
```

## Coordinate discovery

```bash
pdftoppm -r 300 -png SOURCE.pdf /tmp/src
python3 scripts/detect_lines.py /tmp/src-1.png --out /tmp/lines.json
# Map label OCR ends → field x; nearest underscore y → line_y
```

## Gate

```bash
python3 scripts/typewriter_fill.py --source-png /tmp/src-1.png --fields fields.json --out OUT.pdf
python3 scripts/verify_on_line.py --filled-png OUT_300.png --source-png /tmp/src-1.png --fields fields.json
```
