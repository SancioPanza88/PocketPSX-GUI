"""PocketPSX core logic — download, extract, optimize RetroArch for 3DS (PS1/PCSX-ReARMed).

Separated from GUI/CLI so it can be tested and reused.
Original idea: versione2.py (PocketPsx 2.0). Rewritten with error handling,
progress callbacks and pathlib.
"""
from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

import requests

try:
    import py7zr
    HAS_PY7ZR = True
except ImportError:  # pragma: no cover
    HAS_PY7ZR = False

APP_VERSION = "3.0.0"
FALLBACK_STABLE = "1.19.1"

BIOS_LIST = ["SCPH1001.BIN", "SCPH7502.BIN", "SCPH5500.BIN"]
EXPECTED_BIOS_SIZE = 524_288  # 512 KiB original Sony BIOS

STABLE_INDEX_URL = "https://buildbot.libretro.com/stable/"
NIGHTLY_URL = "https://buildbot.libretro.com/nightly/nintendo/3ds/RetroArch_cia.7z"


def stable_url(version: str) -> str:
    return f"https://buildbot.libretro.com/stable/{version}/nintendo/3ds/RetroArch_cia.7z"


LogFn = Callable[[str], None]
ProgressFn = Callable[[int, int], None]  # downloaded, total (total may be 0 if unknown)


@dataclass
class SetupResult:
    ok: bool
    message: str
    output_dir: Optional[Path] = None
    bios_found: list[str] = field(default_factory=list)
    bios_missing: list[str] = field(default_factory=list)


def noop(*_args, **_kwargs):
    pass


def get_latest_stable_version(timeout: int = 10) -> str:
    """Scrape buildbot stable index for the newest X.Y.Z version."""
    try:
        resp = requests.get(STABLE_INDEX_URL, timeout=timeout,
                            headers={"User-Agent": "PocketPSX-GUI"})
        resp.raise_for_status()
        versions = re.findall(r"(\d+\.\d+\.\d+)", resp.text)
        if not versions:
            return FALLBACK_STABLE

        def key(v: str):
            return [int(p) for p in v.split(".")]

        return sorted(set(versions), key=key)[-1]
    except Exception:
        return FALLBACK_STABLE


def check_bios(workdir: Path) -> tuple[list[str], list[str]]:
    """Return (found, missing) BIOS names in workdir. Found = exists + 512KiB."""
    found, missing = [], []
    for name in BIOS_LIST:
        p = workdir / name
        if p.exists() and p.stat().st_size == EXPECTED_BIOS_SIZE:
            found.append(name)
        else:
            # accept case-insensitive name but wrong size counts as missing
            alt = next((c for c in [workdir / name.upper(), workdir / name.lower()]
                        if c.exists()), None)
            if alt is not None and alt.stat().st_size == EXPECTED_BIOS_SIZE:
                found.append(name)
            else:
                missing.append(name)
    return found, missing


def download_file(url: str, dest: Path, log: LogFn = noop,
                  progress: ProgressFn = noop, timeout: int = 30) -> Path:
    log(f"Download: {url}")
    with requests.get(url, stream=True, timeout=timeout,
                       headers={"User-Agent": "PocketPSX-GUI"}) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length", 0) or 0)
        downloaded = 0
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)
                progress(downloaded, total)
    log(f"Salvato: {dest.name} ({downloaded / 1_048_576:.1f} MB)")
    return dest


def extract_archive(archive: Path, temp_dir: Path, log: LogFn = noop) -> Path:
    if not HAS_PY7ZR:
        raise RuntimeError("py7zr non installato. Esegui: pip install -r requirements.txt")
    log("Estrazione archivio 7z…")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    with py7zr.SevenZipFile(archive, mode="r") as z:
        z.extractall(path=temp_dir)
    # layout atteso: temp/RetroArch_cia/retroarch
    source = temp_dir / "RetroArch_cia" / "retroarch"
    if not source.exists():
        # fallback: cerca la prima cartella contenente "cores"
        candidates = [p for p in temp_dir.rglob("cores") if p.is_dir()]
        if candidates:
            source = candidates[0].parent
        else:
            raise FileNotFoundError("Struttura archivio inattesa: cartella 'retroarch' non trovata.")
    return source


def _safe_remove(path: Path):
    try:
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()
    except OSError:
        pass


def optimize_tree(final_dir: Path, log: LogFn = noop) -> dict:
    """Remove non-PS1 assets/cores. Returns stats dict."""
    stats = {"assets_removed": 0, "cores_removed": 0}
    keep_tokens = ("sony", "playstation", "psx", "ps1", "retroarch",
                   "menu", "bg", "font", "cursor", "ctr", "ozone", "rgui", "xmb")
    assets_root = final_dir / "assets"
    if assets_root.exists():
        for root, _dirs, files in os.walk(assets_root):
            for f in files:
                if not any(t in f.lower() for t in keep_tokens):
                    _safe_remove(Path(root) / f)
                    stats["assets_removed"] += 1
    cores_dir = final_dir / "cores"
    info_dir = cores_dir / "info"
    if info_dir.exists():
        for f in list(info_dir.iterdir()):
            if "pcsx_rearmed" not in f.name.lower():
                _safe_remove(f)
                stats["cores_removed"] += 1
    if cores_dir.exists():
        for f in list(cores_dir.iterdir()):
            if f.name.lower() not in ("pcsx_rearmed_libretro.cia", "info"):
                _safe_remove(f)
                stats["cores_removed"] += 1
    log(f"Ottimizzazione: {stats['assets_removed']} asset, "
        f"{stats['cores_removed']} core/info rimossi.")
    return stats


def install_bios(workdir: Path, final_dir: Path, log: LogFn = noop) -> tuple[list[str], list[str]]:
    sys_dir = final_dir / "system"
    sys_dir.mkdir(parents=True, exist_ok=True)
    found, missing = check_bios(workdir)
    for b in found:
        src = workdir / b
        if not src.exists():  # case variants
            src = workdir / b.upper() if (workdir / b.upper()).exists() else workdir / b.lower()
        shutil.copy(src, sys_dir / b.upper())
        shutil.copy(src, sys_dir / b.lower())
    log(f"BIOS installati: {len(found)}/{len(BIOS_LIST)}"
        + (f" (mancano: {', '.join(missing)})" if missing else ""))
    return found, missing


def install_configs(workdir: Path, final_dir: Path, log: LogFn = noop,
                    templates_dir: Optional[Path] = None):
    """Copy retroarch.cfg + PCSX-ReARMed.opt from workdir or bundled templates."""
    cfg_name, opt_name = "retroarch.cfg", "PCSX-ReARMed.opt"
    candidates_cfg = [workdir / cfg_name]
    candidates_opt = [workdir / opt_name]
    if templates_dir:
        candidates_cfg.append(templates_dir / cfg_name)
        candidates_opt.append(templates_dir / opt_name)
    # retroarch.cfg
    for c in candidates_cfg:
        if c.exists():
            shutil.copy(c, final_dir / cfg_name)
            log(f"Config installata: {cfg_name} (da {c.parent.name}/)")
            break
    else:
        log(f"ATTENZIONE: {cfg_name} non trovato, uso default RetroArch.")
    # core options
    opt_dir = final_dir / "config" / "PCSX-ReARMed"
    opt_dir.mkdir(parents=True, exist_ok=True)
    for c in candidates_opt:
        if c.exists():
            shutil.copy(c, opt_dir / opt_name)
            log(f"Core options installate: {opt_name}")
            break
    else:
        log(f"ATTENZIONE: {opt_name} non trovato.")


def run_setup(channel: str = "stable", workdir: Path = Path("."),
              output_name: str = "retroarch",
              templates_dir: Optional[Path] = None,
              keep_archive: bool = False,
              log: LogFn = noop, progress: ProgressFn = noop) -> SetupResult:
    """Full pipeline: download → extract → optimize → bios → configs."""
    workdir = workdir.resolve()
    final_dir = workdir / output_name
    temp_dir = workdir / "temp_extract"

    if channel == "nightly":
        version = "nightly"
        url = NIGHTLY_URL
    else:
        version = get_latest_stable_version()
        url = stable_url(version)
        log(f"Versione stable rilevata: {version}")

    archive = workdir / f"RetroArch_{version}.7z"
    try:
        if not archive.exists():
            download_file(url, archive, log=log, progress=progress)
        else:
            log(f"Uso archivio esistente: {archive.name}")

        source = extract_archive(archive, temp_dir, log=log)

        if final_dir.exists():
            shutil.rmtree(final_dir)
        shutil.move(str(source), str(final_dir))

        optimize_tree(final_dir, log=log)
        found, missing = install_bios(workdir, final_dir, log=log)
        install_configs(workdir, final_dir, log=log, templates_dir=templates_dir)

        shutil.rmtree(temp_dir, ignore_errors=True)
        if not keep_archive and archive.exists():
            archive.unlink()
        msg = f"Completato! Cartella pronta: {final_dir}"
        if missing:
            msg += f" — BIOS mancanti: {', '.join(missing)}"
        log(msg)
        return SetupResult(True, msg, final_dir, found, missing)
    except Exception as exc:  # noqa: BLE001
        shutil.rmtree(temp_dir, ignore_errors=True)
        msg = f"ERRORE: {exc}"
        log(msg)
        return SetupResult(False, msg, None, [], list(BIOS_LIST))
