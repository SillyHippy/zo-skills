#!/usr/bin/env python3
"""Fast field sheet: extract fields → fill template → PDF. Under 5 seconds when text-extractable, ~15s with LLM extraction."""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

TEMPLATE = Path(__file__).parent.parent / "assets" / "template.html"

