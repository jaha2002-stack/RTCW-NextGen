#!/usr/bin/env bash
set -euo pipefail

log=$1
shift
xdpyinfo >/dev/null
stdbuf -oL -eL "$@" &
engine_pid=$!
trap 'kill "$engine_pid" 2>/dev/null || true' EXIT

wait_for_event() {
    local message="Signal Room: $1"
    local count=${2:-1}
    for _ in {1..180}; do
        if (( $(grep -Fxc "$message" "$log" || true) >= count )); then
            return 0
        fi
        kill -0 "$engine_pid" 2>/dev/null || break
        sleep 0.06
    done
    echo "Expected gameplay event: $message (count $count)" >&2
    return 1
}

wait_for_event ready
window=$(xdotool search --onlyvisible --class '^RBDoom3BFG$')
xdotool windowfocus --sync "$window"

# The central obstacle must stop forward movement before any module is reached.
xdotool keydown w
wait_for_event 'movement blocked'
xdotool keyup w key r
wait_for_event reset 2

play_round() {
    local round=$1
    xdotool keydown a
    wait_for_event 'module 1/3 collected' "$round"
    # Move past the clearance needed to avoid the next obstacle.
    sleep 0.15
    xdotool keyup a keydown w
    wait_for_event 'module 2/3 collected' "$round"
    wait_for_event 'module 3/3 collected' "$round"
    wait_for_event 'movement blocked' "$(( round + 1 ))"
    xdotool keyup w keydown d
    wait_for_event 'exit reached' "$round"
    xdotool keyup d
}

play_round 1
xdotool key r
wait_for_event reset 3
play_round 2
xdotool key Escape
wait "$engine_pid"
trap - EXIT
