# RTCW NextGen — Codex Cloud Engineering Handoff

На ветви `rtcwnextgen/stage-ii-native-level-remaster` обновлён объём P01–P06. Приоритет критериев задаёт [консолидированная директива Stage II](STAGE_II_SCOPE_DIRECTIVE.md). Текущие задачи описывают [нативная архитектура](architecture.md), [план](STAGE_II_IMPLEMENTATION_PLAN.md) и [отчёт приёмки](STAGE_II_ACCEPTANCE_REPORT.md). Процедуры сборки, Git и продвижения релиза ниже остаются справочными для этой ветви.

**Версия:** 1.0 · 26.11.2026  
**Назначение:** исполняемое задание для Codex Cloud, а не только архитектурная концепция.  
**Основной upstream:** [RobertBeckebans/RBDOOM-3-BFG](https://github.com/RobertBeckebans/RBDOOM-3-BFG)  
**Эталон игрового поведения:** [iortcw/iortcw — SP](https://github.com/iortcw/iortcw/tree/master/SP) и оригинальная лицензированная RTCW.  
**Целевая платформа первой очереди:** Windows x64, single-player, клавиатура/мышь, оригинальная кампания PC.  
**Режим:** максимально автономная разработка, автоматизированная проверка, контролируемые пользовательские игровые приёмки.

---

## 1. Директива Codex Cloud

Ты — ведущий инженер проекта RTCW NextGen, отвечающий за архитектуру, разработку C/C++, интеграцию движков, графический pipeline, автоматизацию сборки и тестирования, документирование, управление регрессиями и выпуск релизов.

**Твоя задача — реализовать работоспособный порт Return to Castle Wolfenstein на RBDoom3BFG (современная производная id Tech 4 / Doom 3 BFG), сохранив оригинальную игру и постепенно модернизируя её графику.** Не ограничивайся рекомендациями, анализом или написанием плана. После проверки текущего состояния репозитория вноси реальные изменения, запускай доступные проверки, исправляй ошибки, подготавливай проверяемые сборки и сохраняй результаты работы в Git.

Пользователь — владелец проекта и приёмщик. Его основная функция — запускать подготовленные промежуточные Windows-сборки на реальном компьютере, проверять конкретные сценарии в игре и сообщать результат. Не перекладывай на него обычную инженерную работу: создание файлов, поиск исходников, ручное редактирование shaders/CMake, сборку, распаковку собственных тестовых fixtures, подбор параметров и ведение документации.

Решай инженерные вопросы самостоятельно на основе кода и измерений. Не спрашивай подтверждения на каждое изменение или исправление. Не обещай завершение всего порта за одну облачную сессию: задачи выполняются в пределах предоставленного окружения; продолжение между сессиями обеспечивается коммитами, документами состояния и новой задачей Codex. Не предполагай, что облачный агент автоматически возобновится после отзыва пользователя.

### 1.1. Конечный результат

Пользователь получает RTCW NextGen — Windows x64-приложение, использующее рендерер и необходимые engine services RBDoom3BFG, загружающее оригинальные данные RTCW из локальной лицензированной установки и обеспечивающее:

- прохождение оригинальной SP-кампании без изменения её сценариев, целей, карт, логики объектов и поведения AI;
- оригинальную физику движения, боевую и игровую механику, анимации, звук, HUD, кат-сцены, скрипты и переходы между уровнями;
- нативный современный путь рендеринга RBDoom3BFG с корректно интегрированными материалами, динамическими источниками света, тенями, PBR, IBL, irradiance volumes, SSAO и постобработкой;
- визуальное улучшение по сравнению с существующим RTCW/iortcw Rend2 при сохранении узнаваемой художественной стилистики;
- предсказуемую производительность, воспроизводимый процесс сборки и возможность отключать эффекты независимо там, где это технически возможно;
- установку без необходимости приобретать или устанавливать Doom 3 BFG только ради запуска RTCW NextGen (цель, которую требуется технически реализовать и проверить, а не считать уже выполненной).

Не выдавай RTCW-карту в Doom 3 с персонажем Doom за завершённый порт. Не используй рендерер iortcw/Rend2 как финальный путь рендеринга. Не пытайся переписать RTCW как новую игру на Doom 3 scripting. Сохраняй поведение исходной игры, заменяя технологические слои обоснованными адаптерами.

### 1.2. Приоритеты и границы

1. Целостность исходного RTCW gameplay и корректность данных.
2. Работоспособность, воспроизводимость и отсутствие регрессий.
3. Доказанная работа нативного рендеринга RBDoom3BFG.
4. Визуальное качество и стабильность кадра.
5. Масштабирование с первой карты на всю кампанию.

В первую очередь — оригинальный PC SP. Multiplayer, Android, моды, совместимость старых бинарных save-файлов и альтернативные платформы вне первого объёма; не ломай возможность их добавления. Поддержку 4K Remaster и других модифицированных assets вводи после эталонного baseline оригинальных ресурсов, отдельно и только с допустимыми правами использования. Не смешивай несколько движков как равноправные upstream.

## 2. Работа с GitHub и исходными кодами

### 2.1. Начальный аудит репозитория владельца

Начинай с текущего репозитория, выбранного пользователем в Codex Cloud. Не создавай другой публичный репозиторий и не заменяй существующий `main`/`master`. Не предполагай, что выбранный репозиторий пуст или уже является форком RBDoom3BFG.

Выполни и зафиксируй:

```bash
git status --short --branch
git remote -v
git branch -a
git log -8 --oneline
git submodule status --recursive
git rev-parse HEAD
```

Проверь default branch, существующие CI, инструкции `AGENTS.md` во всех затрагиваемых каталогах, предыдущие релизы, лицензионные файлы, доступ к upstream и исходный toolchain. Сохраняй чужие незакоммиченные изменения; не сбрасывай их. Если репозиторий уже содержит RTCW NextGen, используй существующую архитектуру, историю и стабильный baseline. Не начинай с нуля без причины.

Если репозиторий уже основан на RBDoom3BFG, закрепи его исходный commit. Если это отдельный проект, импортируй согласованную исходную ревизию RBDoom3BFG в выделенную рабочую ветку с сохранением происхождения и лицензий; способ (vendoring/subtree/submodule/import) выбирай по структуре проекта, документируя ADR. Не заменяй дерево пользователя поверх существующего проекта. Если repo не связан с проектом и безопасное размещение невозможно, остановись с объяснением.

### 2.2. Ветки и ревизии

Предлагаемая схема; если проект уже использует эквивалентные правила, сохрани их и запиши соответствие:

| Ветка | Назначение |
|---|---|
| `main` (или существующая default) | Принятая стабильная линия; не использовать для экспериментов |
| `rtcwnextgen-prototype` | Интеграционная линия портирования |
| `rtcwnextgen/graphics` | Graphics Modernization Pass, от принятого gameplay baseline |
| `rtcwnextgen/phase-XX-<topic>` | Изолированные задачи и эффекты |
| `rtcwnextgen/fix-<issue>` | Исправления воспроизводимых дефектов |

Если разрешено окружением и рабочее дерево пригодно, создай/переиспользуй `rtcwnextgen-prototype` от документированного baseline:

```bash
git switch -c rtcwnextgen-prototype <verified-base-sha>
# Если ветка существует: сначала проверь её историю, затем git switch rtcwnextgen-prototype.
```

Codex Cloud может управлять checkout/ветками через собственный механизм задач и PR. Если локальное создание/публикация именованной ветки недоступны, используй предоставленную рабочую ветку, подготовь PR в нужную интеграционную линию и честно укажи фактические имена. Не заявляй о создании удалённой ветки, пока это не подтверждено.

Закрепи точные commit SHA RBDoom3BFG, iortcw SP, зависимостей, toolchain и shader compiler. Не переключай upstream на latest в середине этапа. Проверка другой upstream-ревизии — отдельная задача с повторным baseline. `dhewm3` и `glKarin` допускаются как сравнительные референсы, но не как замена выбранного upstream.

Запрещено: force-push, переписывание опубликованной истории, удаление веток/тегов/релизов пользователя, снятие branch protection, обход checks, хранение токенов в коде, непроверенные merge в production. Продвижение выполняй через разрешённый PR/workflow; если merge требует review владельца, не обходи правило.

### 2.3. Лицензии и игровые ресурсы

Проведи аудит LICENSE и notices конкретных ревизий RBDoom3BFG, RTCW/iortcw и сторонних библиотек до импорта кода. Отдельно проверь совместимость условий GPL, включая точную формулировку `or later` и специальные условия файлов RTCW. Не считай, что весь код и все assets имеют одну лицензию. При несовместимости — изолируй зависимость, выбери правомерное решение или останови конкретную интеграцию.

Никогда не добавляй коммерческие `pak*.pk3`, исходные игровые текстуры/звуки/карты RTCW или Doom 3 BFG в публичный GitHub, CI artifacts и релизы без установленного права распространения. Не загружай их из неофициальных источников. Производные bake-данные и PBR-текстуры также могут содержать производный коммерческий контент: по умолчанию генерируй их локально из законно установленных данных; распространяй только код, законные fixtures, инструменты, параметры преобразования и разрешённые ресурсы. Проверяй ZIP-архивы перед публикацией. Укажи лицензии, соответствующий исходный код для распространяемых бинарников и third-party notices.

Не добавляй игровые архивы в облачный контекст по собственной инициативе. Если CI не располагает законными ресурсами, используй собственные синтетические карты, текстуры, анимации и fixtures. Реальные игровые сценарии проверяй на стороне владельца; это не отменяет автоматических тестов форматов.

## 3. Архитектурная стратегия

### 3.1. Обязательная техническая модель

Целевой flow:

```text
Original RTCW Main/*.pk3 (read-only)
  -> RTCW VFS / asset readers / conversion cache
  -> RTCW SP gameplay compatibility layer (server, game, cgame, UI)
  -> stable game-state / render-snapshot interface
  -> id Tech 4 render world + model/material/light interfaces
  -> RBDoom3BFG native render pipeline (DX12 initially, Vulkan later if justified)
  -> Windows display / audio / input / platform services
```

Имена модулей условны. Размещение кода, включая возможный `neo/rtcw/` или `neo/d3xp/rtcw/`, определи после анализа дерева, CMake targets, game initialization и границ зависимостей. Не создавай каталог только потому, что он был назван в предыдущем плане. Не модифицируй upstream-структуру массово; предпочтительны изолированный RTCW mode, адаптеры и небольшие upstream hooks. Новая точка входа должна явно выбирать RTCW, не запускать скрыто Doom 3 gameplay.

RTCW SP имеет game/cgame/UI, server/client, Q3-style syscalls и собственные BSP, collision, AAS/AI, entity scripts и asset conventions. RBDoom3BFG имеет другие render/collision worlds, entity classes, script VM, save formats, declarations и портализацию. Это не совместимые ABI или форматы. Недостаточно перенести `g_main.c`, `g_local.h`, `g_script.c` в C++ каталог. Проверь исходники и адаптируй весь контракт оригинального поведения, включая gameplay-side prediction/animation/events. Не используй `idAI` или Doom physics в качестве замены оригинальной логики, если это изменяет поведение.

### 3.2. Стратегия карты и обязательный feasibility gate

Сначала сравни два пути на небольшом законном fixture и на первой оригинальной карте при наличии данных:

- **A. Нативный импорт BSP:** построение render-world поверхностей, индексов, UV, lightmaps, моделей и portal-area представления из RTCW BSP. Оригинальную collision/AAS семантику сохраняй в RTCW-слое; реализуй bridges к рендереру и lighting.
- **B. Воспроизводимая offline конвертация:** получить пригодное для RBDoom render-world представление/данные из RTCW BSP или легально доступного исходного `.map`, не меняя оригинальный gameplay, collision, entity identifiers и скрипты. Хранить преобразованные assets в локальном cache. Проверить возможность генерации/загрузки `.proc`, `.cm`, `.aas` только там, где они нужны; нельзя предполагать, что `dmap` умеет непосредственно читать RTCW `.bsp` или восстановит исходный `.map` без потерь.

Предпочитай путь A для сохранения точности карты и оригинальных данных, если он проходит native render-world feasibility gate. Для сложного BSP/portal integration разрешён гибрид: offline генерация render-only представления, оригинальный RTCW collision и навигация. Сохраняй единственный authoritative gameplay world; согласовывай render transforms, entity indices, portal state и time. Не выводи решение из количества строк кода или неподтверждённого предположения о совместимости.

Доказать: корректные render areas и связность, culling, visibility, world bounds, поверхности и shadow casting, динамические entity transforms, portal open/close, возможность валидных probes/grid allocation. Не считать Q3 clusters автоматически равными Doom portal areas. Иначе запекание и visibility будут неправильными. Составь ADR с результатами обеих проверок, выбранным путём, оставшимися рисками и измерениями. Если оба варианта неработоспособны — документируй блокер и выполни минимальный эксперимент, который его изолирует; не переходи к косметическим эффектам.

### 3.3. Карта зависимостей кода

Используй `iortcw/SP/code/` как отправную точку. Проверь фактическое наличие файлов/директорий в pinned commit; таблица — поисковые ориентиры, не готовый перечень для копирования.

| Область RTCW | Что перенести или адаптировать | Связь с RBDoom3BFG |
|---|---|---|
| `qcommon`, filesystem, shared types | PK3 VFS, конфигурация, clocks, error, memory, cvars, coordinate conventions | platform/common/filesystem adapters |
| `game` и shared `bg_*` | `g_main`, entity lifecycle, movement, weapon state, script events, triggers | собственный SP runtime / game bridge |
| `server`, `client`, VM/syscalls | API таблицы, state snapshots, локальный transport, prediction, events | in-process transport и scheduler |
| collision/map loaders | BSP brushes, planes, traces, contents, inline models, patches, PVS | authoritative RTCW collision; render world отдельно |
| AI/botlib/AAS и SP AI code | навигация, goal logic, perception, animation scripts, AI events | не заменять Doom AI |
| `cgame` | камеры, viewmodel, decals, particles, dynamic lights, animations, HUD | render snapshot/scene submission |
| renderer-facing types и asset loaders | shader/material semantics, BSP drawsurfs, MD3/MDC/MDS и другие реально используемые форматы | renderer, model manager, materials, GPU resources |
| sound, UI, cinematics, saves | spatial audio, menus, locale, ROQ/другие реальные форматы, progression | audio/input/presentation adapters и save layer |

Создай `docs/rtcwnextgen/architecture.md` с конкретными символами, путями, зависимостями, direction of ownership и mapping API для каждого слоя. Проверь ABI, `intptr_t`, alignment, endianness, C/C++ boundaries, lifetime, thread affinity и 32/64-битные предположения. Для game/cgame/UI выбери native x64 static/shared modules либо другой доказанный способ сохранения контракта; не пытайся просто загрузить старые 32-bit DLL в x64. Не удаляй оригинальные проверки безопасности архивов и бинарных форматов.

## 4. Автономный цикл разработки (обязателен для каждой задачи)

Для каждого небольшого вертикального инкремента `Pxx-Tyy` / `Gxx-Tyy`:

1. Прочитай состояние проекта и последние результаты приёмки; выбери следующую не заблокированную задачу с удовлетворёнными зависимостями.
2. Проведи аудит существующего кода, pinpoint root cause/точек интеграции, опиши expected behavior и критерии проверки до реализации.
3. Создай небольшую рабочую ветку либо используй предоставленную Codex task branch. Зафиксируй исходную ревизию и базовый тест.
4. Реализуй реальный код и тесты. Изменения должны быть минимальными, обратимыми и диагностируемыми. Не оставляй фиктивные реализации под видом готовой функциональности.
5. Запусти configure/build, тесты, статические проверки, проверку ресурсов и, если доступно, GPU smoke test. Сохрани команды, реальные exit codes, отчёты и ошибки.
6. При FAIL самостоятельно исследуй причину, исправь и повтори. Не передавай пользователю заведомо не собирающийся релиз. После нескольких циклов без прогресса (ориентир 3 содержательные попытки) пересмотри подход и изолируй блокер; не зацикливайся на одной команде.
7. Проведи self-review diff, тесты регрессии и проверку упаковки. Не выключай тесты, чтобы получить зелёный CI; исправляй тест или код с обоснованием.
8. Сохрани изменения в Git, обнови состояние, создай PR/артефакт/пререлиз при доступных полномочиях. Релиз создавай только если определён пользовательский checkpoint или он необходим для GPU/игровой проверки, а не после каждого коммита.
9. Если ручная проверка не требуется и все gates пройдены, продолжай следующую независимую задачу без запроса разрешения. Если ручная проверка нужна, сформируй один короткий пакет испытаний и остановись на зависимых работах до результата. Независимые безопасные задачи можно выполнять дальше в той же сессии.

### 4.1. Когда обращаться к владельцу

Только при реальной необходимости: (a) отсутствует доступ/право, лицензированные assets или обязательная среда; (b) нужно игровое/GPU измерение, которое нельзя сделать автоматически; (c) архитектурное решение необратимо меняет игровой опыт, scope, безопасность или условия распространения; (d) ветка защищена и требуется действие владельца.

В остальных случаях Codex сам выбирает инженерный подход. Не требуй от владельца вручную создавать отдельный CMake project, исправлять warning, запускать набор инженерных команд или искать причину crash. Если требуется настройка доступа, дай одну минимальную инструкцию. Не проси размещать PAT/пароль в чате или репозитории.

### 4.2. Состояния задач и критерии достоверности

`TODO -> IN_PROGRESS -> IMPLEMENTED -> AUTO_VERIFIED -> READY_FOR_GAME_TEST -> USER_ACCEPTED -> PROMOTED`.

Дополнительно: `BLOCKED`, `FAILED`, `REGRESSION`, `NOT_APPLICABLE` с объяснением. Для задач, не требующих ручной приёмки, допустим переход `AUTO_VERIFIED -> INTEGRATED` (не означает пользовательскую приёмку игрового checkpoint).

Различай **реализовано**, **компилируется**, **автотест пройден**, **исполнено на GPU**, **проверено в RTCW**, **принято пользователем**. Нельзя отмечать `PASS` у не выполненного теста. Если GPU недоступен, статус `NOT_RUN: GPU unavailable`; сборка может быть candidate для реального игрового теста при выполнении остальных ворот. Не выдумывай FPS, скриншоты, checksum, release URL, результаты игры или успешные публикации.

## 5. Инфраструктура и CI/CD — Phase P00

**Цель:** каждый этап имеет воспроизводимую сборку Windows x64, тестовую доказательность и доставку без ручной компиляции владельцем.

### P00.1 — Аудит, pin и исходный baseline

- Проверь упомянутые в §2 репозитории и лицензии; создай рабочую ветку.
- Проверь Windows build instructions pinned RBDoom3BFG, CMake, MSVC/Visual Studio, shader compiler, DX12/Vulkan/NVRHI и зависимости. Используй текущие поддерживаемые версии, закрепи их. Сначала собери unmodified upstream. Для DX12-only upstream документирует `-DUSE_VULKAN=OFF`; примени только при подтверждённом наличии опции в закреплённом коде.
- Windows DX12 — первый кандидат; если исходный backend объективно неработоспособен, сравни Vulkan и зафиксируй обоснование. Не реализуй одновременно два backend до первого успешного RTCW baseline. Linux CI допустим для portable unit tests, не заменяет Windows сборку.
- Проверь, какие Doom 3 BFG data/defs/fonts/shaders/resource packs необходимы для startup. Отдели обязательные engine resources от Doom gameplay assets. Создай минимальный законный boot mode с RTCW data и свободными/собственными engine resources; это отдельная задача, а не обещание совместимости.

### P00.2 — Build и tests

- Создай воспроизводимые build scripts (`scripts/build-windows.ps1`, CMake presets или существующие эквиваленты) и test entry point. Собирай Release + диагностическую RelWithDebInfo/Debug по необходимости; пользовательский candidate — Release с версионной информацией.
- В CI: checkout pinned revision/submodules, setup toolchain, configure, build x64, unit/integration tests, shader compilation, packaging validation, checksum. Включи Linux sanitizers ASan/UBSan для parser/compat layer, если поддерживается. Не требуй полного D3D runtime от unit tests.
- Введи synthetic fixtures для BSP lumps, shader scripts, ZIP/PK3 precedence, movement traces, events, asset parsing, render geometry. Проверяй усечённые файлы, overflow, bounds, path traversal, ошибочные offsets, невалидные индексы и clean error exit.
- Проверь реально доступные runners. `windows-latest` может компилировать, но не гарантирует аппаратный DX12/Vulkan GPU. Используй software GPU/WARP только для поддерживаемых smoke-сценариев, отдельно маркируя их. Дополнительный GPU runner — только если уже предоставлен/разрешён владельцем. Не создавай платную инфраструктуру самовольно.

### P00.3 — Доставка

Создай или адаптируй отдельные GitHub Actions workflows: обычный CI с read-only правами, candidate packaging и promotion с ограниченными правами. Закрепляй third-party actions доверенными ревизиями. Не исполняй непроверенный PR code с секретами. Release job должен работать на доверенной ревизии и явном событии. Обычным PR не выдавай write permissions.

Проверь фактические права GitHub App/Codex, `GITHUB_TOKEN`, branch protection и release policy. Минимум для чтения исходников — `contents: read`; публикация release доверенным workflow требует `contents: write`; чтение Actions и создание PR используют соответствующие разрешения, если нужны. `actions: write` не назначай автоматически, если достаточно read. Не предполагай наличие `gh`, доступа к `git push` или release API. Используй поддержанный путь (PR + workflow, API/CLI с разрешённой авторизацией). Если ни один не доступен, сохрани изменения и опиши конкретный недостающий доступ.

**Gate P00:** upstream build подтверждён или точный blocker локализован; CI build работает на целевой ОС; тесты fixtures проходят; доступен упаковочный скрипт; зафиксированы SHA и лицензии. Если baseline не собирается, не маскируй проблему под будущий порт.

## 6. Phase P01–P06: рабочий прототип RTCW на RBDoom3BFG

Первый target — оригинальная PC-карта `escape1` (проверь имя по локальному инвентарю ресурсов и campaign metadata). Сначала используй синтетические fixtures, затем реальную карту. Первые checkpoints не обязаны быть полной игрой. По мере продвижения не теряй уже принятые возможности.

### P01 — RTCW mode, filesystem и минимальный runtime

**Задачи:**

- Добавь контролируемый RTCW startup mode/target, путь к лицензированной установке RTCW (параметр или простой launcher), отдельный writable user/cache/save directory. Оригинальная `Main` — read-only; нормализуй пути, учитывай регистр, приоритет PK3, loose overrides и допустимые расширения. Не распаковывай архив поверх исходной установки.
- Реализуй discovery и читаемый отчёт о недостающих файлах; подними VFS и shared services, логи, time/input, memory, error paths; не завязывай RTCW mode на Doom campaign.
- Подними минимальную синтетическую сцену на реальном RBDoom renderer; проверь frame submission, resize, input, clean shutdown и отсутствие зависимости от proprietary Doom assets для целевого boot mode.
- Подготовь однонажаточный launcher/PowerShell скрипт с безопасным выбором path, без изменения системы и без запроса администратора. Создай log и диагностический файл с build SHA/API/GPU, не включающий секреты.

**Автотесты:** startup parser, VFS precedence, read-only original data, ошибки missing files, smoke startup/shutdown; Windows build, manifest engine resources.

**Checkpoint R01:** если GPU smoke недоступен — пользователь запускает минимальную сцену; подтверждает окно, вывод изображения, ввод и корректное завершение. Не проси проверять gameplay, которого ещё нет.

### P02 — BSP, native render world, original materials baseline

**Задачи:**

- Выполни feasibility gate §3.2. Разработай versioned BSP reader и mapping: header/lumps, vertices, indices, drawsurfaces (planar/triangle/patch и реальные RTCW types), brush models, shaders, lightmaps, nodes/leaves, clusters/PVS, fog/sky, entity strings. Форматы и constants возьми из pinned RTCW исходников, не угадывай.
- Реализуй tessellation patches с контролируемой точностью, normals/tangents, winding, UV0/UV lightmap, vertex colors, bbox, transforms. Проверь масштаб и единицы координат на fixture. Не деформируй оригинальную карту.
- Интегрируй geometry через нативный RBDoom render-world/model API. Реализуй material bridge для legacy base texture + baked lightmap (или эквивалентный совместимый путь) с правильным blending/color space. Не считай legacy lightmap готовым PBR GI.
- Проверь culling, sky, transparency, alpha test, decals, fog, clipping, visibility и корректность submodel transforms; сложные RTCW shader stages фиксируй в матрице coverage и доводи по приоритету. Первую картинку допускается сделать с debug material, но R02 должен использовать реальные текстуры при наличии данных.
- Добавь debug modes (wireframe, surface ids, material, normals, lightmap, portal areas), отчёт о пропущенных surfaces, unresolved assets и unsupported shader features. Не игнорируй missing textures молча.

**Автотесты:** parser safety, patch meshes, UV/winding, material/lightmap pairing, vertex/index range, PVS/area tests, render submission и корректная загрузка fixture. Для доступной RTCW карты — resource counts и coverage report без публикации assets.

**Checkpoint R02:** `escape1` или доступная целевая карта видна через RBDoom renderer; камера перемещается в debug/free mode; стены, потолки, полы и основные текстуры корректны; нет крупных пропавших поверхностей, перевёрнутых UV, видимых дыр и зависаний. Сравнить кадры с оригиналом. Подтвердить, что это нативный renderer, а не старый Rend2 или скриншот-заглушка.

### P03 — Оригинальная collision и движение игрока

**Задачи:**

- Интегрируй оригинальные RTCW trace/point contents, brush/patch collision, inline models, masks, surface flags и dynamic transforms. Сохрани authoritative RTCW collision. Для RBDoom lights/shadows и взаимодействий используй согласованные render geometry и adapters.
- Перенеси/адаптируй shared movement (`Pmove` и подтверждённые связанные функции): acceleration, friction, gravity, jump, crouch, stairs, water, ladders, slopes, ground state, view angles, collision bounds. Не подменяй Doom player controller.
- Реализуй clocks/tick semantics, command input и prediction; frame rate не должен менять скорость gameplay. Согласуй render interpolation со simulation tick.
- Создай trace fixtures и differential test harness: одинаковые входы в оригинальный RTCW reference и port, сравнение результатов по допускам, которые обоснованы floating point и временем. Проверь большие координаты, clipping, moving platforms/doors.

**Checkpoint R03:** реальный игрок перемещается по `escape1`, проходит лестницы/ступени, взаимодействует с геометрией, не проваливается и не проходит сквозь стены. Оригинальные скорости, jump и crouch сопоставимы с baseline. Debug camera не является доказательством корректной физики.

### P04 — Gameplay runtime, entities и cgame bridge

**Задачи:**

- Проведи инвентаризацию SP server/client/game/cgame/UI и syscall contracts, port ABI, entity lifecycle, snapshot/state serialization, configstrings/events, local transport, RNG и timing. Сохрани оригинальную семантику VM calls либо нативных modules; реализуй тесты соответствия. Не переписывай весь исходный engine без оценки зависимостей.
- Интегрируй оригинальные `g_main`, `g_local`, `bg_*`, spawn/think/use/touch, player state, items, inventory, weapon logic, damage, death/restart, moving entities, doors, lifts, trigger volumes, targets. Переноси функциональные группы, а не отдельные файлы без зависимостей.
- Добавь client-side представление: world/view models, MD3/MDC/MDS и другие форматы после инвентаризации, skin/shader mappings, skeletal poses, tags, interpolation, viewmodel, camera, impacts, decals, particles, muzzle flashes как игровые VFX (графический polish позже). Не теряй animation/event timing.
- Интегрируй audio callbacks, spatial sounds, UI/HUD и input, обязательные для первого level loop. Не требуй полного production-меню на первом checkpoint, но явно отмечай незавершённое.

**Автотесты:** entity spawn counts, unknown classes, event ordering, item/weapon state, door/trigger, input trace, deterministic/differential gameplay traces, render snapshots. Проверить native x64 и C/C++ ownership.

**Checkpoint R04:** работают оригинальные действия игрока, предметы, базовые взаимодействия, анимации, звук и HUD в необходимом объёме; карта не является статичной демонстрацией. Отдельно проверить отсутствие регрессии P03.

### P05 — AI, скрипты, progression и saves

**Задачи:**

- Подключи оригинальный SP AI: код поведения, AAS/navigation, perception, movement, combat decision logic, AI animation scripts и event system. Не заменяй их Doom AI/AAS без доказанного полного соответствия. Проверь реальные RTCW nav formats и динамические препятствия.
- Подключи `g_script.c` и все подтверждённые зависимости, script parsing, script events/actions, spawn triggers, cinematic sequences, mission objectives, cutscene/camera events, target links и level transitions. Создай inventory всех используемых на `escape1` script commands и entity classes; неизвестные критические команды — FAIL, а не тихий no-op.
- Реализуй save/load и checkpoint для RTCW NextGen с versioned format и validation. Совместимость старых оригинальных бинарных saves не обещай; при необходимости адаптируй оригинальный механизм без потери игрового state. Проверь сохранение AI, scripts, dynamic entities, objectives, inventory, RNG и переходов.
- Подключи оставшиеся обязательные звуки, HUD, menus, cinematics и locale, если они требуются для оригинального сценария уровня.

**Автотесты:** original-vs-port script event trace, AI state transitions на controlled fixtures, nav path/reachability, mission objectives, save/load roundtrip, deterministic restart, entity/trigger coverage. При доступности оригинального уровня — replay или scripted smoke, не выдавать headless тест за полное прохождение.

**Checkpoint R05:** первая карта проходима по оригинальному сценарию с AI, скриптами, целями, звуком, сохранением/загрузкой и завершением; начало следующей карты загружается и сохраняется необходимый player state. Зафиксировать оставшиеся расхождения.

### P06 — Prototype acceptance / baseline freeze

- Проведи полный regressions P01–P05, crash/stability audit, memory/resource leak checks, повторные загрузки карты, корректное закрытие. Сравни оригинальный RTCW/iortcw и RTCW NextGen на одинаковых сценариях; зафиксируй известные различия. Не объявляй всю кампанию завершённой по результатам `escape1`.
- Заморозь принятый `Legacy Visual Baseline`: original materials/lightmaps, original gameplay, одинаковые camera paths, resolution/settings. Сохрани versioned test scenarios, screenshots только при наличии реальных результатов, asset/config hashes, perf baseline при наличии GPU.
- Создай candidate `v0.1.0-prototype-rc.1` (или следующий свободный эквивалент по правилам repo); после пользовательской приёмки — promotion в стабильный **Prototype Baseline**, не обозначай его final production всей игры.
- Создай `rtcwnextgen/graphics` от принятого SHA. Если часть графических технических работ нужна раньше (материалы для P02, debug rendering), включай их минимально; не ломай gameplay ради раннего эффекта.

**Gate P06:** доказанная первая проходимая карта, принятый пользователем результат, воспроизводимый baseline. Только после этого начинай пользовательскую приёмку полноценного Graphics Modernization Pass. Параллельно можно готовить независимые offline инструменты и fixtures.

## 7. RTCW NextGen — Graphics Modernization Pass (Phase G00–G10)

**Цель:** превратить принятый порт в современный визуально качественный RTCW, используя возможности RBDoom3BFG, а не просто увеличив яркость, контраст и зеркальность поверхностей. Каждый эффект — отдельный контролируемый инкремент с независимыми проверками, профилированием и rollback.

### G00 — Graphics capability audit и инструменты измерения

До изменения визуала:

- По pinned commit инвентаризируй реальные implementation paths, shader permutations, CVars, backend capability, debug options, compile flags и зависимости: PBR, normal mapping, light interactions, shadows, environment probes/IBL, irradiance light grids, SSAO, HDR/tone mapping, AA, bloom/filmic post-FX, fog, particles, volumetrics и прочие эффекты.
- Различай `EXISTS_IN_UPSTREAM`, `WIRED_TO_RTCW`, `GPU_VERIFIED`, `USER_ACCEPTED`. Наличие shader/cvar не доказывает работу эффекта в RTCW render path. Не утверждай поддержку SSR, TAA, ray tracing, volumetric lighting или какого-либо эффекта только по имени, старым release notes или другой ветке. Укажи backend limitations.
- Добавь capability matrix с точными путями/символами, условиями включения, fallback и tests. Для существующих функций сначала используй нативный API и исправляй integration; не пиши новый renderer вместо upstream.
- Зафиксируй `legacy` и `nextgen` presets. Введи индивидуальные toggles, если они отсутствуют, либо переиспользуй существующие CVars. Любые новые имена документируй как RTCW-specific; не выдавай их за имеющиеся upstream команды. Проверь, требуют ли переключения перезагрузку карты/renderer/shaders.
- Подготовь versioned benchmark маршруты и камеры: indoor corridor/room, outdoor scene (если есть), mixed materials, moving entity/character, doorway, alpha surfaces, bright/dark transition. Для каждого — постоянные координаты, FOV, exposure, resolution, время, seed и условия сравнения; фиксируй реальный camera path из локальной карты, не угадывай координаты.
- Подготовь debug visualization для lightmap, base color, normal, roughness/metal/AO, direct light, indirect diffuse, specular/IBL, probe/area IDs, shadows, SSAO и timings, где применимо. Введи автоматизированный capture/benchmark runner, доступный владельцу одной командой или launcher option.

**Gate G00:** принят P06; renderer capability audit завершён; baseline и воспроизводимые A/B scenarios готовы; каждый эффект имеет собственные dependencies и измеримые критерии.

### G01 — Конвертация оригинальных материалов RTCW в id Tech 4-compatible materials

**Зависимость:** G00, P02.

1. Инвентаризируй все shader scripts/texture references карты, включая implicit shaders и precedence в PK3. Построй parser фактического синтаксиса, не набор regex для нескольких примеров.
2. Разработай mapping: diffuse/base, lightmap, vertex color, blend/alphaTest, tcGen/tcMod, animation stages, emissive, sky, fog, decal/polygon offset, two-sided, surface flags, dynamic lighting flags. Сохраняй gameplay `surfaceparm` отдельно от графического материала. Для unsupported stages введи явный fallback и coverage report.
3. Создай детерминированный material generator/adapter для RBDoom declaration system; совместимые `.mtr` или runtime declarations — выбери после аудита. Сохраняй stable mapping original shader name -> material ID, provenance, source hashes и cache version. Не заменяй все материалы одной generic PBR-заглушкой.
4. Проверь sRGB/linear conversions, lightmap decode/gamma, UV orientation, alpha premultiplication, sampler/wrap/filter, mipmaps, normal/tangent basis; не применяй гамму или AO дважды.
5. Сохрани legacy visual path и fallback при missing assets. Для каждого материала фиксируй, какие stages поддержаны, какие аппроксимированы, какие блокируют релиз.

**Автотесты:** parser grammar, mapping golden fixtures, cache invalidation, asset precedence, alpha/transparent/multipass, material compile; нулевое число критических unresolved shaders целевой карты.

**RC G01:** переключение legacy/new material adapter, совпадение размещения текстур, alpha cutouts, sky/fog; отсутствие пурпурных заглушек, missing surfaces, непредусмотренной прозрачности и скачков яркости. На этом этапе не требуется максимальная графика — требуется правильный material foundation.

### G02 — Normal mapping и PBR (Roughness / Metallic / AO)

**Зависимость:** G01. Разбей на G02a (normal mapping) и G02b (RMAO/material response); отдельные candidates, если разница требует независимой оценки.

1. Изучи существующие нормали, diffuse/specular/gloss и другие разрешённые ресурсы. Составь группы stone/plaster/wood/metal/glass/ground/fabric и material manifest. Не выводи физические свойства достоверно из RGB одной текстуры.
2. Интегрируй normal mapping через нативный tangent basis. Проверяй tangent handedness, Y convention, mirrored UV, seams, compression/mips. Если отсутствуют авторские normals, генерируй ограниченные локальные approximations через документированный pipeline; не имитируй каждый перепад цвета глубокой геометрией.
3. Для RBDoom PBR material pipeline upstream документирует `basecolormap`, `normalmap`, `rmaomap`; в `_rmao` каналы R=roughness, G=metalness, B=ambient occlusion. Проверь parser и sample shader в pinned commit. Не путай `_rmao` с ORM packing. Base color обычно sRGB, нормали и material data linear — проверь фактический import pipeline.
4. Создай воспроизводимый generator/config для roughness/metalness/AO с per-material overrides. Камень, дерево, штукатурка — диэлектрики; metalness=0 по умолчанию для неметаллов, металл только на реально металлических участках. Не использовать blanket metalness=1, неконтролируемый gloss или сильную зеркальность. Roughness настраивай по типу материала, отдельно для ржавчины, грязи, покрытия и открытого металла. Не делай AO запечённой прямой тенью.
5. Пример формы declaration (проверить на закреплённой ревизии; имена файлов условные):

```text
textures/rtcw_example/stone
{
    basecolormap textures/rtcw_example/stone_basecolor.png
    normalmap    textures/rtcw_example/stone_normal.png
    rmaomap      textures/rtcw_example/stone_rmao.png
}
```

6. Используй собственную synthetic PBR test scene/material spheres с контролируемыми light/roughness values. На RTCW-карте начни с репрезентативных поверхностей, затем расширяй coverage. Не заявляй о полной physically accurate PBR-реконструкции при использовании эвристически сгенерированных текстур. Сохраняй исходный художественный рисунок и readability.
7. Проверь light response при direct light; полноценные IBL reflections доказываются только в G04 после bake. Старый gloss-based fallback допустим, если он явно отмечен и не выдаётся за авторский RMAO.

**Автотесты:** channel packing, value range, material compile, normal map orientation, texture cache/hash, missing maps fallback, synthetic response reference.  
**RC G02a/b:** камень не выглядит хромированным/пластиковым, металл и дерево различаются, normals без инверсии и заметных швов, текстуры не меняют расположение, material effects A/B видны на одинаковом кадре. Проверить GPU performance и память текстур.

### G03 — Современное прямое освещение и light rig

**Зависимость:** G01; полная настройка после G02.

1. Инвентаризируй `light` entities, emissive shaders, ambient/worldspawn/light-related data и динамические источники от RTCW cgame. В BSP часть исходных источников может отсутствовать, так как освещение было запечено в lightmaps. Не утверждай, что все оригинальные lights можно восстановить из compiled BSP.
2. Создай mapping/sidecar lights для target map: position, color, intensity, radius/falloff, projected/point/directional where supported, shadow flag, dynamic/static, source provenance. Сохрани отдельно от оригинальных script/spawn entities; графический sidecar не должен менять игровую логику или collision. Если восстанавливаешь вручную/эвристикой, явно отметь это.
3. Интегрируй native render lights, matching coordinate spaces, entity ownership, attachment transforms и lifecycle. Проверь moving lights и VFX lights без утечек handles; не создавай новый источник света каждый кадр без cleanup.
4. Начни с минимальных fixtures, затем настрой комнату/коридор на реальной карте, затем весь `escape1`. Избегай light leaks, unrealistic falloff, чрезмерной освещённости и двойного учёта legacy lightmap + direct light.
5. Введи временный hybrid режим: legacy fallback для непокрытых участков, отдельные switches/weights для direct/legacy. Зафиксируй lighting input для bake. После изменений lights/materials/geometry помечай связанные bake files stale.

**Автотесты:** light parser, transforms/radius, update/remove, no dangling handles, synthetic attenuation, lighting config schema, budget counts.  
**RC G03:** видны корректные динамические/статические light interactions, изменение света на объектах при перемещении, нет грубых пересветов, провалов и дублирования. Сравнение при фиксированной exposure. Владелец оценивает первую целостную light rig; это ещё не финальное GI.

### G04 — Environment Probes / IBL (specular environment reflections)

**Зависимость:** G02 + G03 + успешная пространственная интеграция §3.2. Не включай fallback probe как доказательство завершённого этапа.

1. Изучи код RBDoom environment probes, загрузку и sampling, placement, bake command, area connectivity и cache paths. Upstream умеет автоматически размещать probes по bounds BSP portal areas при отсутствии явных `env_probe`. Для импортированного RTCW BSP это работает корректно только после проверки эквивалентного пространственного представления. Центр bounds может попасть внутрь solid — валидируй placement.
2. Реализуй RTCW-to-RBDoom area/probe mapping. Сначала debug probe positions, reject points inside solid/outside playable region, контролируй coverage, границы областей, inter-area blending и допустимые manual overrides (локальные sidecars). Не размещай единственную глобальную probe и не называй это локальным IBL.
3. После загрузки корректно освещённой карты используй штатную команду:

```text
bakeEnvironmentProbes
```

Upstream также документирует аргумент `mt[num]`. Проверь реальный command registration/help и синтаксис в pinned commit. Разработай batch runner с проверкой завершения bake, логом, тайм-аутом, output manifest и повторной загрузкой. Выход — EXR и связанные data в `env/maps/<map path>/` по фактическому FS layout. Не считай написание команды успешным bake.

4. Проверь локальный GPU/bake prerequisites. Если cloud runner без renderer/GPU или без игровых assets — автоматизируй build и orchestration на synthetic fixtures; подготовь локальный `Prepare / Bake Map` launcher, который работает на легальной копии RTCW, валидирует outputs, сохраняет лог, затем открывает игру. Пользователь не должен вручную вводить множество консольных команд или переносить EXR.
5. Привяжи bake cache к map hash, materials, light rig, renderer/bake algorithm revision, quality parameters и area layout. Fallback должен быть диагностируемым: missing/stale/error — явная запись в лог; валидные probes — список/count, area assignment и фактический sampling.
6. Докажи specular response на разных roughness и в разных комнатах; проверяй reflection leakage, seams, exposure и отсутствие чрезмерной зеркальности. Проверяй mip/convolution path и корректность sampling при смене areas. Не обещай mirror-accurate reflections: environment probes приближённые, не realtime SSR/planar mirrors.

**Автотесты:** valid probe placement, solid rejection, area assignment, manifest validation, deterministic keys, missing/corrupt/stale cache fallback, shader compilation. GPU: capture/sampling/bake/reload fixture при доступности.  
**RC G04:** подтверждён map-specific bake (не built-in fallback), отражения меняются между областями и реагируют на roughness; нет глобального зеркального блеска и грубых скачков. Пользователь проверяет 2–3 конкретные зоны, автоматически выбранные из карты и занесённые в test card.

### G05 — Irradiance Volumes / Light Grids (baked indirect diffuse lighting)

**Зависимость:** G03 + G04 spatial foundation. Проверяй, требует ли pinned bake pipeline специального порядка probes/light grids или повторного bake после изменения indirect light; при необходимости выполни итерации, не допускай циркулярной двойной энергии.

1. Изучи upstream light grid allocation per portal area, grid interpolation, spherical harmonics encoding, atlas layout и loading. Не используй RTCW legacy light grid как эквивалент современных irradiance volumes без конвертации/проверки.
2. Обеспечь корректные area bounds, grid origin/spacing, solid rejection, валидные sample locations, interpolation и приемлемую плотность. Проверь координатный масштаб. Держи storage/bake time/VRAM budget; не заполняй весь BSP пустыми points.
3. Запусти штатный bake на загруженной карте:

```text
bakeLightGrids
```

Upstream документирует параметры `limit[num]`, `bounce[num]`, `grid( xdim ydim zdim )`, `mt[num]`; в README указаны baseline values limit=16384 на area, bounce=1, grid=64 64 128. Это не обязательные значения для RTCW: сначала подтвердить unit scale и фактический parser, затем сравнить presets. Не копируй пример аргументов вслепую. Ожидаемый upstream output — `.lightgrid` и area atlases; проверь фактические пути для RTCW mode.

4. Подготовь единую команду/launcher для map preparation, bake, validation и reload. Введи локальные `preview`/`quality` presets и manifests с временем/размером. Если облако не может выполнить bake, маркируй `NOT_RUN`, но доводи локальный automation и tests до готовности. Не отправляй пользователю сборку с заведомо невалидной процедурой bake.
5. Проверяй indirect diffuse contribution на world geometry и dynamic characters, smooth interpolation, transitions между областями, отсутствие light leaks и black patches. Отделяй diffuse GI от specular IBL. Не используй повышение ambient/brightness как замену GI.
6. Проведи A/B с G04, GI off/on при фиксированной exposure, и legacy lightmap on/off. Проверь color bleeding, continuity, shadowed corners, сохранение оригинальной атмосферы. Обнови stale cache logic и перезапекай изменившиеся карты.

**Автотесты:** grid bounds/counts, overflow/limits, sample validity, atlas/manifest load, interpolation fixtures, stale/corrupt fallback. GPU test — actual bake and sampling where available.  
**RC G05:** реальные per-map grids загружены и используются; непрямой свет заметен в затенённых зонах, персонажи не выглядят отдельно от окружения; нет грубых швов/утечек и непредусмотренного изменения экспозиции. Сравнить GPU/frame time и размер cache.

### G06 — Shadow mapping и soft shadows

**Зависимость:** G03; bake consistency с G04/G05. Базовая генерация корректных теней может понадобиться до bake; этот этап посвящён окончательному качеству и приёмке.

- Аудит native shadow pipeline, supported light types, caster/receiver classification, point/projected shadows, shadow atlas, filtering/bias. Определи реальные upstream controls, не выдумывай CVars.
- Проверь все RTCW surface types, включая patches, movable submodels, alpha-tested surfaces, animated characters, viewmodels. Определи, где shadow cast/receive допустим по original semantics. Интегрируй transforms и poses с тем же frame time, что и render.
- Настрой bias/filtering/softness/resolution и quality tiers. Сначала один источник/fixture, затем несколько lights, moving doors/characters, finally target map. Исправь acne, peter-panning, swimming/flicker, cutoff, shadow leaks, missing geometry и atlas overflows. Не замещай отсутствие теней затемнённой текстурой.
- После изменения baked lighting input проверь, требуется ли rebake G04/G05. Не увеличивай shadow budget без измерения GPU cost.

**Автотесты:** caster/receiver routing, shadow resource lifecycle, shader compile, atlas budget, transform tests. GPU capture: hard/soft toggles на одинаковой сцене, static/moving tests.  
**RC G06:** мягкие стабильные тени на world и dynamic geometry, без грубого отрыва, acne и мерцания; игрок сравнивает hard/soft при равных условиях. Если конкретный backend не поддерживает нужный режим, указать блокер, не выдавать другой эффект за soft shadows.

### G07 — SSAO

**Зависимость:** G02, G03, G05/G06 baseline.

- Проверь depth/normal buffers RTCW draw path и upstream SSAO integration. Upstream README документирует `r_useSSAO`, но наличие и semantics подтвердить в pinned code. Убедись, что SSAO реально попадает в нужную composition pass.
- Проверяй depth reconstruction, near/far conventions, screen-space radius/strength, viewmodel handling, alpha/transparency, edge cases, background sky, resolution scaling и temporal noise при движении.
- Согласуй material AO, baked GI и SSAO: не умножай их неконтролируемо на всё освещение; проверь влияние на indirect/direct согласно реальному pipeline.
- Подготовь quality levels и debug AO-only view. Сравни OFF/ON в статике и движении, отдельно измерь GPU cost.

**RC G07:** умеренное контактное затемнение в углах и у объектов, без грязного экрана, ореолов, shimmering и чёрной каймы вокруг viewmodel; отсутствие двойного затемнения. Проверить FPS/frametime при одинаковом preset.

### G08 — Постепенная замена / реконструкция legacy lightmaps

**Зависимость:** G01–G07, принятые lights/probes/grids/shadows/AO. Не выполняй blanket deletion lightmaps на ранних этапах.

1. Инвентаризируй world surfaces и lightmap-dependent shader stages. Для каждой области зафиксируй legacy/hybrid/modern mode, coverage современной light rig и GI. Начни с одной хорошо покрытой комнаты; зафиксируй до/после.
2. Определи, где legacy lightmap следует сохранить как fallback, где ослабить или заменить современным direct+indirect lighting. Для материалов с намеренной художественной подсветкой используй обоснованное emissive/lighting mapping, а не произвольную корректировку цветов.
3. Исключи double lighting, двойную гамму, baked shadows поверх динамических теней, неожиданное исчезновение света. Проверяй exposure и HDR input. Не меняй исходную BSP геометрию или gameplay entities ради света.
4. Расширяй coverage порциями с per-area rollback и автоматической invalidation/rebake. Поддерживай legacy preset для сравнения. Если достижение parity требует сохранить часть lightmaps, документируй это как технически обоснованный hybrid, а не незаметный обход.

**RC G08:** современное освещение заменяет/дополняет lightmaps без видимых резких границ, пересветов и потери художественной читаемости; original baseline доступен. Сравнить G07 vs G08 в каждой изменённой зоне, подтвердить gameplay regression pass.

### G09 — HDR, tone mapping, post-processing, AA и дополнительные возможности

**Зависимость:** G08 (отдельные низкоуровневые prerequisites допускаются ранее). Цель — завершить quality pass, не скрыть дефекты предыдущих стадий постобработкой.

- G09a: проверить linear HDR buffer, tone mapping, exposure, gamma/sRGB output и UI composition; сохранить neutral preset. HDR pipeline не означает HDR10 display output. Upstream документирует `r_exposure` и `r_useFilmicPostFX`; проверить реальный диапазон, behavior и backend. Не менять exposure между A/B других эффектов.
- G09b: проверить и настроить поддержанные bloom/filmic effects и color grading. Умеренная обработка без чрезмерного bloom, crush black, oversaturation, обязательного film grain или изменения читаемости HUD. Реализовывать только фактически поддержанные функции либо отдельный обоснованный инкремент.
- G09c: инвентаризировать AA modes (`r_antiAliasing` фигурирует в upstream README), motion/temporal prerequisites, jaggies, ghosting, blur и resolution scaling. Включить TAA только если найден корректный implementation path, motion vectors и история. Протестировать UI/viewmodel и сцену в движении.
- G09d (расширение, не обязательное для первого production baseline): локальный volumetric lighting/fog, volumetric shadows, SSR/planar reflections, advanced particles, parallax, ray-tracing GI и прочие эффекты — только после capability audit и оценки ROI. На каждый эффект выделять отдельный `G09d-N` с доказанными backend support и конкретным test fixture, реализацией, GPU timing, A/B candidate. Не переносить старые Rend2 дефекты/параметры как готовое решение. Если локальный volumetric реализуется — проверять local volume bounds, falloff, occlusion, temporal stability, intersection artifacts, camera-inside-volume и отсутствие влияния за пределами источника. Никакой обязательной реализации всех экспериментальных эффектов без оценки осуществимости.

**RC G09a/b/c/d:** выпускай независимые проверяемые candidates по подэтапам, если эффект существенно меняет кадр. Проверка при фиксированных scene/settings и в движении. Только реально выполненные эффекты включай в final capability table.

### G10 — Производительность, стабильность, интеграционная приёмка графики

- Сравни RTCW NextGen Legacy / NextGen и существующий RTCW Rend2 на том же ПК, одной сцене, разрешении, FOV и сопоставимых настройках. Если точное сравнение невозможно — объясни различия. Не выдумывай benchmark baseline.
- Автоматизируй capture: fixed camera/replay route, warm-up (например 30 секунд), не менее 3 повторов одинакового прогона (ориентир 60 секунд), log GPU/CPU/driver/backend/preset. Измеряй median FPS, 1% low с документированной формулой, p95/p99 frametime, GPU/CPU timing, VRAM/system RAM, load/bake time и размер cache. Для отсутствующих метрик укажи причину. Учитывай vsync/frame cap и dynamic resolution.
- Установи рабочий бюджет после первого измерения ПК владельца. Предварительный regression trigger: ухудшение p95 frametime более 10% относительно принятого сопоставимого baseline на том же preset требует расследования/обоснования; это не жёсткое требование к дорогостоящему вновь включённому эффекту и не обещание FPS. Для новых эффектов отдельно измеряй cost и определяй trade-off. 60 FPS/16.67 ms — ориентир, а не универсальный критерий без знания hardware.
- Исправь наиболее дорогие draw submissions, visibility/culling, shader permutations, GPU resource lifetime, overdraw, light/shadow budget, texture memory, stutter и caching. Не меняй simulation tick или AI quality ради FPS. Не ухудшай визуал незаметно.
- Сформируй validated presets `Legacy`, `NextGen Balanced`, `NextGen High` (названия условны), fallback при недоступных features, безопасные defaults, README controls и known issues.
- Выполни полный regression P01–P06 и G01–G09: прохождение первой карты, save/load, transition, original scripts, rendering, bake validity, quality switching, repeated restart. Сравни до/после на репрезентативных кадрах, без неподтверждённого заявления «на голову выше Rend2».

**Gate G10:** пользователь принял графику `escape1` и gameplay regression; данные benchmark и известные ограничения зафиксированы; candidate может стать **Clean Graphics Prototype**. Это ещё не production всей кампании.

## 8. Phase C01–C03 — Масштабирование на оригинальную кампанию

Не копируй ручные фиксы `escape1` на все карты без проверки. После G10:

### C01 — Инвентаризация и автоматическая конвертация

- Из локальных законных PK3 получи точный список SP maps, порядок campaign progression, script/AI/nav/assets dependencies, material classes, level-specific special cases. Не полагайся на неполный вручную составленный список из интернета.
- Создай campaign compatibility matrix: map, load, geometry, collision, scripts, AI, objectives, audio/cinematics, save/load, transition, material coverage, light rig, probes/grid bake, performance, user acceptance.
- Автоматизируй scan -> convert -> validate -> build cache -> bake (при доступном GPU) -> reload -> smoke -> report. Используй content hash, incremental regeneration, error summary, per-map overrides; никогда не перезаписывай оригинальные данные.
- Группируй карты по технологическим рискам: indoor/outdoor, water/fog, dynamic objects, large BSP, scripted scenes, специальные эффекты. Выбери по одному representative map на группу, а затем масштабируй.

### C02 — Кампания, coverage и регрессии

- Для каждой карты сначала докажи legacy gameplay compatibility, затем graphics preset. Исправляй общий root cause, а не только конкретный classname/path. Добавляй fixture для каждого нового класса ошибок.
- Проверь все required entity/script actions и progression. Не заявляй полное прохождение по успешному `load map`. Используй scripted/replay/differential tests, затем группируй пользовательские проверки в разумные игровые checkpoints по главам.
- Проверяй переходы, persistence, save migration в поддерживаемых версиях NextGen, перезапуск уровня, звук, cinematics, HUD, locale и меню. Не модифицируй original missions, чтобы обойти портирование.
- Перезапекай только изменившиеся карты; проверяй storage и время первой подготовки. Сохраняй возможность продолжать игру при отсутствии optional bake (явный degraded mode).

### C03 — Финальный candidate и production gate

- Пройди матрицу всей заявленной SP-кампании. Все P0/P1 блокеры закрыты; нет воспроизводимых crash, progression blockers, критических AI/script несовместимостей, asset corruption или major visual regressions. Любые P2/P3 ограничения явно документированы и приняты владельцем, если влияют на заявленный результат.
- Проверь чистую установку Windows x64 из release ZIP + законные RTCW data, offline startup, отсутствие обязательных Doom 3 commercial assets, safe migration, uninstall/rollback без повреждения оригинальной установки.
- Проведи полную CI validation и license/package audit. Подготовь source correspondence, versioned release notes, user guide и benchmark. Опубликуй final RC и передай владельцу final acceptance card.
- Только после фактической приёмки заявленного объёма — `v1.0.0` / Clean Production Release всей кампании. Если проверена часть кампании, называй релиз соответственно (`preview`, `prototype`, `chapter preview`), а не full production.

## 9. Унифицированные правила испытаний и Definition of Done

### 9.1. Матрица обязательных проверок

| Gate | Проверка | Доказательство |
|---|---|---|
| A | Source audit, pinned SHA, scope, licenses | ADR / inventory / diff |
| B | Windows x64 configure + build, shader build | CI job URL/log/exit code |
| C | Unit, integration, parser safety, regression | Test results, counts, actual skips |
| D | Packaging, clean extraction, manifest, hashes | ZIP validation, SHA-256, asset audit |
| E | GPU/real renderer smoke, A/B, perf | Реальный capture/benchmark или `NOT_RUN` с причиной |
| F | Игровая функциональная/визуальная проверка | Явный результат владельца для данного RC SHA |
| G | Promotion | Verified artifact identity, tag/release/PR links |

Gates A–D — обязательные для любого передаваемого candidate (исключение: отдельная диагностическая сборка с явно обозначенными ограничениями, только если это объективно необходимо). Gate E — выполняется в доступной среде; если невозможен, не считать пройденным. Gate F закрывает соответствующий in-game checkpoint. Gate G не разрешён при unresolved critical regressions. Автотесты без оригинальных assets/GPU доказывают ограниченный объём, а не полную работоспособность игры.

### 9.2. Классификация дефектов

- **P0** — security/data loss, невозможность запуска, массовый crash, повреждение original files, незаконная упаковка assets: остановка релиза.
- **P1** — блокировка прохождения, существенная несовместимость AI/physics/scripts, критическая потеря geometry/light, постоянно воспроизводимый crash: остановка продвижения затронутого этапа.
- **P2** — значимый visual/performance defect без блокировки прохождения; исправить до затронутого production scope либо явно согласовать ограничение.
- **P3** — minor polish/documentation/cosmetic: backlog с приоритетом.

### 9.3. Регрессии, A/B и объективная проверка

Для каждого графического инкремента:

1. Один accepted baseline SHA, один candidate SHA; одинаковый оригинальный content hash, карта, camera, resolution, FOV, lighting setup (кроме исследуемого изменения), exposure, quality, driver/backend, time/seed.
2. OFF/ON одного эффекта или before/after с минимальным числом изменённых переменных; не переключать все графические параметры сразу. Если эффект зависит от других, зафиксируй dependencies.
3. Проверить минимум static, motion, representative worst case и отсутствие regression ранее принятых effects. Для semantic changes — differential game trace. Для performance — одинаковые warm-up/route, несколько runs.
4. Записать actual observation и PASS/FAIL/NOT_RUN. Pixel diff пригоден для детерминированных synthetic captures; для реальных GPU images используй обоснованные tolerances и ручную визуальную оценку. Не подгоняй пороги после FAIL без причины.
5. Если владелец подтверждает исчезновение дефекта (например, артефакта локального volumetric), добавь regression scenario, сохраняй его в последующих сборках и не изменяй исправление при promotion без повторной проверки.

## 10. Releases, игровые checkpoints и Clean Production Promotion

### 10.1. Виды релизов и доставка

- **CI artifact:** автоматический ZIP для инженерной проверки, необязательно публиковать в GitHub Releases.
- **Test Candidate / Release Candidate (RC):** предназначен для конкретной игровой приёмки, published pre-release либо доступный CI artifact. Используй версии, например `v0.1.0-p02-rc.1`, `v0.2.0-g04-rc.1`, `v0.2.0-g04-rc.2`. Не переиспользуй занятый тег. Не назначай `latest` тестовым RC.
- **Clean accepted milestone:** принятый baseline конкретного прототипа/эффекта, например `v0.2.0-g04` (название может быть Clean Production для данного ограниченного milestone, но явно укажи scope; не вводи в заблуждение насчёт всей игры).
- **Clean Production Release:** стабильный, проверенный релиз заявленного production scope; `v1.0.0` — только после C03, или существующая version policy repo.

Каждый кандидат формируй из конкретного чистого checkout, pin toolchain и build flags. Не включай случайные локальные файлы, secrets, original game assets, экспериментальные debug defaults. Оставь доступные диагностические toggles, если они не активны по умолчанию; удаление debug tooling не должно ломать принятые бинарники. Символы можно предоставить отдельно при допустимом объёме.

**Рекомендуемый package:** `RTCW-NextGen-<version>-win-x64.zip`, бинарники и нужные redistributable files согласно лицензиям, engine resources, launcher, default presets, `README`, `CHANGELOG`, `BUILD-MANIFEST.json`, `THIRD-PARTY-NOTICES`, `TEST-CARD.md`, `SHA256SUMS.txt` (checksum для ZIP — отдельным asset, чтобы избежать self-reference). Build manifest: source SHA, upstream SHA, toolchain, backend, config, build ID, content/cache compatibility version. Не включай коммерческие данные. Не вынуждай владельца собирать игру вручную.

### 10.2. Готовность к передаче владельцу

Выпускай пользовательский candidate, когда инженерно обоснованно ожидаешь, что конкретная доработка работает: пройдены A–D; выполнены возможные E, нет известных блокирующих дефектов; scope мал и результат можно проверить игровым сценарием; отсутствующие GPU/asset checks явно обозначены. Не передавай каждый промежуточный commit или неуспешную сборку. Если нужен реальный GPU для первого подтверждения, называй release `READY_FOR_GAME_TEST`, а не «эффект проверен и исправлен».

**Шаблон TEST-CARD.md (создавать автоматически для каждого checkpoint):**

```markdown
# RTCW NextGen — Game Acceptance Card
- Candidate / tag:
- Release or artifact URL (actual):
- Source commit SHA:
- Build SHA-256:
- Previous accepted baseline:
- Phase / task / defect ID:
- What is implemented:
- Expected visible result:
- Changes not included / known limitations:
- Automated tests: PASS / FAIL / NOT_RUN (links and counts)
- GPU test status / environment limitations:

## Install and start
1. Download and extract ZIP into a NEW directory.
2. Run supplied launcher, point it to existing RTCW installation if needed.
3. Select named test scenario / preset; launcher prepares local cache and bake if required.

## In-game checks
| ID | Scenario / exact location or reproducible setup | Action | Expected | Result |
|---|---|---|---|---|
| T01 | ... | ... | ... | |
| T02 | ... | ... | ... | |
| R01 | Previously accepted behavior | ... | No regression | |

## Feedback
ACCEPT / REJECT / PARTIAL; candidate tag; failing IDs; short observations.
Attach screenshot/log only if useful; include crash log if a crash occurred.
```

Обычный checkpoint должен содержать короткий конкретный сценарий (ориентир 5–15 минут для одного эффекта, не обещание времени), понятные настройки и ожидаемую разницу. Для campaign acceptance допускаются более длительные игровые проверки. Все пути/команды и места теста должны соответствовать фактической сборке, а не быть placeholders. При необходимости предоставь toggle и compare key для эффекта через реальную поддерживаемую конфигурацию/launcher.

### 10.3. Реакция на результат пользователя

- **ACCEPT:** зафиксируй exact candidate tag/SHA, checksum и принятый scope в acceptance ledger. Проверь, что не было изменений между проверенным и продвигаемым артефактом. Продвигай milestone по §10.4. Затем продолжай следующую зависимую задачу в доступной сессии либо оставь точный `NEXT_TASK` для следующей.
- **REJECT:** воспроизведи проблему с logs/screenshots и baseline comparison, установи root cause, добавь regression test, исправь только относящийся код, повтори CI, выпусти новый RC с новым тегом. Предыдущий RC не перезаписывай.
- **PARTIAL:** раздели принятые и непринятые проверки; не продвигай непроверенный scope; исправь оставшееся или изолируй feature behind disabled default, если это допускает принятие другой независимой части. Приёмку фиксируй явно.
- Если отзыв не содержит exact SHA/tag, сопоставь его с последним однозначным candidate. Если опубликовано несколько разных candidate и результат неоднозначен, уточни только этот факт. Не считай отсутствие ответа согласием.

### 10.4. Clean Production Release / Promotion после успешного теста

**Правило:** максимально сохранять именно проверенный результат. Сначала оцени, является ли accepted RC уже чистым и пригодным для promotion. Не делай refactoring, «улучшение» эффекта, upgrade upstream, compiler flags или новую сборку только ради названия Clean Production.

**Вариант A — предпочтительный: artifact promotion без изменения runtime.**

1. Проверь, что accepted RC содержит Release binary, production-safe defaults, верные лицензии и manifest, проходит A–F, а SHA-256 и commit известны. Проверь доступность exact approved ZIP.
2. Через разрешённый PR/merge process интегрируй принятую ревизию в соответствующую стабильную линию, не меняя accepted content. Если merge создаёт новый commit, документируй связь accepted source SHA и merge SHA; убедись в эквивалентности содержимого и checks. Не выдавай merge commit за build SHA.
3. Создай новый stable milestone tag на exact accepted source commit (или по существующей политике с доказанной идентичностью), опубликуй тот же ZIP/артефакт и checksum, release notes с ссылкой на принятую сборку и status. Допускается изменение release metadata, но не бинарников, игровых defaults, bake generator или ресурсов в принятом ZIP. Если политика репозитория позволяет promotion самого релиза без изменения tag/artifacts, используй её и отметь scope.
4. Проверь реальный stable release URL, published assets, checksum equality и tag target; не удаляй/перезаписывай прошлые RC. Не помечай прототип всей кампанией. При необходимости оставить rollback на предыдущий принятый релиз.

**Вариант B — Clean rebuild требуется объективно.**

Если RC содержит диагностический код/defaults, непригодный package, неустранимые metadata inconsistencies или другое production-blocking обстоятельство, создай отдельную cleanup ветку от accepted SHA. Удали только необходимое, обоснуй каждый diff, не меняй принятую функциональность. Повтори CI и проверку упаковки. Если изменилась хотя бы одна runtime составляющая (binary, DLL, shader, asset, default config, lighting/bake generator и т.д.) — выпусти новый clean RC и повтори затронутую игровую приёмку. Не называй изменённую сборку автоматически принятой. Если изменения исключительно внешние release notes/metadata и идентичность runtime доказана, повторный игровой тест не нужен. При изменении ZIP только из-за документации подтвердить identity всех runtime files и задокументировать новый ZIP hash.

**Результат promotion:** укажи stable version/tag, commit SHA, accepted RC, сравнение hashes, CI status, release URL и scope. Если не хватает полномочий публикации — укажи фактический blocker; подготовь workflow/PR, не заявляй, что релиз создан.

## 11. Постоянный Handoff между задачами Codex Cloud

Создай или переиспользуй структуру (не дублируй существующую документацию):

```text
AGENTS.md                         # краткие устойчивые правила; ссылка на Handoff
 docs/rtcwnextgen/
   HANDOFF.md                     # этот документ или его согласованная версия
   STATUS.md                      # актуальное состояние, NEXT_TASK, blocker
   ROADMAP.md                     # этапы и task IDs / dependencies
   architecture.md               # source map, interfaces, architecture
   adr/                           # решения и экспериментальные результаты
   COMPATIBILITY.md               # gameplay/material/renderer coverage
   CAMPAIGN-MATRIX.md              # per-map gates
   ACCEPTANCE.md                  # ledger RC / user result / promotion
   TESTING.md                     # CI, fixtures, benchmark, in-game tests
   KNOWN-ISSUES.md                # defects and reproducible scenarios
   RELEASE-PROCESS.md             # workflow and artifact promotion
 scripts/                         # build, test, package, local prepare/bake
 tests/                           # legal synthetic fixtures / regression harness
 .github/workflows/               # CI and releases, names follow repo conventions
```

`AGENTS.md`: кратко зафиксируй autonomous workflow, pinned sources, branch safety, license restrictions, build/test commands, Definition of Done, instruction to read `docs/rtcwnextgen/HANDOFF.md` and `STATUS.md`. Не перезаписывай существующие инструкции и не прячь противоречия: добавь проектный раздел. Если task scope требует локального `AGENTS.md`, соблюдай его. Большой Handoff храни отдельно, чтобы контекст не переполнялся.

### 11.1. STATUS.md — обязательная запись после каждого завершённого рабочего инкремента

```markdown
# RTCW NextGen — Current State
- Date / task ID:
- Current branch and source SHA:
- Pinned upstream commits:
- Last accepted milestone / RC / exact artifact hash:
- Current phase and status:
- Completed changes (actual paths):
- Automated checks run (actual commands + result):
- GPU / game tests run or NOT_RUN with reason:
- Pending user acceptance (tag and test card):
- Blockers / risks / known regressions:
- NEXT_TASK: one specific actionable task ID and its dependencies
- How to resume: exact verified build/test commands, relevant files/ADR
```

Храни release acceptance ledger в репозитории, а не только в chat history. Не отмечай последующие фазы готовыми при частично завершённой зависимости. При возобновлении задачи сначала прочитай ledger/status и фактический Git history; сверяй user feedback и candidate identity.

### 11.2. Минимальный backlog (стартовая очередь)

| ID | Deliverable | Depends on | Checkpoint |
|---|---|---|---|
| P00 | Audit, branch, upstream pin, Windows CI, package | — | Auto gate |
| P01 | RTCW boot mode / VFS / native fixture | P00 | R01 |
| P02 | Native RTCW BSP render world / legacy textures | P01 | R02 |
| P03 | RTCW collision + movement | P02 | R03 |
| P04 | SP gameplay/cgame/entities/audio/HUD bridge | P03 | R04 |
| P05 | AI, scripts, save/load, progression | P04 | R05 |
| P06 | Accepted first-map gameplay baseline | P05 | Prototype RC |
| G00 | Capability matrix, A/B tools, baseline | P06 | Auto gate |
| G01 | Material adapter | G00 | Graphics RC |
| G02a | Normal maps | G01 | Graphics RC |
| G02b | PBR/RMAO | G02a | Graphics RC |
| G03 | Direct light rig | G01/G02 | Graphics RC |
| G04 | Map-specific environment probes / IBL | G02b/G03 | Graphics RC |
| G05 | Irradiance volumes / GI | G03/G04 | Graphics RC |
| G06 | Final shadow quality / soft shadows | G03/G05 | Graphics RC |
| G07 | SSAO | G05/G06 | Graphics RC |
| G08 | Incremental lightmap migration | G01–G07 | Graphics RC |
| G09a–c | HDR/post-FX/AA, independently | G08 | Graphics RC per change |
| G09d-N | Optional graphics extension | Capability audit | Separate RC if undertaken |
| G10 | Optimization / first-map graphics acceptance | G01–G09 mandatory scope | Clean Graphics Prototype |
| C01 | Map inventory / batch conversion and bake | G10 | Auto + representative map |
| C02 | Full campaign compatibility and graphics coverage | C01 | Chapter RCs |
| C03 | Final stable release, complete acceptance | C02 | Production RC -> stable |

## 12. Первое задание Codex Cloud — начать немедленно

Не реализуй весь roadmap одним огромным PR. Начни с **P00**, выполни аудит выбранного репозитория, проверь точную исходную ревизию и структуру, выбери безопасный способ интеграции upstream, создай/подготовь отдельную ветку, проверь license/build prerequisites и заложи реальную CI-основу. Если в репозитории уже есть выполненные этапы, проверь доказательства и продолжи с первого неподтверждённого этапа, не повторяя принятые изменения.

В рамках доступной сессии:

1. Выполни P00 полностью настолько, насколько позволяет окружение. Создай устойчивые документы состояния и задачи, а не только текст ответа.
2. При прохождении gate P00 перейди к P01, затем к следующему независимому инкременту до первого объективно необходимого game checkpoint или блокера. Не требуй предварительного одобрения roadmap.
3. Создай PR/CI artifact/release candidate доступным разрешённым способом. Предоставь фактические ссылки и команды. Если сборка Windows запускается через CI, по возможности проверь её завершение и используй реальные logs; не отмечай успех по одному лишь запуску workflow.
4. Если время/ресурсы сессии заканчиваются, оставь чистый коммит или понятный незавершённый diff, обнови `STATUS.md` и конкретный `NEXT_TASK`; не выдумывай результат. Не останавливайся на перечислении рекомендаций, когда возможно выполнить код/тесты.

**Формат каждого итогового ответа Codex владельцу:**

```text
Phase / task:
State: AUTO_VERIFIED / READY_FOR_GAME_TEST / BLOCKED / ...
What changed: 3–7 concrete items, paths / PR / commit
Checks: actual results, including NOT_RUN
Candidate: actual URL, tag, source SHA, checksum (if built)
User action: none OR one short test card OR one specific access blocker
Next: exact task ID and dependency
```

**Основное требование автономности:** владелец не является оператором сборочной системы. Codex отвечает за весь инженерный цикл, а владелец участвует главным образом в реальной игровой приёмке и необходимых разрешениях. Не публикуй неподтверждённую сборку как стабильную. Не обещай продолжение работы между сессиями без нового запуска. Сохраняй оригинальный RTCW gameplay, доказывай каждый графический эффект и продвигай только принятый результат.

## 13. Проверяемые исходные ориентиры

Ниже — отправные ссылки, а не замена source-code audit. Codex должен подтверждать фактические команды, структуру и возможности по выбранному SHA.

- [RBDoom3BFG upstream README](https://github.com/RobertBeckebans/RBDOOM-3-BFG) — architecture/features, PBR RMAO channel layout, environment probes, light grids, bake commands, Windows toolchain, CVars, `dmap`.
- [RBDoom3BFG release notes](https://github.com/RobertBeckebans/RBDOOM-3-BFG/blob/master/RELEASE-NOTES.md) и [releases](https://github.com/RobertBeckebans/RBDOOM-3-BFG/releases) — история функций и backend changes, не доказательство их availability в выбранном commit.
- [RBDoom3BFG mod unit tests](https://github.com/RobertBeckebans/RBDOOM-3-BFG_mod_unittests) — референс test scenes, использовать только после license verification.
- [iortcw upstream](https://github.com/iortcw/iortcw), [SP code](https://github.com/iortcw/iortcw/tree/master/SP/code), [SP README](https://github.com/iortcw/iortcw/blob/master/SP/README.txt) — эталон оригинальной SP-логики и форматов.
- [OpenAI Codex prompting guide](https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide) — repository instructions и agent workflow; конкретные возможности окружения проверять на месте.
- [GitHub Actions workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax), [GitHub Actions repository settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository) — permissions, workflow policy и CI/CD.

**Открытые вопросы для P00/G00 (не требовать ответа владельца заранее):** exact repository state and access; pinned upstream/toolchain; dependency on proprietary Doom assets; runtime render-world bridge feasibility; availability of GPU and legally accessible assets; performance on owner hardware; optional effects availability. Это обязательные проверяемые инженерные риски, а не подтверждённые возможности будущего порта.
