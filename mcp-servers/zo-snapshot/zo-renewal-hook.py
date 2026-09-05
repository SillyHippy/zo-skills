#!/usr/bin/env python3
"""
Zo Renewal Hook: Automatically runs before Zo Computer takes a VM snapshot / renewal handoff.
Creates an atomic zo-snapshot checkpoint so you have an exact, diffable history for every renewal.
"""
import sys
import subprocess
import os

def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "prepare"
    
    if action == "prepare":
        op_id = os.environ.get("ZO_RENEWAL_OPERATION_ID", "auto")
        gen = os.environ.get("ZO_RENEWAL_GENERATION", "")
        label = f"Auto-Snapshot before Zo VM Renewal (Op: {op_id} Gen: {gen})"
        try:
            subprocess.run(
                ["/usr/local/bin/zo-snapshot", "create", label, "--scope", "config"],
                check=True,
                capture_output=True,
                timeout=15
            )
        except Exception as e:
            # Don't block renewal on snapshot error
            print(f"[zo-snapshot-hook] Warning: failed to take pre-renewal snapshot: {e}", file=sys.stderr)
            sys.exit(0)

if __name__ == "__main__":
    main()
