# RTCW NextGen — состояние проекта

- Дата и задача — 26.11.2026, P00.1–P00.3.
- Интеграционная ветка — `rtcwnextgen-prototype`, от `ea6b8ccce796289cb91fe2447b733e56cb12d817` (`master`). SHA рабочей ревизии определяется по `git rev-parse HEAD`.
- Ревизии движка и зависимостей зафиксированы в [ADR 0001](adr/0001-upstream-baseline.md).
- Состояние — локальная проверка baseline пройдена в Linux, Windows CI и проверка реального Windows ZIP ожидают запуска.
- Добавлены сборка Windows DX12, GitHub Actions с правами чтения, контролируемая упаковка Windows ZIP и автоматические проверки.
- Linux Release собрал `RBDoom3BFG` и `rbdmap`. В чистой проверенной сборке облачной среды DXC выполнил 749 задач SPIR-V.
- `python3 -B scripts/test-project.py --rbdmap build-cloud/tools/compilers/rbdmap` — 3 теста прошли. Проверены создание BSP и коллизий, выбор файлов для ZIP, чистая распаковка и SHA-256 на синтетических входах.
- `actionlint` и `git diff --check` — пройдены.
- Vulkan через Xvfb/Mesa llvmpipe загрузил шейдеры и инициализировал рендерер. Полный запуск завершился с кодом 1 при загрузке `Arial_Narrow`. Аппаратный GPU/DX12 и игровая приёмка — NOT_RUN.
- Игровые кандидаты и приёмка — ожидают будущего игрового этапа. Список ресурсов приведён в [TESTING](TESTING.md).
- **NEXT_TASK P00-T04** — выполнить Windows CI на проверяемом коммите, подтвердить Release и DXIL, запуск `rbdmap` на runner, ZIP и SHA-256. После прохождения P00 переходить к P01 согласно [Handoff](HANDOFF.md).
