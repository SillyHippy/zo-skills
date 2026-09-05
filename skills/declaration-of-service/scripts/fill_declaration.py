#!/usr/bin/env python3
"""DEPRECATED — use fill_proof.py instead. Generates PROOF OF SERVICE PDFs."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from fill_proof import main

if __name__ == "__main__":
    main()
