#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# setup_copilot_backend.sh
#
# Fetches a short-lived GitHub Copilot bearer token, writes (or refreshes) the
# JLT config file in the current directory, and registers it with `jlt`.
#
# Requirements:
#   - GitHub CLI (`gh`) installed and authenticated (`gh auth login`)
#   - `curl`, `jq`, and `jlt` available on PATH
# -----------------------------------------------------------------------------

set -euo pipefail

BACKEND_NAME="copilot_student"
OUT_FILE="$(pwd)/copilot_backend.toml"

# -------------------------------------------------------
# 1. Check dependencies
# -------------------------------------------------------
for cmd in gh curl jq jlt; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "ERROR: '$cmd' is not installed or not on PATH."
        exit 1
    fi
done

# -------------------------------------------------------
# 2. Exchange GitHub OAuth token for a Copilot bearer token
# -------------------------------------------------------
echo "→ Fetching Copilot bearer token ..."
RESPONSE_FILE="$(mktemp)"
curl -H "Authorization: token $(gh auth token)" \
     -H "Accept: application/json" \
     "https://api.github.com/copilot_internal/v2/token" \
     -o "$RESPONSE_FILE"

# The response is JSON; use jq to extract the token field
COPILOT_TOKEN="$(jq -r '.token' "$RESPONSE_FILE")"
rm "$RESPONSE_FILE"

if [[ -z "$COPILOT_TOKEN" ]]; then
    echo "ERROR: Copilot token not found in the API response."
    exit 1
fi

# -------------------------------------------------------
# 3. Write the toml config file
# -------------------------------------------------------
echo "→ Writing config to '${OUT_FILE}' ..."

cat > "$OUT_FILE" << TOML
backend_type = "github_copilot"
api_key      = "$COPILOT_TOKEN"
model        = "gpt-4o"
TOML

echo "   api_key = \"${COPILOT_TOKEN:0:8}...${COPILOT_TOKEN: -4}\""

# -------------------------------------------------------
# 4. Register with jlt
# -------------------------------------------------------
echo "→ Registering backend '${BACKEND_NAME}' with jlt ..."
jlt backend config --backend_name "$BACKEND_NAME" --path_file "$OUT_FILE"
jlt backend activate --backend_name "$BACKEND_NAME"
echo "   Backend '${BACKEND_NAME}' is now active."

echo ""
echo "⚠  Copilot tokens expire in ~30 minutes. Re-run to refresh."
