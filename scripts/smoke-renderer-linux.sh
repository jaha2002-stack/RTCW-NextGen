#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
tool_dir=/workspace/scratch/rtcw-tools
prefix="$tool_dir/prefix/usr"
export PATH="$prefix/bin:$PATH"
export LD_LIBRARY_PATH="$prefix/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

run_dir=$(mktemp -d)
printf 'Renderer smoke output: %s\n' "$run_dir"
mkdir -p "$run_dir/fixture/base/materials" "$run_dir/fixture/base/textures" "$run_dir/save" "$run_dir/runtime" "$run_dir/cache" "$run_dir/data"
chmod 700 "$run_dir/runtime"
printf '// Minimal configuration for the synthetic renderer fixture.\n' > "$run_dir/fixture/base/default.cfg"
cp "$root/tests/fixtures/renderer-smoke.mtr" "$run_dir/fixture/base/materials/"
cp "$root/tests/fixtures/renderer_smoke_white.tga" "$run_dir/fixture/base/textures/"
ln -s "$root/base/renderprogs2" "$run_dir/fixture/base/renderprogs2"

export SDL_VIDEODRIVER=x11
export VK_DRIVER_FILES="$prefix/share/vulkan/icd.d/lvp_icd.json"
export XDG_RUNTIME_DIR="$run_dir/runtime" XDG_CACHE_HOME="$run_dir/cache" XDG_DATA_HOME="$run_dir/data"
validation=${RTCW_SMOKE_VK_VALIDATION:-1}
mode=1
fixture="$run_dir/fixture"
preview_args=()
launcher=(sh -c 'xdpyinfo >/dev/null && exec "$@"' sh)
if [[ "${1:-}" == --window-events && "$#" == 1 ]]; then
    mode=2
    launcher=(bash "$root/tests/renderer-smoke-window-events.sh" "$run_dir/engine.log")
elif [[ "${1:-}" == --native-level && "$#" == 1 ]]; then
    mode=2
    launcher=(bash "$root/tests/renderer-smoke-window-events.sh" "$run_dir/engine.log")
    fixture="$run_dir/native-level"
    cp -R "$root/tests/fixtures/native-level" "$run_dir/assets"
    mkdir -p "$run_dir/assets/textures"
    cp "$root/tests/fixtures/renderer_smoke_white.tga" "$run_dir/assets/textures/"
    python3 -B "$root/scripts/compile-native-level.py" "$root/tests/fixtures/cloud_room.map" \
        --rbdmap "$root/build-cloud/tools/compilers/rbdmap" --assets "$run_dir/assets" --out "$fixture" --aas aas48
    ln -s "$root/base/renderprogs2" "$fixture/base/renderprogs2"
    preview_args=(+set com_nativeMapPreview maps/level)
elif (( $# != 0 )); then
    echo "Usage: $0 [--window-events | --native-level]" >&2
    exit 2
fi
timeout --kill-after=5s 30s xvfb-run -a -e "$run_dir/xvfb.log" -s '-screen 0 800x600x24 -noreset' \
    "${launcher[@]}" "$root/build-cloud/RBDoom3BFG" \
    +set fs_basepath "$fixture" +set fs_savepath "$run_dir/save" \
    +set r_fullscreen 0 +set r_windowWidth 640 +set r_windowHeight 480 \
    +set s_noSound 1 +set logFile 2 +set com_renderSmoke "$mode" +set r_useValidationLayers "$validation" \
    "${preview_args[@]}" > "$run_dir/engine.log" 2>&1

test -s "$run_dir/save/base/qconsole.log"
if [[ "$validation" == 2 ]]; then
    grep -F 'VK_LAYER_KHRONOS_validation' "$run_dir/engine.log"
    if grep -E 'Validation Error|VUID-' "$run_dir/engine.log"; then
        exit 1
    fi
fi
if (( ${#preview_args[@]} )); then
    grep -F 'Native map preview loaded maps/level at -40.0 0.0 48.0' "$run_dir/engine.log"
    grep -Fx 'Native collision forward fraction=0.6553 endpoint=127.75 0.00 48.00' "$run_dir/engine.log"
    grep -Fx 'Native collision down fraction=0.3730 endpoint=-40.00 0.00 0.25' "$run_dir/engine.log"
    grep -Fx 'Native collision nearby fraction=1.0000 endpoint=-8.00 0.00 48.00' "$run_dir/engine.log"
    grep -F 'Native map preview finished' "$run_dir/engine.log"
    grep -Fx 'Renderer smoke received Escape' "$run_dir/engine.log"
    image="$run_dir/save/base/screenshots/native-map-preview.png"
    [[ $(magick identify -format '%wx%h' "$image") == 704x512 ]]
    pixels=$(magick "$image" -format '%[fx:p{w/2,h/2}.r>2*p{w/2,h/2}.b && p{w/2,h/2}.r>0.15 && p{w/16,h/2}.b>2*p{w/16,h/2}.r && p{w/16,h/2}.b>0.15]' info:)
    if [[ "$pixels" != 1 ]]; then
        echo "Expected the red panel ahead and a blue wall to the side in $image" >&2
        exit 1
    fi
    printf 'Verified native world geometry and materials in %s\n' "$image"
    exit 0
fi
grep -F 'Synthetic renderer smoke test finished' "$run_dir/engine.log"
image="$run_dir/save/base/screenshots/renderer-smoke.png"
if [[ "$mode" == 2 ]]; then
    grep -Fx 'Renderer smoke received Escape' "$run_dir/engine.log"
    [[ $(magick identify -format '%wx%h' "$image") == 704x512 ]]
fi
pixels=$(magick "$image" -format '%[fx:p{w/4,h/2}.r>0.8 && p{w/4,h/2}.b<0.2 && p{3*w/4,h/2}.r<0.2 && p{3*w/4,h/2}.b>0.8]' info:)
if [[ "$pixels" != 1 ]]; then
    echo "Expected distinct red and blue regions in $image" >&2
    exit 1
fi
printf 'Verified renderer pixels in %s\n' "$image"
