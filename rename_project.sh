#!/bin/bash
set -euo pipefail

if [ -z "${1:-}" ]; then
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

# Function to convert snake_case to PascalCase
to_pascal_case() {
    echo "$1" | sed -r 's/(^|_)([a-z])/\U\2/g'
}

validate_detected_name() {
    local label="$1"
    local value="$2"
    local pattern="$3"

    if [[ -z "$value" ]]; then
        echo "Error: $label is empty"
        exit 1
    fi

    if [[ ! "$value" =~ $pattern ]]; then
        echo "Error: Refusing to continue because detected $label '$value' looks invalid"
        exit 1
    fi
}

replace_literal_in_file() {
    local file="$1"
    local search="$2"
    local replacement="$3"
    local escaped_search
    local escaped_replacement
    local tmp_file

    escaped_search=$(printf '%s' "$search" | sed 's/[.[\\*^$()+?{|]/\\&/g')
    escaped_replacement=$(printf '%s' "$replacement" | sed 's/[&|\\]/\\&/g')
    tmp_file=$(mktemp "${file}.XXXXXX")

    if ! sed "s|$escaped_search|$escaped_replacement|g" "$file" > "$tmp_file"; then
        rm -f "$tmp_file"
        return 1
    fi
    chmod --reference="$file" "$tmp_file"
    mv "$tmp_file" "$file"
}

replace_literal_in_files() {
    local search="$1"
    local replacement="$2"

    while IFS= read -r -d '' file; do
        # Skip binary files to avoid corrupting assets.
        if ! grep -Iq . "$file"; then
            continue
        fi

        replace_literal_in_file "$file" "$search" "$replacement"
    done < <(find . -type f "${EXCLUDES[@]}" -print0)
}

OLD_PASCAL_NAME=$(to_pascal_case "$OLD_PACKAGE_NAME")
NEW_PASCAL_NAME=$(to_pascal_case "$NEW_PACKAGE_NAME")

validate_detected_name "package name" "$OLD_PACKAGE_NAME" '^[a-z][a-z0-9_]*$'
validate_detected_name "project name" "$OLD_PROJECT_NAME" '^[a-z0-9][a-z0-9-]*$'
validate_detected_name "PascalCase package name" "$OLD_PASCAL_NAME" '^[A-Z][A-Za-z0-9]+$'
validate_detected_name "new package name" "$NEW_PACKAGE_NAME" '^[a-z][a-z0-9_]*$'
validate_detected_name "new project name" "$NEW_PROJECT_NAME" '^[a-z0-9][a-z0-9-]*$'
validate_detected_name "new PascalCase package name" "$NEW_PASCAL_NAME" '^[A-Z][A-Za-z0-9]+$'

echo "---"
echo "Renaming project from '$OLD_PROJECT_NAME' ($OLD_PACKAGE_NAME / $OLD_PASCAL_NAME) to '$NEW_PROJECT_NAME' ($NEW_PACKAGE_NAME / $NEW_PASCAL_NAME)"
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
replace_literal_in_files "$OLD_PACKAGE_NAME" "$NEW_PACKAGE_NAME"

# Replace project name (todo-api)
replace_literal_in_files "$OLD_PROJECT_NAME" "$NEW_PROJECT_NAME"

# Replace PascalCase name (TodoApi)
replace_literal_in_files "$OLD_PASCAL_NAME" "$NEW_PASCAL_NAME"

echo "Formatting the code..."
uv run poe format

echo "---"
echo "Project successfully renamed to '$NEW_PROJECT_NAME'!"
echo "This script is intended for one-time use and can now be deleted"
echo "---"
