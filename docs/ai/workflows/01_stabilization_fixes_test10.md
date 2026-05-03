# Agent Workflow: 01 — Stabilization fixes (test.10 audit)

# PROMPT 01 — Stabilization fixes по аудиту DedZapret test.10

## Комментарий для пользователя

Давать агенту первым. Это не про новые функции, а про исправление реальных багов из логов `v0.3.5-test.10`: Flowseal, runtime assets, Problem Domains, sing-box nodes, bug report, кодировка Windows diagnostics.

## Правила для агента

- Не делать GUI/tray.
- Не менять структуру меню.
- Не добавлять новые стратегии от себя.
- Не делать `winws2` дефолтом.
- Все фиксы делать маленькими коммитами.
- После каждого блока запускать тесты.
- Не логировать секреты, ссылки подписок и raw-ноды.
- User-facing text — на русском.
- Preserve portable mode.

---

<role>
You are a senior Python/Windows systems engineer working on DedZapret / “ЗапретМенеджер на винду”.
Use the audit results from DedZapret v0.3.5-test.10.
Your task is to fix real bugs found in logs and diagnostics, not to add GUI/tray or redesign menus.
</role>

<main_goal>
Implement stabilization fixes based on the v0.3.5-test.10 audit.

Main issues from logs:
1) Problem Domains recording is broken in control test.
2) Flowseal imported strategies are still mostly INVALID because assets resolve to wrong paths.
3) Runtime fake/list repair does not pull from Flowseal upstreams.
4) v7/Gv1 can fail on missing `quic_initial_ietf.bin`.
5) Windows diagnostics output is garbled in `meta.json`.
6) sing-box health says `nodes_count=0` even when `nodes.json` exists and has size.
7) Bug report misses important strategy/node artifacts.
8) Strategy metrics show `0/N` for unmeasured metrics instead of `N/A`.
9) Preflight validator falsely treats hex/modifier args as files.
</main_goal>

<critical_rules>
- Do NOT implement tray.
- Do NOT implement GUI.
- Do NOT restructure main menu.
- Do NOT introduce V2Ray/Xray backend.
- Do NOT make winws2 default.
- Do NOT invent new original strategies.
- Keep user-facing text in Russian.
- Preserve portable mode.
- Do not log secrets.
- Use small commits.
- Run tests after each logical block.
</critical_rules>

<tasks>

<task id="1" title="Problem Domains recording">
Bug:
Control test still imports old `add_from_domain_checks` and fails.

Fix:
- Replace old import with the new Problem Domains API, or add compatibility wrapper:
  `add_from_domain_checks(ctx, checks, strategy="control")`
- `control_test` must record failed domains.
- Problem Domains must be visible as selectable domain set.
- Add/adjust unit tests.

Commit:
`fix(problem-domains): restore control test recording`
</task>

<task id="2" title="Flowseal asset resolution">
Bug:
Flowseal `imported=19`, but strategies are mostly INVALID.
Files exist under:
- `DedZapretData/data/upstreams/flowseal/bin`
- `DedZapretData/data/upstreams/flowseal/lists`

But preflight looks in `runtime/zapret` or `data/lists`.

Fix:
- Ensure imported Flowseal strategies resolve:
  - `{FLOWSEAL_BIN}` -> `DedZapretData/data/upstreams/flowseal/bin`
  - `{FLOWSEAL_LISTS}` -> `DedZapretData/data/upstreams/flowseal/lists`
- `list-general.txt` must resolve from `{FLOWSEAL_LISTS}`.
- `quic_initial_dbankcloud_ru.bin` and other Flowseal fake files must resolve from `{FLOWSEAL_BIN}`.
- Add tests for imported Flowseal strategies.

Commit:
`fix(flowseal): resolve imported assets from upstream paths`
</task>

<task id="3" title="Runtime assets repair from upstreams">
Bug:
`runtime_asset_report` shows missing:
- `tls_clienthello_max_ru.bin`
- `4pda.bin`
- `t2.bin`
- `list-general.txt`

Fix:
- Runtime repair must search not only `runtime/`, but also:
  - `DedZapretData/data/upstreams/flowseal/bin`
  - `DedZapretData/data/upstreams/flowseal/lists`
- Decide `4pda.bin` mismatch:
  - either alias `tls_clienthello_4pda_to.bin` -> `4pda.bin`
  - or correct the strategy reference if objectively wrong.
- Decide `t2.bin`:
  - source it,
  - correct strategy reference,
  - or mark unavailable clearly.
- Do not create empty fake `.bin` files.
- Do not download suspicious binaries.
- Add tests.

Commit:
`fix(runtime-assets): repair missing fake and list assets from upstreams`
</task>

<task id="4" title="v7/Gv1 quic_initial_ietf.bin">
Bug:
A strategy/overlay can fail with:
`missing quic_initial_ietf.bin`

Fix:
- Find which strategy/overlay adds:
  `--dpi-desync-fake-unknown-udp=quic_initial_ietf.bin`
- Either:
  1. add/repair this asset;
  2. replace reference with existing correct fake;
  3. if it is not a file, teach preflight not to treat it as a file.
- Add preflight test.

Commit:
`fix/runtime): resolve quic_initial_ietf fake asset for game strategy`
</task>

<task id="5" title="Windows diagnostics decoding">
Bug:
`meta.json` contains garbled `ipconfig`/`route`/`netsh` output.

Fix:
- Centralize decoding for Windows subprocess output:
  - `locale.getpreferredencoding(False)`
  - `cp866` fallback
  - `utf-8` fallback
  - `errors="replace"`
- Store `encoding_used` in diagnostics metadata.
- Add cp866 sample test.

Commit:
`fix(diagnostics): decode Windows command output correctly`
</task>

<task id="6" title="sing-box nodes health">
Bug:
`singbox_health` shows `nodes_count=0`, but `nodes.json` exists and has size.

Fix:
Add to sing-box health:
- `nodes_file_exists`
- `nodes_file_size`
- `nodes_schema_detected`
- `load_nodes_error`
- `subscriptions_count`
- `nodes_count`

If `nodes_file_exists=true` and `size>0` and `nodes_count=0`, show:
`nodes.json найден, но ноды не прочитаны. Возможна несовместимая схема файла или ошибка парсера.`

Commit:
`feat(singbox): report nodes file schema and load errors`
</task>

<task id="7" title="Bug report artifacts">
Add to bug report:
- `strategy_runs.jsonl`
- `latest_strategy_ranking.json`
- `latest_strategy_ranking.txt`
- raw `problem_domains.json`
- `problem_domains_summary.json/txt`
- masked `singbox_nodes_summary.json`

Do NOT include raw node links or raw subscription URLs.

Commit:
`chore(report): include strategy and node summaries in bug reports`
</task>

<task id="8" title="Metrics display for unmeasured checks">
Bug:
If TCP/DNS/PING/UDP metrics were not measured, results show `0/N`.

Fix:
- Show `N/A` for unmeasured metrics.
- Only show `0/N` if the metric was actually measured and failed.

Commit:
`fix(strategy-test): show N/A for unmeasured metrics`
</task>

<task id="9" title="Runtime preflight false file checks">
Bug:
Preflight treats values like these as files:
- `0x0F0F0F0F`
- `rnd,dupsid,sni=...`
- `none`

Fix:
- Only check as file path if:
  - value contains `.bin/.txt/.dat/.pem/.crt`, or
  - value contains slash/backslash, or
  - option is strictly file-based.
- Do not file-check hex/modifier values.

Commit:
`fix(runtime-preflight): avoid false file checks for modifiers`
</task>

</tasks>

<testing>
After each block:
- `python3 -m pytest -q`
- `python3 -m unittest discover -s tests -p 'test_*_unittest.py' -v`

No real network in unit tests.
Use mocks/temp dirs.
</testing>

<expected_final_response>
Report:
1. Commits created.
2. Files changed.
3. Bugs fixed.
4. Tests added/updated.
5. Exact test commands and results.
6. Windows manual checklist.
7. Known limitations.
</expected_final_response>
