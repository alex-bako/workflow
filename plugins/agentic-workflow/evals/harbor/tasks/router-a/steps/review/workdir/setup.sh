#!/bin/bash
# Runs before the reviewer starts. Harbor empties /tests only before a verifier
# runs, so the previous step's rubric is still there: remove it, and start this
# step's call logs fresh.
find /tests /logs/verifier -mindepth 1 -delete 2>/dev/null
mv -f /var/log/git-calls.log /var/log/git-calls.packet.log 2>/dev/null
mv -f /var/log/gh-calls.log /var/log/gh-calls.packet.log 2>/dev/null
rm -f /app/setup.sh
exit 0
