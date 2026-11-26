# Сборка и проверки Phase P00

## Windows x64

```powershell
pwsh -File scripts/build-windows.ps1
python -B scripts/test-project.py --rbdmap build-windows/tools/compilers/Release/rbdmap.exe
python scripts/package-windows.py --out build-windows/artifacts
```

Сборка использует Visual Studio 2022 с MSVC 14.44 и Windows SDK 10.0.26100.0. Скрипт проверяет SHA-256 дистрибутивов CMake и ISPC. Шейдеры DXIL компилируются как зависимость движка. Для диагностики доступен `-Configuration Debug`. ZIP использует Release.

## Linux в подготовленной облачной среде

```bash
cd /workspace/RTCW-NextGen
tool_dir=/workspace/scratch/rtcw-tools
prefix="$tool_dir/prefix/usr"
export PATH="$prefix/bin:$tool_dir/dxc/bin:$PATH"
export LD_LIBRARY_PATH="$prefix/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
cmake -S neo -B build-cloud -DCMAKE_BUILD_TYPE=Release -DFFMPEG=OFF -DBINKDEC=ON \
    -DCOMPILE_COMMANDS=ON -DCMAKE_PREFIX_PATH="$prefix" -DDXC_CUSTOM_PATH="$tool_dir/dxc/bin"
cmake --build build-cloud --parallel 4
python3 -B scripts/test-project.py --rbdmap build-cloud/tools/compilers/rbdmap
```

Штатный CMake движка не регистрирует CTest. `scripts/test-project.py` покрывает упаковку и запуск `rbdmap` на исходной синтетической карте. Для полной проверки требуется `--rbdmap`.

После сборки `bash scripts/smoke-renderer-linux.sh` запускает синтетический режим на Vulkan с Mesa llvmpipe и Xvfb. Скрипт проверяет завершение процесса и красную и синюю области в PNG. Вариант `bash scripts/smoke-renderer-linux.sh --window-events` требует `xdotool`, изменяет размер окна с 640×480 до 704×512, нажимает Escape и проверяет размер захваченного кадра. Для проверки с установленным слоем Vulkan validation задайте `RTCW_SMOKE_VK_VALIDATION=2` и при необходимости укажите путь к JSON слоя через `VK_LAYER_PATH`. Запуск использует временный каталог с двумя синтетическими ресурсами и скомпилированными шейдерами.

## Игровые ресурсы

- Для сборки и синтетических тестов Phase P00 достаточно checkout и его подмодулей.
- Для полного запуска текущего upstream RBDOOM нужен каталог `base/` лицензированной PC-версии **DOOM 3 BFG Edition** (в том числе штатные файлы `.resources`) и пакеты `base/*.pk4` релиза RBDOOM-3-BFG 1.6.0 по [README движка](../../README.md#installation). Облачный запуск с программным Vulkan дошёл до отсутствующего `newfonts/Arial_Narrow/48.dat` и остановился. Каталог можно использовать на компьютере владельца для smoke-теста базового движка.
- Для сверки форматов и проверки совместимости с одиночной кампанией **Return to Castle Wolfenstein** нужен каталог `Main/` оригинальной лицензированной PC-установки: `pak0.pk3`, `sp_pak1.pk3`, `sp_pak2.pk3`, `sp_pak3.pk3`. Состав указан в [инструкции iortcw на закреплённой ревизии](https://github.com/iortcw/iortcw/tree/438e7d413b5f7277187c35b032eb0ef9093ae778#installation). Достаточно держать файлы в существующей локальной установке. При необходимости проверяем на месте содержимое и контрольные суммы.

Команда `python scripts/rtcw_data.py "<путь к установке RTCW>"` читает каталог четырёх PK3, сообщает о недостающих или нечитаемых файлах и ищет запись `maps/escape1.bsp`. Проверка работает на месте. Она читает метаданные ZIP, поэтому не проверяет содержимое BSP или CRC файлов внутри архивов.

Команда `python scripts/rtcw_data.py "<путь к установке RTCW>" --locate maps/escape1.bsp` определяет источник ресурса внутри одного каталога `Main`. Для одиночного режима архивы `mp_*` пропускаются, имена `sp_*` сортируются как `zz_*`, поздний по сортировке PK3 имеет приоритет, а отдельный файл ищется после архивов. Правило сверено с [FS_AddGameDirectory в закреплённом iortcw SP](https://github.com/iortcw/iortcw/blob/438e7d413b5f7277187c35b032eb0ef9093ae778/SP/code/qcommon/files.c#L3197).
