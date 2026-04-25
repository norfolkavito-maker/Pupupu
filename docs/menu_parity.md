# Menu parity audit

Goal: keep menu feature parity across refactors. If a feature is temporarily
unavailable (e.g. runtime missing), the menu item must remain visible and show
"недоступно" with a clear explanation on selection.

## Main menu (StressOzz-like)

| Item | v0.3.1 portable | v0.3.3 | Notes |
|------|-----------------|--------|-------|
| 1 Start/Stop Zapret | ✅ | ✅ | Requires runtime + admin rights |
| 2 Strategies menu | ✅ | ✅ | |
| 3 Strategy tests | ✅ | ✅ | Requires runtime for real runs |
| 4 TG WS Proxy | ✅ | ✅ | |
| 5 DoH menu | ✅ | ✅ | |
| 6 Discord menu | ✅ | ✅ | |
| 7 Hosts menu | ✅ | ✅ | |
| 8 Game/program launcher | ✅ | ✅ | |
| 0 System menu | ✅ | ✅ | |

## System menu

| Item | v0.3.1 portable | v0.3.3 | Notes |
|------|-----------------|--------|-------|
| 1 System info | ✅ | ✅ | |
| 2 Check upstream updates | ✅ | ✅ | |
| 3 Apply updates (sync) | ✅ | ✅ | |
| 4 blockcheck | ✅ | ✅ | Requires runtime |
| 5 blockcheck2 | ✅ | ✅ | Requires runtime |
| 6 QUIC block toggle | ✅ | ✅ | |
| 7 TCP timestamps enabled | ✅ | ✅ | |
| 8 TCP timestamps disabled | ✅ | ✅ | |
| 9 Flush DNS | ✅ | ✅ | |
| 10 Backup (zip) | ✅ | ✅ | |
| 11 Restore backup (zip) | ✅ | ✅ | |
| 12 Update exclude + RKN | ✅ | ✅ | |
| 13 Key setup ("под ключ") | ✅ | ✅ | |
| 14 Check runtime | ❌ | ✅ | Added in v0.3.3 |
