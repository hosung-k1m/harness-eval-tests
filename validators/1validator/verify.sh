#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

ensure_dependencies() {
    # 1validator only requires standard POSIX/bash shell environment and core file utilities
    return 0
}

ensure_dependencies

if [ -f hi.txt ] || [[ -f hi.txt ]]; then
    echo "exists"
    exit 0
fi

echo "not exists"
exit 1
