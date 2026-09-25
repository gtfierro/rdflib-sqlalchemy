#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: ./publish.sh [--testpypi] [--build-only] [--skip-existing]

Builds source and wheel distributions of the current commit with `uv build`,
checks them with twine, and uploads them with `uv publish`.

The build runs on a clean export of HEAD (`git archive`), so untracked or
uncommitted files in the working tree can never end up in a release.

Options:
  --testpypi      Upload to TestPyPI instead of PyPI
  --build-only    Build and validate artifacts, but do not upload them
  --skip-existing Skip files that are already on the index
  --help          Show this help text

Authentication:
  Set UV_PUBLISH_TOKEN=<your token>, or pass nothing and uv will prompt
  for credentials (or use the keyring, if configured).
EOF
}

publish_url="https://upload.pypi.org/legacy/"
check_url="https://pypi.org/simple/"
build_only=0
skip_existing=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --testpypi)
            publish_url="https://test.pypi.org/legacy/"
            check_url="https://test.pypi.org/simple/"
            shift
            ;;
        --build-only)
            build_only=1
            shift
            ;;
        --skip-existing)
            skip_existing=1
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

for cmd in git uv; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Missing required command: $cmd" >&2
        exit 1
    fi
done

repo_root=$(git rev-parse --show-toplevel)
cd "$repo_root"

if [[ -n $(git status --porcelain --untracked-files=no) ]]; then
    echo "Uncommitted changes to tracked files; commit or stash them first." >&2
    exit 1
fi

src=$(mktemp -d)
trap 'rm -rf "$src"' EXIT
git archive HEAD | tar -x -C "$src"

rm -rf dist
uv build --no-sources --out-dir dist "$src"
uvx twine check --strict dist/*

if [[ $build_only -eq 1 ]]; then
    echo "Build complete. Artifacts are in dist/."
    exit 0
fi

publish_args=(--publish-url "$publish_url")

if [[ $skip_existing -eq 1 ]]; then
    publish_args+=(--check-url "$check_url")
fi

uv publish "${publish_args[@]}" dist/*
