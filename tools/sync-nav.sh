#!/usr/bin/env bash
# Copy tools/nav.html and tools/footer.html into every page.
# Pass --check to report drift without writing (used by the test suite).
set -euo pipefail
cd "$(dirname "$0")/.."
exec python3 tools/sync_chrome.py "$@"
