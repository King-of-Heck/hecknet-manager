# Manager

Tkinter process manager for the HeckNet printer scripts, with per-process log tailing, permanent on-disk logs and status lights.

A Tkinter panel for running the other HeckNet printer scripts. Each one is
launched as a subprocess with its output streamed into a collapsible log pane.

| Light | Meaning |
|---|---|
| green | running, no errors in the recent window |
| yellow | running, but errors seen recently |
| red | not running - stopped, crashed, or never started |
| grey | scheduled, waiting for its next run |

Start, stop and restart are per script, and uptime is shown for each.

## Logs

Every line a script writes is appended to `logs/<id>.log` next to the manager,
as well as going to the live panel. The panel is only the recent view: it keeps
the last 5,000 lines, so for a script that polls every ten minutes the earliest
of them eventually scroll away. The file is the record, and it survives closing
the manager.

Lines on disk carry the full date, not just the time, because a file can span
weeks. A line that already begins with a full date-and-time stamp of its own
is left as it is rather than stamped twice; a time-only stamp still gets the
prefix, since the date is the point. Once a file passes 10 MB
(`LOG_ROLLOVER_BYTES`) it becomes `<id>.log.1`, the part that was `.1` becomes
`.2`, and so on. Parts are never deleted.

The COPY button puts the whole log for that script on the clipboard, every
rolled part included and oldest first. It confirms with the size, so you know
how large a paste you are about to make.

`logs/manager.log` is the panel's own log rather than a script's. Each start
appends a banner naming the version and the file it is running from, followed
by the path scan showing which script file every card resolved to. It is only
ever appended to, so it doubles as a record of when the version last changed.

## Version

`MANAGER_VERSION` is shown in the window title, beside the header and in the
status bar, and is written into every log at startup. It is maintained by hand,
so the banner prints the running filename alongside it — if the two disagree,
that is visible rather than quietly wrong.

## Console window

Started in a way that gives it a console of its own, such as double-clicking
the file, the panel hides that window. A console it shares with a shell or an
editor's build is left alone, since hiding it would take the terminal with it;
the test is how many processes are attached, not whether a console exists.

Running it under `pythonw.exe` works too, which avoids the console being
created in the first place.

## Scheduled scripts

An entry in `_SCRIPT_DEFS` can carry a `"schedule"` list of `"HH:MM"` times
(24-hour, local). The Morning and Evening reports use it:

    "schedule": ["08:00"],

While the panel is open it starts those scripts at those times. A time that
passes while the panel is closed, or more than five minutes late (after the PC
wakes from sleep, say), is skipped rather than caught up. If the script is
already running when its time comes, that run is skipped and logged.

Scheduled scripts sit grey between runs, showing the next run time, and turn
yellow if their last run logged an error. START ALL leaves them alone; their
own START button still runs them immediately.

## Setup

Set `HECKNET_ROOT` to the folder holding the script directories, or leave it
unset and put this file alongside them.

    setx HECKNET_ROOT "C:\path\to\hecknet"

Each entry in `_SCRIPT_DEFS` names a folder and a filename stem. The folder is
scanned and the highest-numbered file matching that stem is the one launched,
so dropping in a newer version is enough to switch to it. The resolved
filename is logged when the script starts, so you can confirm which version
was picked.

The scan runs at startup and again every time a script is started, so a file
deployed while the panel is open is picked up by that script's RESTART — you
do not have to restart the panel. A change of version is logged; an unchanged
one is not. If the scan fails, because the folder has gone or a network share
has blinked, the script stays on the file it is already running.

The panel does not upgrade itself this way. Whatever launches `hecknet_manager.py`
names one file, so a newer copy of the manager takes effect only once that
launcher points at it.

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
