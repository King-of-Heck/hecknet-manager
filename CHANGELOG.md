# Changelog

Version numbers were reassigned for release (the old scheme bumped the
minor version for bugfixes); the original number is in parentheses. The
notes below are from each script's own version history.

Only one source file was retained. Its own history documents an initial release and a second version adding version auto-discovery; the published 1.1.0 corresponds to that second version. Files labelled 1.2 through 1.4 were not kept, and no changes for them were ever recorded.

## 1.5.0

The panel now says which version it is, and no longer leaves a console window
behind it.

`MANAGER_VERSION` appears in the window title, beside the header and in the
status bar, and a banner naming it goes into every card's log at startup.
Nothing recorded this before, so after a deploy the only way to tell one build
from another was to ask whoever had started it — which is exactly the question
that came up. The banner prints the running filename next to the constant,
because the constant is maintained by hand: the two disagreeing is then visible
rather than quietly wrong.

The startup path scan, which only ever went to stdout, is now also written to
`logs/manager.log`. That is where the record of which script file each card
resolved to now lives, and it matters more once there is no console to print to.

Started in a way that gives it a console of its own — double-clicking the file —
that window is hidden. A console shared with a shell or an editor's build is
left alone, since hiding it would take the terminal with it, so the test is how
many processes are attached rather than whether a console exists. Running under
`pythonw.exe` is handled too: `sys.stdout` and `sys.stderr` are `None` there,
which `print()` tolerates but a direct write would not.

## 1.4.1

A line that already begins with its own full date-and-time stamp no longer gets
a second one added on the way to disk.

The scripts all timestamp their own output, so every line in `logs/<id>.log`
read `[2026-11-09 14:23:37] [2026-11-09 14:23:37] Polling 45 feeds...`, the two
stamps differing by up to a second — the script's emit time against the moment
the UI tick drained the queue.

A time-only stamp still gets the prefix, since supplying the date is the whole
reason the disk log stamps at all and a file can span weeks. Manager lines,
which carry no stamp of their own, are unaffected.

## 1.4.0

Each script's version is re-resolved every time it starts, so dropping a newer
file into its folder and pressing RESTART switches to it.

The folder scan ran once, while the manager built its config, and the resolved
path was baked into the card. RESTART re-launched that same path, so a newly
deployed script sat unused until the manager application itself was restarted —
which is not where anyone looks. A version that had been in place for twelve
days was found still unused this way, with the fault it fixed still being
logged hundreds of times a day.

A version change is announced in the log. An unchanged version is not, since
every restart now re-resolves and saying so each time would bury the one
occasion it matters. The version badge on the card is updated to match.

If a re-resolve fails — the folder has gone, a network share has blinked — the
card stays on the file it is already running rather than adopting the
unversioned fallback path, which would not exist. Only when there is nothing to
keep does the fallback go through, so a genuinely missing script is still
reported.

## 1.3.0

Logs are kept permanently on disk. Every line streamed from a script is
appended to `logs/<id>.log` next to the manager, in addition to the live panel,
so history survives closing the manager.

The panel is a view of recent activity, not the record. It held 500 lines and
nothing else existed, which worked out to roughly an hour of a ten-minute
poller before the earliest lines were discarded, and there was no way to look
back at a fault once it had scrolled away. Disk lines carry the full date
rather than just the time, since a file spanning weeks needs it.

A file is rolled over to `<id>.log.1`, `.2`, and so on once it passes
`LOG_ROLLOVER_BYTES` (10 MB). Parts are never deleted, so nothing is lost; the
numbering runs oldest-last, matching the usual convention. The panel buffer is
raised from 500 to 5,000 lines now that the disk file is the real record.

A new COPY button on each card puts the whole on-disk log, every rolled part
included and oldest first, on the clipboard. The button confirms with a brief
COPIED and reports the size, so a large paste is not a surprise.

## 1.2.0

Morning and Evening reports are started by the Manager itself at the times in
their "schedule" config (08:00 / 22:30), replacing Windows Task Scheduler. Runs
missed while the Manager was closed are skipped. START ALL now leaves scheduled
reports alone, and their cards show a grey light and the next run time while
idle.

## 1.1.0  (originally 1.4)

Process manager with start, stop and restart controls, per-process log tailing,
uptime, and status indicators. Discovers the highest-numbered script in each
configured folder at startup.

