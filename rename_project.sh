#!/bin/bash
set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <new-project-name>"
  echo "Error: No project name supplied"
  exit 1
fi

if [ ! -d "todo_api" ]; then
    echo "Error: 'todo_api' directory not found"
    echo "Please run this script from the root of the project on a fresh template"
    exit 1
fi

OLD_PACKAGE_NAME="todo_api"
OLD_PROJECT_NAME="todo-api"

INPUT_NAME=$1
NEW_PACKAGE_NAME=$(echo "$INPUT_NAME" | sed 's/-/_/g')
NEW_PROJECT_NAME=$(echo "$INPUT_NAME" | sed 's/_/-/g')

echo "---"
echo "Renaming project from '$OLD_PACKAGE_NAME' to '$NEW_PACKAGE_NAME'"
echo "---"

echo "Renaming directory '$OLD_PACKAGE_NAME' to '$NEW_PACKAGE_NAME'"
mv "$OLD_PACKAGE_NAME" "$NEW_PACKAGE_NAME"

echo "Replacing package name references in files..."
find . -type f \
    -not -path "./.git/*" \
    -not -path "./.venv/*" \
    -not -path "./.ruff_cache/*" \
    -not -path "./.mypy_cache/*" \
    -not -path "./.pytest_cache/*" \
    -not -path "./*.egg-info/*" \
    -not -name "rename_project.sh" \
    -print0 | xargs -0 sed -i "s/\b$OLD_PACKAGE_NAME\b/$NEW_PACKAGE_NAME/g"

echo "Updating project name in pyproject.toml..."
sed -i "s/name = \"$OLD_PROJECT_NAME\"/name = \"$NEW_PROJECT_NAME\"/g" pyproject.toml

echo "Formatting the code..."
uv run poe format

echo "---"
echo "Project successfully renamed to '$NEW_PACKAGE_NAME'!"
echo "This script is intended for one-time use and can now be deleted"
echo "---"