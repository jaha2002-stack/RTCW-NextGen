# Сборка и проверки проекта

## Windows x64

```powershell
pwsh -File scripts/build-windows.ps1
python -B scripts/test-project.py --rbdmap build-windows/tools/compilers/Release/rbdmap.exe
python -B scripts/compile-native-level.py tests/fixtures/cloud_room.map --rbdmap build-windows/tools/compilers/Release/rbdmap.exe --assets tests/fixtures/native-level --out build-windows/native-level --aas aas48
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

## Нативный уровень

`scripts/compile-native-level.py` принимает авторский `brushDef3` или Valve 220 `.map` и каталог с собственными `materials/`, `textures/` и `def/`. Утилита компилирует `maps/level` в новом выходном каталоге, проверяет ожидаемые файлы и записывает `level-build.json` и `rbdmap.log`. Параметр `--aas aas48` требует `.aas48` и предполагает определение профиля в `def/`. Без `--aas` компилируются геометрия и коллизии.

`bash scripts/smoke-renderer-linux.sh --native-level` компилирует авторскую комнату, загружает `.proc` в `idRenderWorld`, проверяет материал стены из `info_player_start`, точечные трассы `.cm` в стену, в пол и через свободное пространство, изменение размера окна и штатный выход. С `RTCW_SMOKE_VK_VALIDATION=2` проверяются ошибки Vulkan validation. Исходники карты, материалы и настройки навигации находятся в `tests/fixtures/`.

Для собственного предпросмотра требуется декларация `_default`, материалы карты, `info_player_start` с `origin` и шейдеры собранного backend в `base/renderprogs2`. Готовый каталог уровня указывается в `fs_basepath`. Отдельный каталог для кадра и журнала указывается в `fs_savepath`. Включение `com_nativeMapPreview maps/level` показывает мир и сохраняет `base/screenshots/native-map-preview.png`. С `com_renderSmoke 2` можно изменить размер окна и закрыть его по Escape.

После сборки `bash scripts/smoke-renderer-linux.sh` запускает синтетический режим на Vulkan с Mesa llvmpipe и Xvfb. Скрипт проверяет завершение процесса и красную и синюю области в PNG. Вариант `bash scripts/smoke-renderer-linux.sh --window-events` требует `xdotool`, изменяет размер окна с 640×480 до 704×512, нажимает Escape и проверяет размер захваченного кадра. Для проверки с установленным слоем Vulkan validation задайте `RTCW_SMOKE_VK_VALIDATION=2` и при необходимости укажите путь к JSON слоя через `VK_LAYER_PATH`. Запуск использует временный каталог с двумя синтетическими ресурсами и скомпилированными шейдерами.

## Игровые ресурсы

- Для сборки и синтетических тестов Phase P00 достаточно checkout и его подмодулей.
- Для полного запуска текущего upstream RBDOOM нужен каталог `base/` лицензированной PC-версии **DOOM 3 BFG Edition** (в том числе штатные файлы `.resources`) и пакеты `base/*.pk4` релиза RBDOOM-3-BFG 1.6.0 по [README движка](../../README.md#installation). Облачный запуск с программным Vulkan дошёл до отсутствующего `newfonts/Arial_Narrow/48.dat` и остановился. Каталог можно использовать на компьютере владельца для smoke-теста базового движка.
- Для сверки форматов и проверки совместимости с одиночной кампанией **Return to Castle Wolfenstein** нужен каталог `Main/` оригинальной лицензированной PC-установки: `pak0.pk3`, `sp_pak1.pk3`, `sp_pak2.pk3`, `sp_pak3.pk3`. Состав указан в [инструкции iortcw на закреплённой ревизии](https://github.com/iortcw/iortcw/tree/438e7d413b5f7277187c35b032eb0ef9093ae778#installation). Достаточно держать файлы в существующей локальной установке. При необходимости проверяем на месте содержимое и контрольные суммы.

Команда `python scripts/rtcw_data.py "<путь к установке RTCW>"` читает каталог четырёх PK3, сообщает о недостающих или нечитаемых файлах и ищет запись `maps/escape1.bsp`. Проверка работает на месте. Она читает метаданные ZIP, поэтому не проверяет содержимое BSP или CRC файлов внутри архивов.

Команда `python scripts/rtcw_data.py "<путь к установке RTCW>" --locate maps/escape1.bsp` определяет источник ресурса внутри одного каталога `Main`. Для одиночного режима архивы `mp_*` пропускаются, имена `sp_*` сортируются как `zz_*`, поздний по сортировке PK3 имеет приоритет, а отдельный файл ищется после архивов. Правило сверено с [FS_AddGameDirectory в закреплённом iortcw SP](https://github.com/iortcw/iortcw/blob/438e7d413b5f7277187c35b032eb0ef9093ae778/SP/code/qcommon/files.c#L3197).

Команда `python scripts/rtcw_data.py "<путь к установке RTCW>" --state-dir "<путь для сохранений и кэша>"` дополнительно проверяет разделение путей. Проверка раскрывает символьные ссылки, отклоняет пересечение с деревом установки или фактическим каталогом `Main` и сообщает об обычном файле на пути. Она проверяет структуру путей без создания каталогов и проверки права на запись.

Команда `python scripts/rtcw_data.py "<путь к установке RTCW>" --bsp-info maps/escape1.bsp` выбирает ресурс по тем же правилам, что `--locate`. Она читает 144 байта заголовка IBSP v47 из PK3 или отдельного файла, проверяет границы, перекрытия и размеры записей в секциях. На выходе JSON с источником, диапазонами и количеством фиксированных записей. Код 1 означает ошибку поиска, чтения или структуры заголовка. Проверка содержимого секций и полного CRC требует отдельного чтения файла. [Описание формата на закреплённой ревизии](https://github.com/iortcw/iortcw/blob/438e7d413b5f7277187c35b032eb0ef9093ae778/SP/code/qcommon/qfiles.h#L549)

Для авторского BSP-файла команда `python scripts/ibsp_metadata.py "<путь к файлу .bsp>"` дополнительно проверяет диапазоны вершин и индексов каждой поверхности, а также значения индексов внутри диапазона её вершин. Проверка читает таблицы поверхностей и индексов из отдельного файла и соблюдает ограничения IBSP v47 на размер этих таблиц. На выходе JSON с числом проверенных поверхностей или ошибка с номером некорректной поверхности. Входной файл открывается в режиме чтения. [Синтетические тесты](../../scripts/test-project.py)
