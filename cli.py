"""PocketPSX CLI — same engine as the GUI, for terminal/automation use."""
from __future__ import annotations

import argparse
from pathlib import Path

from core import APP_VERSION, run_setup

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES = BASE_DIR / "config_templates"


def main() -> int:
    ap = argparse.ArgumentParser(
        description=f"PocketPSX v{APP_VERSION} — RetroArch 3DS PS1 setup (CLI)")
    ap.add_argument("--channel", choices=["stable", "nightly"], default="stable")
    ap.add_argument("--workdir", default=".", help="working folder with BIOS + outputs")
    ap.add_argument("--output", default="retroarch", help="output folder name")
    ap.add_argument("--keep-archive", action="store_true")
    args = ap.parse_args()

    def log(m: str):
        print(m)

    def progress(done: int, total: int):
        if total:
            print(f"\r{done / 1_048_576:.1f}/{total / 1_048_576:.1f} MB "
                  f"({done / total * 100:.0f}%)", end="", flush=True)

    res = run_setup(channel=args.channel, workdir=Path(args.workdir),
                    output_name=args.output, templates_dir=TEMPLATES,
                    keep_archive=args.keep_archive, log=log, progress=progress)
    print()
    print(res.message)
    return 0 if res.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
