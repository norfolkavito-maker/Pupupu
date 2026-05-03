# Agent Workflow: 02 — Test engine performance

# PROMPT 02 — Ускорение самого теста доступа без урезания стратегий/доменов

## Комментарий для пользователя

Давать после стабилизации багов. Это не “проверять меньше”, а **быстрее проверять тот же объём**: параллельные доменные проверки внутри одной стратегии, compact output, DNS cache, дедупликация одинаковых команд, deadline, отмена.

## Правила для агента

- Не менять глобально меню.
- Не урезать Full/Test All.
- Не запускать несколько winws-стратегий одновременно.
- Один winws на стратегию, внутри — параллельные проверки доменов.
- Не печатать тысячи строк в консоль по умолчанию.
- Подробные результаты писать в файл.
- Добавить возможность отмены теста.
- Не делать `winws2` дефолтом.

---

<role>
You are a senior Python/Windows performance engineer.
The user does NOT want a global menu redesign now.
Work inside the current menu structure.
The goal is to speed up the technical execution of strategy access tests, not to reduce functionality.
</role>

<context>
DedZapret already has:
- Test all strategies with progress
- strategy preflight
- JSONL telemetry
- latest ranking
- Flowseal/runtime diagnostics

Problem:
Testing all strategies can be slow because domain access checks are sequential, timeouts are expensive, DNS is repeated, and console output may be too verbose.

The user is OK with testing all strategies and all selected domains.
The task is to make the checking engine faster and output more efficient.
</context>

<main_goal>
Optimize strategy test execution speed while keeping current menu structure.

Do not globally reorganize menus.
Do not remove Full/Test All.
Do not invent new strategies.
Do not run multiple winws strategies at the same time.
</main_goal>

<critical_rules>
- Do NOT redesign the main menu.
- Do NOT reduce Full/Test All functionality.
- Do NOT force only 5–8 domains.
- Do NOT make winws2 default.
- Do NOT run several winws strategies simultaneously.
- Do NOT log secrets.
- Preserve existing result files and telemetry.
</critical_rules>

<tasks>

<task id="1" title="Audit current test flow">
Find where these happen:
- strategy start/stop
- domain checks
- DNS resolve
- HTTP checks
- per-domain output
- result writing

Confirm:
- winws starts once per strategy, not once per domain.

If winws is started per domain anywhere, fix it.

Correct flow:
Strategy v7:
1. preflight
2. start winws once
3. check all domains
4. stop winws
5. save result
</task>

<task id="2" title="Bounded parallel domain checks inside one active strategy">
Implement concurrency for domain access checks.

Rules:
- Only one strategy/winws active at a time.
- Domain checks within that strategy can run concurrently.
- Default concurrency: 8.
- Configurable: 1, 4, 8, 16.
- Must work on Windows.
- Must not require extra admin rights beyond existing winws needs.
</task>

<task id="3" title="Test speed settings under existing strategy test menu">
Do not redesign menu globally.

Add:
Настройки скорости теста:
1) Параллельные проверки доменов: 8
2) Connect timeout
3) Read timeout
4) Общий лимит на домен
5) Общий лимит на стратегию
6) Подробный вывод в консоль: ON/OFF
7) DNS cache: ON/OFF
8) Deduplicate одинаковые стратегии: ON/OFF

Store settings in existing config/state mechanism if appropriate.

Recommended defaults:
- concurrency: 8
- connect_timeout: 2.0 sec
- read_timeout: 3.0 sec
- total_domain_timeout: 4.0 sec
- max_strategy_time_sec: 90 sec
- detailed_console_output: false
- dns_cache: true
- deduplicate_equivalent_strategies: true
</task>

<task id="4" title="Optimize HTTP access check">
Do not download full pages.

Use:
- lightweight GET
- stream/small read
- do not download full body
- separate connect/read timeout if possible

Result must distinguish:
- OK
- HTTP error
- DNS error
- connect timeout
- TLS error
- read timeout
- unknown error

If using requests:
- use Session carefully.
- If sharing Session across threads is unsafe, use per-worker Session.

Do not add heavy dependencies unless clearly justified.
</task>

<task id="5" title="DNS cache during sweep">
Implement in-memory DNS cache for one sweep:
- key: domain
- value: result/error/timestamp
- TTL: 5–15 minutes
- optional setting to disable

Goal:
Avoid resolving the same domain again for every strategy.

Do not persist DNS cache unless needed.
</task>

<task id="6" title="Efficient console output">
Detailed per-domain printing can slow Windows console.

Add output modes:
- compact: update one progress line per strategy every 0.3–0.5 sec
- detailed: print every domain result

Default: compact.

Still write detailed domain results to file/JSONL.

Example compact output:
`[Strategy 03/42] v7 | domains 18/46 | OK 14 | FAIL 4 | elapsed 21s`

At end of strategy, print summary:
`v7: OK 28/46 | avg 420 ms | score 82 | failed: discord.com, ea.com`
</task>

<task id="7" title="Preflight before network tests">
Before running sweep:
- validate all strategies
- skip INVALID from network check
- include them in final table as INVALID with missing assets

This is not reducing scope because invalid strategies cannot be tested anyway.
</task>

<task id="8" title="Deduplicate equivalent strategies">
Before network checks:
- build normalized command signature for each strategy
- if two strategies resolve to the same engine+args, test only one
- copy result to duplicates with `duplicate_of` field

Final table should show `duplicate_of` or mention duplicates in summary.

Default:
- deduplicate ON
</task>

<task id="9" title="Strategy hard deadline">
Add `max_strategy_time_sec`.

If exceeded:
- cancel remaining domain checks for that strategy
- stop current winws
- mark strategy `partial_timeout`
- save partial results
- continue next strategy
</task>

<task id="10" title="Cancellation">
Support stopping the running sweep:
- Ctrl+C
- Q/Esc if current input system supports non-blocking safely

On cancel:
- stop current winws
- save partial results
- write partial ranking
- show: `Тест остановлен пользователем`
</task>

<task id="11" title="Metrics display fix">
If TCP/DNS/PING/UDP were not measured in this optimized run, show:
`N/A`

Do not show:
`0/N`
</task>

<task id="12" title="Preserve result files">
Existing outputs must continue working:
- `strategy_runs.jsonl`
- `latest_strategy_ranking.json`
- `latest_strategy_ranking.txt`
- `results_all_strategies_*.txt`

Add details files if needed:
- `results/details_strategy_<id>.jsonl`
- `results/test_sweep_details_<timestamp>.jsonl`
</task>

<task id="13" title="Tests">
Add unit/mocked tests:
- domain checks execute with bounded concurrency
- concurrency setting respected
- invalid strategies are skipped before network
- duplicate strategies reuse result
- compact output does not print every domain
- detailed output does print every domain
- max_strategy_time produces partial_timeout
- cancellation saves partial results
- unmeasured metrics display N/A
- no multiple winws strategies active simultaneously
- result files are still written

No real network in unit tests.
Use mocks/fakes.
</task>

</tasks>

<do_not>
- Do not redesign the whole main menu.
- Do not reduce Full/Test All functionality.
- Do not force only 5–8 domains.
- Do not make winws2 default.
- Do not run several winws strategies simultaneously.
- Do not log secrets.
- Do not break existing result files.
</do_not>

<commit_plan>
Use small commits:
1. `perf(test): add bounded parallel domain checks`
2. `perf(test): add compact progress renderer and speed settings`
3. `perf(test): add DNS cache deadlines and duplicate strategy reuse`
4. `fix(test): show N/A for unmeasured metrics and save partial results`
</commit_plan>

<expected_final_response>
Report:
1. What was optimized.
2. Whether winws starts once per strategy.
3. Concurrency default.
4. Timeout defaults.
5. Example compact output.
6. Result files written.
7. Tests added.
8. Exact test commands/results.
9. Windows manual checklist.
10. Known limitations.
</expected_final_response>
