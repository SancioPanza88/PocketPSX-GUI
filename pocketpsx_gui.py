"""PocketPSX-GUI — modern CustomTkinter interface (IT/EN) for RetroArch 3DS PS1 setup."""
from __future__ import annotations

import queue
import threading
import webbrowser
from pathlib import Path

import customtkinter as ctk

from core import (APP_VERSION, BIOS_LIST, check_bios, get_latest_stable_version,
                  run_setup)

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "config_templates"
YOUTUBE_URL = "https://www.youtube.com/@DraxTube01"

STRINGS = {
    "it": {
        "subtitle": "Setup RetroArch PS1 per Nintendo 3DS • PCSX-ReARMed",
        "channel": "Canale di distribuzione",
        "stable": "STABLE — consigliata",
        "nightly": "NIGHTLY — sperimentale",
        "stable_detected": "Stable rilevata:",
        "bios_title": "Stato BIOS (nella cartella di lavoro)",
        "bios_ok": "trovato ✓",
        "bios_missing": "mancante ✗ (copialo qui per includerlo)",
        "cfg_title": "File di configurazione",
        "options": "Opzioni",
        "keep_archive": "Mantieni archivio .7z dopo il setup",
        "open_folder": "Apri cartella finale al termine",
        "workdir": "Cartella di lavoro:",
        "browse": "Sfoglia…",
        "start": "⬇  SCARICA E INSTALLA",
        "verify": "Verifica BIOS",
        "open_out": "Apri cartella output",
        "youtube": "🎬 Tutorial YouTube",
        "ready": "Pronto. Scegli il canale e premi Avvia.",
        "running": "Installazione in corso… non chiudere.",
        "done": "✅ Completato!",
        "failed": "❌ Fallito, leggi il log.",
        "language": "Lingua",
        "footer": "I BIOS Sony (SCPH*.BIN) non sono inclusi: procurali legalmente dal tuo hardware.",
    },
    "en": {
        "subtitle": "RetroArch PS1 setup for Nintendo 3DS • PCSX-ReARMed",
        "channel": "Release channel",
        "stable": "STABLE — recommended",
        "nightly": "NIGHTLY — experimental",
        "stable_detected": "Detected stable:",
        "bios_title": "BIOS status (in working folder)",
        "bios_ok": "found ✓",
        "bios_missing": "missing ✗ (copy it here to include it)",
        "cfg_title": "Configuration files",
        "options": "Options",
        "keep_archive": "Keep .7z archive after setup",
        "open_folder": "Open output folder when done",
        "workdir": "Working folder:",
        "browse": "Browse…",
        "start": "⬇  DOWNLOAD & INSTALL",
        "verify": "Check BIOS",
        "open_out": "Open output folder",
        "youtube": "🎬 YouTube tutorials",
        "ready": "Ready. Pick a channel and press Start.",
        "running": "Installing… do not close.",
        "done": "✅ Done!",
        "failed": "❌ Failed, see log.",
        "language": "Language",
        "footer": "Sony BIOS files (SCPH*.BIN) are NOT included: dump them legally from your hardware.",
    },
}

# PlayStation-inspired palette
PS_BLUE = "#003791"
PS_TEAL = "#008191"
BG_DARK = "#1b1e26"
CARD = "#232733"
TEXT_MUTED = "#9aa3b2"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.lang = "it"
        self.channel = ctk.StringVar(value="stable")
        self.keep_archive = ctk.BooleanVar(value=False)
        self.open_folder = ctk.BooleanVar(value=True)
        self.workdir = ctk.StringVar(value=str(BASE_DIR))
        self.log_q: queue.Queue[str] = queue.Queue()
        self.busy = False
        self.title(f"PocketPSX-GUI v{APP_VERSION}")
        self.geometry("860x760")
        self.minsize(760, 680)
        self._build()
        self._refresh_all()
        self.after(120, self._drain_log)
        threading.Thread(target=self._detect_stable_bg, daemon=True).start()

    # ---------- layout ----------
    def _build(self):
        s = STRINGS[self.lang]
        # header
        self.header = ctk.CTkFrame(self, fg_color=PS_BLUE, corner_radius=0)
        self.header.pack(fill="x")
        self.title_lbl = ctk.CTkLabel(self.header, text="◉ POCKETPSX-GUI",
                                      font=ctk.CTkFont(size=26, weight="bold"),
                                      text_color="white")
        self.title_lbl.pack(pady=(14, 0))
        self.sub_lbl = ctk.CTkLabel(self.header, text=s["subtitle"], text_color="#d7e3ff")
        self.sub_lbl.pack(pady=(0, 4))
        self.ver_lbl = ctk.CTkLabel(self.header, text=f"v{APP_VERSION} • RetroArch 3DS • PCSX-ReARMed",
                                    text_color="#bcd0ff", font=ctk.CTkFont(size=12))
        self.ver_lbl.pack(pady=(0, 12))

        body = ctk.CTkScrollableFrame(self, fg_color=BG_DARK)
        body.pack(fill="both", expand=True, padx=12, pady=12)

        # top row: channel + language
        top = ctk.CTkFrame(body, fg_color=CARD, corner_radius=12)
        top.pack(fill="x", pady=(0, 10))
        self.channel_lbl = ctk.CTkLabel(top, text=s["channel"], font=ctk.CTkFont(weight="bold"))
        self.channel_lbl.pack(anchor="w", padx=14, pady=(12, 4))
        ch_row = ctk.CTkFrame(top, fg_color="transparent")
        ch_row.pack(fill="x", padx=14)
        ctk.CTkRadioButton(ch_row, text=s["stable"], variable=self.channel,
                           value="stable").pack(side="left", padx=(0, 18), pady=4)
        ctk.CTkRadioButton(ch_row, text=s["nightly"], variable=self.channel,
                           value="nightly").pack(side="left", pady=4)
        self.stable_lbl = ctk.CTkLabel(top, text=f"{s['stable_detected']} …", text_color=TEXT_MUTED)
        self.stable_lbl.pack(anchor="w", padx=14, pady=(2, 6))
        lang_row = ctk.CTkFrame(top, fg_color="transparent")
        lang_row.pack(fill="x", padx=14, pady=(0, 12))
        self.lang_lbl = ctk.CTkLabel(lang_row, text=s["language"])
        self.lang_lbl.pack(side="left")
        self.lang_menu = ctk.CTkSegmentedButton(lang_row, values=["IT", "EN"],
                                                command=self._switch_lang)
        self.lang_menu.pack(side="left", padx=10)
        self.lang_menu.set("IT")

        # workdir
        wd = ctk.CTkFrame(body, fg_color=CARD, corner_radius=12)
        wd.pack(fill="x", pady=(0, 10))
        self.wd_lbl = ctk.CTkLabel(wd, text=s["workdir"], font=ctk.CTkFont(weight="bold"))
        self.wd_lbl.pack(anchor="w", padx=14, pady=(12, 4))
        wd_row = ctk.CTkFrame(wd, fg_color="transparent")
        wd_row.pack(fill="x", padx=14, pady=(0, 12))
        ctk.CTkEntry(wd_row, textvariable=self.workdir).pack(side="left", fill="x", expand=True,
                                                             padx=(0, 8))
        self.browse_btn = ctk.CTkButton(wd_row, text=s["browse"], width=110,
                                        command=self._browse)
        self.browse_btn.pack(side="left")

        # bios card
        bios = ctk.CTkFrame(body, fg_color=CARD, corner_radius=12)
        bios.pack(fill="x", pady=(0, 10))
        self.bios_lbl = ctk.CTkLabel(bios, text=s["bios_title"], font=ctk.CTkFont(weight="bold"))
        self.bios_lbl.pack(anchor="w", padx=14, pady=(12, 4))
        self.bios_rows: dict[str, ctk.CTkLabel] = {}
        for name in BIOS_LIST:
            row = ctk.CTkFrame(bios, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=2)
            ctk.CTkLabel(row, text=name, font=ctk.CTkFont(family="Consolas")).pack(side="left")
            st = ctk.CTkLabel(row, text="…", text_color=TEXT_MUTED)
            st.pack(side="right")
            self.bios_rows[name] = st
        self.cfg_lbl = ctk.CTkLabel(bios, text="", text_color=TEXT_MUTED,
                                    font=ctk.CTkFont(size=12))
        self.cfg_lbl.pack(anchor="w", padx=14, pady=(6, 12))

        # options
        opt = ctk.CTkFrame(body, fg_color=CARD, corner_radius=12)
        opt.pack(fill="x", pady=(0, 10))
        self.opt_lbl = ctk.CTkLabel(opt, text=s["options"], font=ctk.CTkFont(weight="bold"))
        self.opt_lbl.pack(anchor="w", padx=14, pady=(12, 4))
        self.keep_chk = ctk.CTkCheckBox(opt, text=s["keep_archive"], variable=self.keep_archive)
        self.keep_chk.pack(anchor="w", padx=14, pady=2)
        self.open_chk = ctk.CTkCheckBox(opt, text=s["open_folder"], variable=self.open_folder)
        self.open_chk.pack(anchor="w", padx=14, pady=(2, 12))

        # progress
        prog = ctk.CTkFrame(body, fg_color=CARD, corner_radius=12)
        prog.pack(fill="x", pady=(0, 10))
        self.status_lbl = ctk.CTkLabel(prog, text=s["ready"])
        self.status_lbl.pack(anchor="w", padx=14, pady=(12, 4))
        self.bar = ctk.CTkProgressBar(prog)
        self.bar.pack(fill="x", padx=14, pady=(0, 4))
        self.bar.set(0)
        self.pct_lbl = ctk.CTkLabel(prog, text="", text_color=TEXT_MUTED)
        self.pct_lbl.pack(anchor="e", padx=14, pady=(0, 10))

        # buttons
        btns = ctk.CTkFrame(body, fg_color="transparent")
        btns.pack(fill="x", pady=(0, 10))
        self.start_btn = ctk.CTkButton(btns, text=s["start"], fg_color=PS_TEAL,
                                       hover_color="#006b78", height=44,
                                       font=ctk.CTkFont(size=15, weight="bold"),
                                       command=self._start)
        self.start_btn.pack(fill="x", pady=4)
        row2 = ctk.CTkFrame(btns, fg_color="transparent")
        row2.pack(fill="x")
        self.verify_btn = ctk.CTkButton(row2, text=s["verify"], command=self._refresh_all)
        self.verify_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.out_btn = ctk.CTkButton(row2, text=s["open_out"], command=self._open_output)
        self.out_btn.pack(side="left", fill="x", expand=True, padx=(4, 0))
        self.yt_btn = ctk.CTkButton(body, text=s["youtube"], fg_color="transparent",
                                    border_width=1, command=lambda: webbrowser.open(YOUTUBE_URL))
        self.yt_btn.pack(fill="x")

        # log
        logcard = ctk.CTkFrame(body, fg_color=CARD, corner_radius=12)
        logcard.pack(fill="both", expand=True, pady=(10, 0))
        ctk.CTkLabel(logcard, text="LOG", font=ctk.CTkFont(weight="bold")).pack(anchor="w",
                                                                               padx=14, pady=(10, 4))
        self.logbox = ctk.CTkTextbox(logcard, height=180, font=ctk.CTkFont(family="Consolas", size=12))
        self.logbox.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.logbox.configure(state="disabled")

        self.footer_lbl = ctk.CTkLabel(self, text=s["footer"], text_color=TEXT_MUTED,
                                       font=ctk.CTkFont(size=11), wraplength=820)
        self.footer_lbl.pack(pady=(0, 10))

    # ---------- behavior ----------
    def _t(self, key: str) -> str:
        return STRINGS[self.lang][key]

    def _switch_lang(self, val: str):
        self.lang = "it" if val.upper() == "IT" else "en"
        s = STRINGS[self.lang]
        self.sub_lbl.configure(text=s["subtitle"])
        self.channel_lbl.configure(text=s["channel"])
        self.stable_lbl.configure(text=f"{s['stable_detected']} {getattr(self, '_stable', '…')}")
        self.bios_lbl.configure(text=s["bios_title"])
        self.wd_lbl.configure(text=s["workdir"])
        self.browse_btn.configure(text=s["browse"])
        self.opt_lbl.configure(text=s["options"])
        self.keep_chk.configure(text=s["keep_archive"])
        self.open_chk.configure(text=s["open_folder"])
        self.start_btn.configure(text=s["start"])
        self.verify_btn.configure(text=s["verify"])
        self.out_btn.configure(text=s["open_out"])
        self.yt_btn.configure(text=s["youtube"])
        self.lang_lbl.configure(text=s["language"])
        self.footer_lbl.configure(text=s["footer"])
        if not self.busy:
            self.status_lbl.configure(text=s["ready"])
        self._refresh_bios()

    def _log(self, msg: str):
        self.log_q.put(msg)

    def _drain_log(self):
        try:
            while True:
                msg = self.log_q.get_nowait()
                self.logbox.configure(state="normal")
                self.logbox.insert("end", msg + "\n")
                self.logbox.see("end")
                self.logbox.configure(state="disabled")
        except queue.Empty:
            pass
        self.after(120, self._drain_log)

    def _detect_stable_bg(self):
        v = get_latest_stable_version()
        self._stable = v
        self.after(0, lambda: self.stable_lbl.configure(
            text=f"{self._t('stable_detected')} {v}"))

    def _refresh_bios(self):
        wd = Path(self.workdir.get())
        if not wd.exists():
            return
        found, _missing = check_bios(wd)
        for name, lbl in self.bios_rows.items():
            if name in found:
                lbl.configure(text=f"● {self._t('bios_ok')}", text_color="#2ecc71")
            else:
                lbl.configure(text=f"● {self._t('bios_missing')}", text_color="#e74c3c")
        cfg = TEMPLATES_DIR / "retroarch.cfg"
        opt = TEMPLATES_DIR / "PCSX-ReARMed.opt"
        self.cfg_lbl.configure(
            text=f"{self._t('cfg_title')}: retroarch.cfg "
                 f"{'✓' if cfg.exists() else '✗'} • PCSX-ReARMed.opt "
                 f"{'✓' if opt.exists() else '✗'} (bundled templates)")

    def _refresh_all(self):
        self._refresh_bios()
        self._log("BIOS check: " + ", ".join(
            f"{n}={'OK' if (Path(self.workdir.get()) / n).exists() else 'KO'}"
            for n in BIOS_LIST))

    def _browse(self):
        from tkinter import filedialog
        d = filedialog.askdirectory(initialdir=self.workdir.get())
        if d:
            self.workdir.set(d)
            self._refresh_bios()

    def _open_output(self):
        import os
        import subprocess
        out = Path(self.workdir.get()) / "retroarch"
        target = str(out if out.exists() else Path(self.workdir.get()))
        try:
            if os.name == "nt":
                import subprocess as sp
                sp.Popen(["explorer", target])
            elif hasattr(os, "uname") and os.uname().sysname == "Darwin":
                subprocess.Popen(["open", target])
            else:
                subprocess.Popen(["xdg-open", target])
        except Exception as exc:
            self._log(f"Impossibile aprire cartella: {exc}")

    def _progress(self, done: int, total: int):
        def _ui():
            if total > 0:
                frac = min(done / total, 1.0)
                self.bar.set(frac)
                self.pct_lbl.configure(
                    text=f"{done / 1_048_576:.1f} / {total / 1_048_576:.1f} MB ({frac * 100:.0f}%)")
            else:
                self.pct_lbl.configure(text=f"{done / 1_048_576:.1f} MB")
        self.after(0, _ui)

    def _start(self):
        if self.busy:
            return
        self.busy = True
        self.bar.set(0)
        self.status_lbl.configure(text=self._t("running"))
        wd = Path(self.workdir.get())
        wd.mkdir(parents=True, exist_ok=True)
        channel = self.channel.get()
        keep = self.keep_archive.get()
        do_open = self.open_folder.get()

        def worker():
            res = run_setup(channel=channel, workdir=wd, templates_dir=TEMPLATES_DIR,
                            keep_archive=keep, log=self._log, progress=self._progress)
            def done():
                self.busy = False
                self.bar.set(1.0 if res.ok else 0)
                self.status_lbl.configure(text=self._t("done") if res.ok else self._t("failed"))
                self._refresh_bios()
                if res.ok and do_open:
                    self._open_output()
            self.after(0, done)
        threading.Thread(target=worker, daemon=True).start()


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
