#!/usr/bin/env python3
"""Regression test for hardened placement: simple form, trap form, anchor override."""
import json

import core

ok = True

# 1) Simple form — must place 5/5 on lines, zero needs_review
core.make_test_form("tests/test_blank.pdf")
r = core.fill_flat_pdf(
    "tests/test_blank.pdf", "tests/test_filled.pdf",
    {"Name": "John Doe", "Address": "123 Main St",
     "City, State, ZIP": "Tulsa, OK 74116", "Case No.": "FD-2026-1234",
     "Phone": "918-555-1234"},
)
print("SIMPLE placed:", [(p["label"], p["underscore"], p["no_line"]) for p in r["placed"]])
print("SIMPLE needs_review:", r["needs_review"], "missing:", r["missing"])
assert len(r["placed"]) == 5 and not r["needs_review"] and not r["missing"], "simple failed"
ok &= True

# 2) Trap form (box border + full-width section rule) — values must still land on row underscores
core.make_test_form("tests/test_trap.pdf", bordered=True)
r2 = core.fill_flat_pdf(
    "tests/test_trap.pdf", "tests/test_trap_filled.pdf",
    {"Name": "Jane Smith", "Address": "456 Oak Ave",
     "City, State, ZIP": "Tulsa, OK 74116", "Case No.": "FD-2026-9999",
     "Phone": "405-555-6789"},
)
print("TRAP placed:", [(p["label"], p["underscore"], p["no_line"], p["x"]) for p in r2["placed"]])
print("TRAP needs_review:", r2["needs_review"], "missing:", r2["missing"])
assert len(r2["placed"]) == 5 and not r2["needs_review"] and not r2["missing"], "trap failed"

# 3) Anchor override — explicit coords must be used verbatim
r3 = core.fill_flat_pdf(
    "tests/test_blank.pdf", "tests/test_anchored.pdf",
    {"Name": "Anchored Person"},
    anchors={"Name": {"x": 500, "baseline": 300, "x_end": 2000}},
)
print("ANCHOR placed:", r3["placed"])
assert r3["placed"][0]["x"] == 500 and r3["placed"][0]["baseline"] == 300, "anchor failed"

print("ALL PLACEMENT TESTS: PASS")
