#!/usr/bin/env bash
# start_ollama.sh — start ollama serve on the first free port, print "PID PORT".
# Exits non-zero if no free port works or the server fails to become ready.

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# Settings

# Set bash options for safety: exit on error (-e), treat unset variables as errors (-u), and fail on pipe errors (-o pipefail).
set -euo pipefail

BIND_ADDR="${OLLAMA_BIND_ADDR:-127.0.0.1}"
START_PORT="${OLLAMA_START_PORT:-11434}"	# default ollama port
PORT_TRIES="${OLLAMA_PORT_TRIES:-100}"      # how many ports to scan from START_PORT
LOG_FILE="${OLLAMA_LOG:-/tmp/ollama.log}"
TIMEOUT="${OLLAMA_START_TIMEOUT:-30}"		# seconds to wait for readiness per port
# Note that this syntax mean s "use the value of the environment variable if set, otherwise use the default value".

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

# Return 0 if the TCP port is free, 1 if something is listening.
port_is_free() {
    local port="$1"
    # bash /dev/tcp: a successful connect means something is listening (busy).
    if (exec 3<>"/dev/tcp/${BIND_ADDR}/${port}") 2>/dev/null; then
        exec 3>&- 3<&-   # close the probe connection
        return 1
    fi
    return 0
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

for ((p = START_PORT; p < START_PORT + PORT_TRIES; p++)); do
    if ! port_is_free "$p"; then
        echo "port ${p} busy, trying next" >&2
        continue
    fi

    HOST="${BIND_ADDR}:${p}"

    # Launch detached so it survives this script exiting.
	# nohup is used to ignore SIGHUP (it allows the process to continue running after the script exits).
    OLLAMA_HOST="${HOST}" nohup ollama serve >"${LOG_FILE}" 2>&1 &
    PID=$!

    # Poll the API until it answers or we time out.
    ready=0
    for ((i = 0; i < TIMEOUT; i++)); do
        if curl -fsS "http://${HOST}/api/version" >/dev/null 2>&1; then
            ready=1
            break
        fi
        # Process died — likely lost a port race; move to the next port.
        if ! kill -0 "${PID}" 2>/dev/null; then
            break
        fi
        sleep 1
    done

    if [[ "$ready" -eq 1 ]]; then
        echo "${PID} ${p}"      # stdout: "PID PORT", for callers to capture
        exit 0
    fi

    # Clean up this attempt before trying the next port.
    echo "ollama failed to start on ${HOST}; see ${LOG_FILE}" >&2
    kill "${PID}" 2>/dev/null || true
    wait "${PID}" 2>/dev/null || true
done

echo "no free/working port found in range ${START_PORT}-$((START_PORT + PORT_TRIES - 1)); see ${LOG_FILE}" >&2
exit 1
