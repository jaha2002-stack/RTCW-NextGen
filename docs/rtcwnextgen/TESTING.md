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

## Игровые ресурсы

- Для сборки и синтетических тестов Phase P00 достаточно checkout и его подмодулей.
- Для полного запуска текущего upstream RBDOOM нужен каталог `base/` лицензированной PC-версии **DOOM 3 BFG Edition** (в том числе штатные файлы `.resources`) и пакеты `base/*.pk4` релиза RBDOOM-3-BFG 1.6.0 по [README движка](../../README.md#installation). Облачный запуск с программным Vulkan дошёл до отсутствующего `newfonts/Arial_Narrow/48.dat` и остановился. Каталог можно использовать на компьютере владельца для smoke-теста базового движка.
- Для сверки форматов и проверки совместимости с одиночной кампанией **Return to Castle Wolfenstein** нужен каталог `Main/` оригинальной лицензированной PC-установки: `pak0.pk3`, `sp_pak1.pk3`, `sp_pak2.pk3`, `sp_pak3.pk3`. Состав указан в [инструкции iortcw на закреплённой ревизии](https://github.com/iortcw/iortcw/tree/438e7d413b5f7277187c35b032eb0ef9093ae778#installation). Достаточно держать файлы в существующей локальной установке. При необходимости проверяем на месте содержимое и контрольные суммы.
