#!/usr/bin/env bash
set -euo pipefail

run_dir=$1
shift
log="$run_dir/engine.log"
image="$run_dir/save/base/screenshots/relay-station.png"
stdbuf -oL "$@" &
game=$!
trap 'kill "$game" 2>/dev/null || true' EXIT

wait_for() {
    local message=$1 occurrences=${2:-1}
    for ((attempt=0; attempt<100; attempt++)); do
        if (( $(grep -Fc "$message" "$log" || true) >= occurrences )); then
            return
        fi
        kill -0 "$game" 2>/dev/null || break
        sleep 0.1
    done
    printf 'Relay milestone missing: %s\n' "$message" >&2
    return 1
}

wait_for 'Relay: ready'
window=$(xdotool search --onlyvisible --pid "$game" | head -1)
xdotool windowfocus --sync "$window"
xdotool key F12
wait_for 'Relay: capture at'
for ((attempt=0; attempt<30; attempt++)); do
    if [[ -s "$image" ]]; then break; fi
    sleep 0.1
done
cp "$image" "$run_dir/relay-entry.png"

xdotool key space
wait_for 'Relay: jumped'
sleep 0.6
xdotool keydown w
wait_for 'Relay: stepped up'
sleep 0.6
xdotool keydown c
wait_for 'Relay: crouched'
wait_for 'Relay: power cell collected'
xdotool keyup c
wait_for 'Relay: closed gate blocked movement'
xdotool keyup w key e
wait_for 'Relay: gate opened'

xdotool keydown w
wait_for 'Relay: ladder engaged'
wait_for 'Relay: drone arrived'
wait_for 'Relay: level complete'
xdotool keyup w key F12
wait_for 'Relay: capture at' 2
for ((attempt=0; attempt<30; attempt++)); do
    if [[ -s "$image" && "$image" -nt "$run_dir/relay-entry.png" ]]; then break; fi
    sleep 0.1
done
[[ -s "$image" && "$image" -nt "$run_dir/relay-entry.png" ]]
cp "$image" "$run_dir/relay-complete.png"

xdotool key r
wait_for 'Relay: reset' 2
xdotool keydown w
wait_for 'Relay: stepped up' 2
xdotool keyup w key Escape
wait "$game"
grep -Fq 'Relay Station finished' "$log"
if grep -Eq 'signal caught|Segmentation fault|Sys_Error' "$log"; then
    exit 1
fi
