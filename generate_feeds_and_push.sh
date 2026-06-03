#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"

echo "=== Generating feeds ==="
set +e
uv run python generate_feeds.py --no-cache --skip-unchanged
generate_exit=$?
set -e

if [ $generate_exit -ne 0 ]; then
    echo "=== Some feeds failed, continuing to commit any that succeeded ==="
fi

echo "=== Checking for feed changes ==="
if git diff --quiet -- feeds; then
    echo "No feed changes to commit."
    exit $generate_exit
fi

changed=$(git diff --name-only -- feeds | sed 's|feeds/||' | tr '\n' ' ' | sed 's/ $//')
echo "=== Changed feeds: $changed ==="

echo "=== Staging feeds ==="
git add feeds

echo "=== Committing ==="
git commit -m "chore: regenerate RSS feeds ($changed)"

echo "=== Pushing ==="
git push

exit $generate_exit
