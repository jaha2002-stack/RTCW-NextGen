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
- P01-T01 — AUTO_VERIFIED на синтетических входах, включая [Windows CI](https://github.com/jaha2002-stack/RTCW-NextGen/actions/runs/45849490125). `scripts/rtcw_data.py` также успешно прочитал каталоги четырёх архивов доступной лицензированной установки. Запись `maps/escape1.bsp` находится в `pak0.pk3`.
- P01-T02 — Linux smoke PASS. Причина чёрного кадра — `map _white` перенаправлялся на отсутствующую текстуру `guis/assets/white`. Синтетический материал использует собственную белую текстуру 8×8. `bash scripts/smoke-renderer-linux.sh` подтвердил красную и синюю области в PNG 640×480 и завершение процесса с кодом 0.
- Vulkan validation выявил утечку семафора при завершении. Очистка теперь освобождает всю очередь семафоров независимо от числа изображений swapchain. Повторный smoke с `VK_LAYER_KHRONOS_validation` прошёл без ошибок слоя. Аппаратный GPU, runtime DX12, resize и ввод — NOT_RUN.
- **NEXT_TASK P01-T03** — после проверки сборки Windows проверить изменение размера окна и ввод в синтетическом режиме. Ручной checkpoint R01 требует рабочего кадра, окна, ввода и корректного завершения.
