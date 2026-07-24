#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1
    pwd
)"

cd "$SCRIPT_DIR"

if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created teams/team4/.env from .env.example"
fi

if ! docker network inspect polylife_net >/dev/null 2>&1; then
    echo "The shared network polylife_net does not exist."
    echo "Start the root Core service first:"
    echo "  docker compose -f docker-compose.yml up -d core"
    exit 1
fi

docker compose up --build