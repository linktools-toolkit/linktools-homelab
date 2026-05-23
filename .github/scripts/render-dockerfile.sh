#!/bin/bash
# Usage: render-dockerfile.sh <Dockerfile>
# Replaces lines matching "# INCLUDE <fragment>" with the fragment file content.
set -e

DOCKERFILE="$1"
FRAGMENTS_DIR="$(cd "$(dirname "$0")/../dockerfiles/fragments" && pwd)"

if [ -z "$DOCKERFILE" ]; then
    echo "Usage: $0 <Dockerfile>" >&2
    exit 1
fi

while IFS= read -r line; do
    if [[ "$line" =~ ^#\ INCLUDE\ (.+)$ ]]; then
        fragment="${BASH_REMATCH[1]}"
        fragment_path="${FRAGMENTS_DIR}/${fragment}"
        if [ ! -f "$fragment_path" ]; then
            echo "Fragment not found: $fragment_path" >&2
            exit 1
        fi
        cat "$fragment_path"
    else
        printf '%s\n' "$line"
    fi
done < "$DOCKERFILE"
