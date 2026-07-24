# Manager

Tkinter process manager for the HeckNet printer scripts, with per-process log tailing and status lights.

A Tkinter panel for running the other HeckNet printer scripts. Each one is
launched as a subprocess with its output streamed into a collapsible log pane.

| Light | Meaning |
|---|---|
| green | running, no errors in the recent window |
| yellow | running, but errors seen recently |
| red | not running - stopped, crashed, or never started |

Start, stop and restart are per script, and uptime is shown for each.

## Setup

Set `HECKNET_ROOT` to the folder holding the script directories, or leave it
unset and put this file alongside them.

    setx HECKNET_ROOT "C:\path\to\hecknet"

Each entry in `_SCRIPT_DEFS` names a folder and a filename stem. At startup
the folder is scanned and the highest-numbered file matching that stem is the
one launched, so dropping in a newer version is enough to switch to it. The
resolved filename is logged when the script starts, so you can confirm which
version was picked.

Scripts are launched unbuffered so their output appears in the log pane as it
happens rather than in batches.

## Requirements

- Windows. Printing goes through the Win32 GDI API.
- Python 3.10 or later.
- An 80mm thermal printer installed as a Windows printer. Built against an
  XP-80C at 203 DPI; other 80mm printers should work if the DPI matches.

Set `PRINTER_NAME` in `hecknet_manager.py` to the printer's name as it appears in
Settings > Printers & scanners.

Receipts are rendered as images at 4x and downsampled before printing, which
is what keeps the text dark and legible on a thermal head. Courier is used
throughout; glyphs Courier lacks are composited from Segoe UI Emoji.

## Running

```bash
python hecknet_manager.py
```

## A note on the history

Only one source file was retained. Its own history documents an initial release and a second version adding version auto-discovery; the published 1.1.0 corresponds to that second version. Files labelled 1.2 through 1.4 were not kept, and no changes for them were ever recorded.

## Versioning

Tagged releases, with the change notes in [CHANGELOG.md](CHANGELOG.md).

## Licence

MIT. See [LICENSE](LICENSE).
