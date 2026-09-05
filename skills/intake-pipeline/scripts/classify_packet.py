#!/usr/bin/env python3
"""Classify a legal intake packet before any case/Drive/field-sheet action."""
import argparse
import json
import re
from pathlib import Path


def classify(text: str) -> str:
    t = text.lower()
    if re.search(r"\babc\s+legal\b|abcl\s+legal|abclegal", t):
        return "abc_legal"
    if re.search(r"\bproof\s+serve\b|proofserve|proof-serve", t):
        return "proof_serve"
    return "normal_client"


def main():
    p = argparse.ArgumentParser(description="Classify ABC Legal, Proof Serve, or normal client packet")
    p.add_argument("files", nargs="+", help="Text files to inspect")
    args = p.parse_args()
    text = "\n".join(Path(f).read_text(encoding="utf-8", errors="ignore") for f in args.files)
    result = {"classification": classify(text), "requires_confirmation": False}
    if result["classification"] != "normal_client":
        result["requires_confirmation"] = True
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()


def classify_packet_text(text: str) -> dict:
    kind = classify(text)
    return {"classification": kind, "requires_confirmation": kind != "normal_client"}


__all__ = ["classify", "classify_packet_text"]
