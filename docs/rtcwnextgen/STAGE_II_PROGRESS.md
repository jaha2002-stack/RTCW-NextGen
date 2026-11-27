# Прогресс Native Playable Level Prototype

- Ветвь `rtcwnextgen/stage-ii-native-level-remaster` создана от `2525b4c175c7602c984f298a0f38381f9ffae9ad`. Предыдущие проверки PK3, путей, заголовка IBSP и ссылок поверхностей вошли в основу. [Предыдущий Windows CI](https://github.com/jaha2002-stack/RTCW-NextGen/actions/runs/45919540004)
- `compile-native-level.py` компилирует авторский `.map` в отдельный каталог. На тесте получены `.proc`, `.cm` и `.aas48`. Сверены хеши результатов, байты входного файла и отказ при отсутствии запрошенной навигации. У Valve 220 подтверждены границы помещения `[-128, 128] × [-128, 128] × [0, 128]` и назначение материала панели.
- RBDoom3BFG загрузил скомпилированный `.proc` в нативный render world. Vulkan validation прошёл, снимок после resize имеет 704×512, красная панель впереди, синяя стена сбоку, выход по Escape штатный. Локальный тест использовал только авторский MAP, MTR, TGA, настройки AAS и шейдеры движка.
- Из точки `(-40, 0, 48)` нативные коллизии остановили трассу у стены на `x=127,75` и у пола на `z=0,25` с учётом допуска движка в 0,25. Короткая трасса дошла до `(-8, 0, 48)` с долей `1,0`.
- Linux Release собран. Прошли 17 тестов `test-project.py`, проверка кода CI и проверка исходного двухцветного режима. Диагностическая Windows-упаковка включает `tools/compile-native-level.py`. [Windows CI ветви](https://github.com/jaha2002-stack/RTCW-NextGen/actions?query=branch%3Artcwnextgen%2Fstage-ii-native-level-remaster)

**Следующая независимая задача** — проверить связь двух авторских областей, видимость через дверной проём и AAS-маршрут. [План](STAGE_II_IMPLEMENTATION_PLAN.md) · [Матрица приёмки](STAGE_II_ACCEPTANCE_REPORT.md)
