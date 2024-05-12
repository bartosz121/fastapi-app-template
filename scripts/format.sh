#!/bin/sh -e

export PREFIX=""
if [ -d '.venv' ]; then
    export PREFIX=".venv/bin/"
fi
export TARGET="todo_api tests"

set -x

${PREFIX}ruff check --fix $TARGET
${PREFIX}ruff format $TARGET