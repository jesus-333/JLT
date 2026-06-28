#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# setup_github_copilot_backend.sh
#
# Writes the JLT GitHub Copilot config file in the current directory and
# registers it with `jlt`.
#
# The Copilot backend now runs on top of the official `github-copilot-sdk`,
# which performs the GitHub -> Copilot token exchange (and refresh) internally.
# We therefore only need to hand it an ordinary GitHub token : no more
# short-lived `copilot_internal/v2/token` bearer token to fetch and refresh.
#
# Requirements:
#   - GitHub CLI (`gh`) installed and authenticated (`gh auth login`)
#   - `jlt` available on PATH, installed with the Copilot extra :
#         pip install jlt[github_copilot]
#   - The Copilot runtime downloaded once (auto-downloaded on first use too) :
#         python -m copilot download-runtime
# -----------------------------------------------------------------------------

set -euo pipefail

BACKEND_NAME="copilot_student"
OUT_FILE="$(pwd)/copilot_backend.toml"

# -------------------------------------------------------
# 1. Check dependencies
# -------------------------------------------------------
for cmd in gh jlt; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "ERROR: '$cmd' is not installed or not on PATH."
        exit 1
    fi
done

# -------------------------------------------------------
# 2. Grab the GitHub token (the SDK handles the Copilot exchange)
# -------------------------------------------------------
echo "→ Reading GitHub token from 'gh auth token' ..."
GITHUB_TOKEN="$(gh auth token)"

if [[ -z "$GITHUB_TOKEN" ]]; then
    echo "ERROR: could not read a GitHub token. Run 'gh auth login' first."
    exit 1
fi

# -------------------------------------------------------
# 3. Write the toml config file
# -------------------------------------------------------
echo "→ Writing config to '${OUT_FILE}' ..."

cat > "$OUT_FILE" << TOML
backend_type = "github_copilot"
api_key      = "$GITHUB_TOKEN"
model        = "gpt-4o"
TOML

echo "   api_key = \"${GITHUB_TOKEN:0:8}...${GITHUB_TOKEN: -4}\""

# -------------------------------------------------------
# 4. Make sure the Copilot runtime is available
# -------------------------------------------------------
echo "→ Ensuring the Copilot runtime is downloaded ..."
python -m copilot download-runtime || \
    echo "   (download will be retried automatically on first use)"

# -------------------------------------------------------
# 5. Register with jlt
# -------------------------------------------------------
echo "→ Registering backend '${BACKEND_NAME}' with jlt ..."
jlt backend config --backend_name "$BACKEND_NAME" --path_file "$OUT_FILE"
jlt backend activate --backend_name "$BACKEND_NAME"
echo "   Backend '${BACKEND_NAME}' is now active."

echo ""
echo "✓ Done. The github-copilot-sdk refreshes the Copilot token for you, so"
echo "  there is no ~30 minute expiry to re-run for anymore."
