#!/bin/bash
set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <new-project-name>"
  echo "Error: No project name supplied"
  exit 1
fi

# Detect current package name (dir containing main.py)
OLD_PACKAGE_NAME=$(find . -maxdepth 2 -name "main.py" -exec dirname {} + | head -n 1 | sed 's|./||')

if [ -z "$OLD_PACKAGE_NAME" ] || [ ! -d "$OLD_PACKAGE_NAME" ]; then
    echo "Error: Could not detect the primary package directory (containing 'main.py')"
    exit 1
fi

# Detect current project name from pyproject.toml
OLD_PROJECT_NAME=$(grep '^name = ' pyproject.toml | head -n 1 | cut -d'"' -f2)

if [ -z "$OLD_PROJECT_NAME" ]; then
    echo "Error: Could not detect project name from pyproject.toml"
    exit 1
fi

INPUT_NAME=$1
NEW_PACKAGE_NAME=$(echo "$INPUT_NAME" | sed 's/-/_/g' | tr '[:upper:]' '[:lower:]')
NEW_PROJECT_NAME=$(echo "$INPUT_NAME" | sed 's/_/-/g' | tr '[:upper:]' '[:lower:]')

echo "---"
echo "Renaming project from '$OLD_PROJECT_NAME' ($OLD_PACKAGE_NAME) to '$NEW_PROJECT_NAME' ($NEW_PACKAGE_NAME)"
echo "---"

if [ "$OLD_PACKAGE_NAME" != "$NEW_PACKAGE_NAME" ]; then
    echo "Renaming directory '$OLD_PACKAGE_NAME' to '$NEW_PACKAGE_NAME'"
    mv "$OLD_PACKAGE_NAME" "$NEW_PACKAGE_NAME"
fi

echo "Replacing name references in files..."

export LC_ALL=C

EXCLUDES=(
    -not -path "./.git/*"
    -not -path "./.venv/*"
    -not -path "./.ruff_cache/*"
    -not -path "./.mypy_cache/*"
    -not -path "./.pytest_cache/*"
    -not -path "./*.egg-info/*"
    -not -name "rename_project.sh"
    -not -name "uv.lock"
    -not -name "logs.txt"
)

# Replace package name (todo_api)
find . -type f "${EXCLUDES[@]}" -print0 | xargs -0 sed -i "s/\b$OLD_PACKAGE_NAME\b/$NEW_PACKAGE_NAME/g"

# Replace project name (todo-api)
find . -type f "${EXCLUDES[@]}" -print0 | xargs -0 sed -i "s/$OLD_PROJECT_NAME/$NEW_PROJECT_NAME/g"

echo "Formatting the code..."
uv run poe format

echo "---"
echo "Project successfully renamed to '$NEW_PROJECT_NAME'!"
echo "This script is intended for one-time use and can now be deleted"
echo "---"