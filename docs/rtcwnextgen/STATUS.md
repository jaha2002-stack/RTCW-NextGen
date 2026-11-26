# RTCW NextGen — состояние проекта

- Дата и задача — 26.11.2026, P01-T02 (синтетический smoke-тест рендерера).
- Интеграционная ветка — `rtcwnextgen-prototype` на `4b660789c3f0060ea983182d586ebbdb694af015`. Эксперимент сохранён в `rtcwnextgen/phase-p01-renderer-smoke`.
- Ревизии движка и зависимостей зафиксированы в [ADR 0001](adr/0001-upstream-baseline.md).
- Состояние P00 — AUTO_VERIFIED для исходного baseline. [Windows CI](https://github.com/jaha2002-stack/RTCW-NextGen/actions/runs/45848446252) подтвердил Release x64, DX12/DXIL, три функциональные проверки, распаковку и SHA-256 Windows ZIP на коммите `015972ee7366dc0ea04d58b1c2ee87f251a5e469`. Артефакт GitHub Actions имеет SHA-256 `ba0543cf6e36fd4edbdedbdf414004a2edd02d86f04faa5a62b16c54198557fb`. Внутренний ZIP сопровождается отдельным файлом `.zip.sha256`.
- Добавлены сборка Windows DX12, GitHub Actions с правами чтения, контролируемая упаковка Windows ZIP и автоматические проверки.
- Linux Release собрал `RBDoom3BFG` и `rbdmap`. В чистой проверенной сборке облачной среды DXC выполнил 749 задач SPIR-V.
- `python3 -B scripts/test-project.py --rbdmap build-cloud/tools/compilers/rbdmap` — 5 тестов пройдены. Проверены создание BSP и коллизий, выбор файлов для ZIP, чистая распаковка и SHA-256, а также синтетические PK3.
- `actionlint` и `git diff --check` — пройдены.
- Vulkan через Xvfb/Mesa llvmpipe загрузил шейдеры и инициализировал рендерер. Полный запуск завершился с кодом 1 при загрузке `Arial_Narrow`. Аппаратный GPU/DX12 и игровая приёмка — NOT_RUN.
- Игровые кандидаты и приёмка — ожидают будущего игрового этапа. Список ресурсов приведён в [TESTING](TESTING.md).
- P01-T01 — `scripts/rtcw_data.py` читает директории PK3 и определяет наличие первой карты. Тесты покрывают чтение с различным регистром имён, сохранность архивов и диагностику отсутствующего, повреждённого и пустого PK3. Реальные ресурсы — NOT_RUN (лицензионная установка не подключена).
- P01-T01 — AUTO_VERIFIED на синтетических входах, включая [Windows CI](https://github.com/jaha2002-stack/RTCW-NextGen/actions/runs/45849490125).
- P01-T02 — FAILED на проверке пикселей. Минимальная конфигурация из `tests/fixtures/renderer-smoke.mtr` стартует с Mesa llvmpipe, отправляет один 2D draw call с четырьмя треугольниками на кадр, сохраняет PNG 640×480 и завершает процесс с кодом 0. `bash scripts/smoke-renderer-linux.sh` возвращает 1: ожидаются красная и синяя области, а все пиксели чёрные. Диагностический `r_drawEyeColor 1` даёт серый RGBA (128,128,128,255), подтверждая захват активного render target. Аппаратный GPU и Windows для этой экспериментальной ветки — NOT_RUN.
- **NEXT_TASK P01-T02** — воспроизвести `bash scripts/smoke-renderer-linux.sh` после сборки Linux и локализовать, где теряется цвет при отрисовке GUI. Начать с проверки состояния render target и параметров shader stage отдельного draw call. Затем повторить проверку пикселей и собрать Windows-вариант.
