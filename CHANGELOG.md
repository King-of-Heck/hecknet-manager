# Changelog

Version numbers were reassigned for release (the old scheme bumped the
minor version for bugfixes); the original number is in parentheses. The
notes below are from each script's own version history.

Only one source file was retained. Its own history documents an initial release and a second version adding version auto-discovery; the published 1.1.0 corresponds to that second version. Files labelled 1.2 through 1.4 were not kept, and no changes for them were ever recorded.

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

