#!/usr/bin/env bash
# Sets up and opens Remotion Studio on macOS.
set -euo pipefail

REPO="https://github.com/pipobilal78-alnorsk/Bilal-AlGharawi.git"
BRANCH="claude/add-remotion"
DIR="$HOME/Bilal-AlGharawi"

if ! command -v node >/dev/null 2>&1 || ! command -v git >/dev/null 2>&1; then
  if ! command -v brew >/dev/null 2>&1; then
    echo "Homebrew is required: https://brew.sh" >&2
    exit 1
  fi
  brew install node git
fi

if [ -d "$DIR/.git" ]; then
  git -C "$DIR" fetch origin "$BRANCH"
  git -C "$DIR" checkout "$BRANCH"
  git -C "$DIR" pull origin "$BRANCH"
else
  git clone --branch "$BRANCH" "$REPO" "$DIR"
fi

cd "$DIR"
npm install
mkdir -p remotion/public
[ -f remotion/public/source.mp4 ] || echo "Note: put your source video at $DIR/remotion/public/source.mp4 for the 'Social' composition."
npm run remotion:studio
