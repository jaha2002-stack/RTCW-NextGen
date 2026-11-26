#!/usr/bin/env bash
set -euo pipefail

log=$1
shift
xdpyinfo >/dev/null
stdbuf -oL -eL "$@" &
engine_pid=$!
trap 'kill "$engine_pid" 2>/dev/null || true' EXIT

wait_for_frame() {
    local size=$1
    for _ in {1..100}; do
        if grep -Fxq "Renderer smoke frame $size" "$log"; then
            return 0
        fi
        kill -0 "$engine_pid" 2>/dev/null || break
        sleep 0.08
    done
    echo "Renderer never submitted a $size frame" >&2
    return 1
}

wait_for_frame 640x480
window=$(xdotool search --onlyvisible --class '^RBDoom3BFG$')
xdotool windowsize --sync "$window" 704 512
wait_for_frame 704x512
xdotool windowfocus --sync "$window"
xdotool key Escape
wait "$engine_pid"
trap - EXIT
