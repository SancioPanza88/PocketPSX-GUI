# ◉ PocketPSX-GUI v3.0.0

**Setup guidato di RetroArch PS1 per Nintendo 3DS (core PCSX-ReARMed) — con interfaccia grafica moderna.**

> Evoluzione di PocketPsx 2.0 (tool CLI `versione2.py`): stesso motore di ottimizzazione, nuova GUI bilingue IT/EN, download con progress bar, verifica BIOS, template di configurazione integrati.

🎬 Tutorial e aggiornamenti: https://www.youtube.com/@DraxTube01

---

## ✨ Funzionalità

- 🖥️ **GUI moderna** (CustomTkinter, tema scuro stile PlayStation) + **CLI** per automazione
- 🌍 **Bilingue IT/EN** con switch istantaneo
- 📦 Download **Stable** (auto-rilevamento ultima versione dal Buildbot) o **Nightly**
- 📊 Progress bar reale (MB scaricati / totali) in thread separato — la UI non si blocca
- 🧹 **Ottimizzazione SD**: rimuove asset non-PS1, core e file info inutili
- 🔍 **Verifica BIOS** con semafori verde/rosso (controllo dimensione 512 KiB)
- ⚙️ Template integrati `retroarch.cfg` + `PCSX-ReARMed.opt` ottimizzati per 3DS
- 📂 Apertura automatica cartella finale, opzione mantieni archivio

## 🖼️ Anteprima

```
┌────────────────────────────────────────────┐
│  ◉ POCKETPSX-GUI            (header blu PS) │
│  Setup RetroArch PS1 per 3DS               │
├────────────────────────────────────────────┤
│ [● Stable ○ Nightly]   [IT|EN]             │
│ BIOS: SCPH1001 ● SCPH7502 ● SCPH5500 ●     │
│ [████████████░░░░░░] 125.3/210.0 MB (60%)  │
│ [ ⬇ SCARICA E INSTALLA ]                   │
│ LOG …                                      │
└────────────────────────────────────────────┘
```

## 🚀 Installazione

```bash
git clone https://github.com/SancioPanza88/PocketPSX-GUI.git
cd PocketPSX-GUI
pip install -r requirements.txt
python pocketpsx_gui.py
```

Solo terminale:

```bash
python cli.py --channel stable --workdir ./lavoro
python cli.py --help
```

### Creare l'EXE Windows

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name "PocketPSX-GUI" pocketpsx_gui.py
```

## 📁 Uso

1. Copia i tuoi BIOS **nella cartella di lavoro** (vedi sotto).
2. Avvia la GUI, scegli **Stable** (consigliata) o **Nightly**.
3. Premi **Scarica e installa** e attendi il log `Completato!`.
4. Copia la cartella `retroarch/` generata nella root della SD del 3DS.

Struttura prodotta:

```
lavoro/
├── retroarch/
│   ├── cores/ (solo pcsx_rearmed_libretro.cia + info)
│   ├── system/ (BIOS in maiuscolo + minuscolo)
│   ├── config/PCSX-ReARMed/PCSX-ReARMed.opt
│   └── retroarch.cfg
```

## 🔑 BIOS — NOTA LEGALE

I BIOS Sony (`SCPH1001.BIN`, `SCPH7502.BIN`, `SCPH5500.BIN`, 512 KiB ciascuno) **NON sono inclusi** in questo repo per copyright.
Procurali effettuando il dump dal tuo hardware originale e copiali nella cartella di lavoro prima del setup.
Senza BIOS l'emulazione potrebbe non avviarsi o usare l'HLE meno compatibile.

Verifica rapida: la GUI mostra 🟢 se il file esiste ed è esattamente 524.288 byte.

## ⚙️ Configurazione inclusa

- `config_templates/retroarch.cfg` — preset 3DS (audio dsp_thread, driver ctr, playlist, ecc.)
- `config_templates/PCSX-ReARMed.opt` — DRC attivo, frameskip auto, clock PSX 57, audio ottimizzato (no XA/CDDA per performance)

Puoi sostituirli con i tuoi: metti `retroarch.cfg` / `PCSX-ReARMed.opt` nella cartella di lavoro e avranno priorità sui template.

## 🧠 Come funziona (pipeline)

`core.run_setup()` → download 7z dal Buildbot → estrazione `RetroArch_cia/retroarch` → pulizia asset/core → copia BIOS (upper+lower) → copia config → cleanup temp.

Funzioni riusabili: `get_latest_stable_version()`, `check_bios()`, `download_file()`, `extract_archive()`, `optimize_tree()`, `install_bios()`, `install_configs()`.

## 🙏 Crediti

- Motore originale: PocketPsx 2.0 / `versione2.py`
- Core: PCSX-ReARMed, RetroArch / Libretro Buildbot
- Docs EN/IT originali conservate come riferimento storico nella release 2.0

## 📄 Licenza

MIT — vedi [LICENSE](LICENSE).

---

# ◉ PocketPSX-GUI v3.0.0 (EN)

**Guided RetroArch PS1 setup for Nintendo 3DS (PCSX-ReARMed core) — with a modern GUI.**

## Features

- Modern CustomTkinter GUI (PlayStation-style dark theme) + CLI for automation
- Bilingual IT/EN with instant switch
- Stable (auto-detected from Buildbot) or Nightly download with real progress bar
- SD optimization: strips non-PS1 assets, unused cores/info files
- BIOS check with green/red indicators (512 KiB size validation)
- Bundled tuned `retroarch.cfg` + `PCSX-ReARMed.opt`

## Quickstart

```bash
pip install -r requirements.txt
python pocketpsx_gui.py
```

## BIOS — LEGAL NOTE

Sony BIOS files are **NOT included**. Dump them legally from your own hardware and copy them into the working folder before running the setup.
