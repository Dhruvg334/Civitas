#!/usr/bin/env bash
set -euo pipefail
[ -f .env ] || cp .env.example .env
npm install
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e 'apps/api[dev]' -e 'services/workflow[dev]' -e 'services/knowledge[dev]' -e 'services/evaluation[dev]' -e 'services/ml[dev]'
echo "Civitas local setup completed."
