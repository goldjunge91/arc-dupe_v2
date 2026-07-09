#!/usr/bin/env python3
"""
Build script for SlotSwapTool.exe.
Injects a unique per-build signature, runs PyInstaller, then restores
the source file so git stays clean.

Output:  duper/dist/SlotSwapTool.exe
         duper/build/   (PyInstaller work dir)
"""
import os
import random
import string
import subprocess
import sys
import uuid


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))           # duper/
ROOT = os.path.dirname(HERE)                                # repo root

SOURCE_FILE = os.path.join(HERE, "slot_swap_tool.py")
SPEC_FILE   = os.path.join(HERE, "SlotSwapTool.spec")

PLACEHOLDER = "__BUILD_ID_PLACEHOLDER__"


def _resolve_python() -> str:
    """Return the project .venv Python if present, otherwise sys.executable."""
    venv_python = os.path.join(ROOT, ".venv", "Scripts", "python.exe")
    if os.path.exists(venv_python):
        print(f"[BUILD] Using project venv Python: {venv_python}")
        return venv_python
    print(f"[BUILD] Using system Python: {sys.executable}")
    return sys.executable


def generate_signature() -> str:
    """Return a unique UUID + random-string watermark."""
    uid  = str(uuid.uuid4()).replace("-", "").upper()[:8]
    rand = "".join(random.choices(string.ascii_letters, k=10))
    return f"{uid}-{rand}"


def build() -> None:
    signature = generate_signature()
    print(f"[BUILD] Generated unique signature: {signature}")

    # Read source
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        original_source = f.read()

    if PLACEHOLDER not in original_source:
        print("[ERROR] Placeholder not found in source! Already built?")
        print(f'        Reset the BUILD_ID line to: BUILD_ID = "{PLACEHOLDER}"')
        sys.exit(1)

    # Inject signature
    modified_source = original_source.replace(PLACEHOLDER, signature)
    with open(SOURCE_FILE, "w", encoding="utf-8") as f:
        f.write(modified_source)
    print(f"[BUILD] Injected signature into {SOURCE_FILE}")

    python = _resolve_python()

    try:
        print("[BUILD] Running PyInstaller...")
        subprocess.run(
            [
                python, "-m", "PyInstaller",
                SPEC_FILE,
                "--noconfirm",
                "--distpath", os.path.join(HERE, "dist"),
                "--workpath", os.path.join(HERE, "build"),
            ],
            check=True,
            cwd=HERE,   # run from duper/ so spec's __file__ resolves correctly
        )
        print(f"[BUILD] Success!  Signature: {signature}")
        print(f"[BUILD] Output:   {os.path.join(HERE, 'dist', 'SlotSwapTool.exe')}")

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] PyInstaller failed: {e}")

    finally:
        # Restore original source — keep git clean
        with open(SOURCE_FILE, "w", encoding="utf-8") as f:
            f.write(original_source)
        print(f"[BUILD] Restored {SOURCE_FILE} to original state")


if __name__ == "__main__":
    build()
