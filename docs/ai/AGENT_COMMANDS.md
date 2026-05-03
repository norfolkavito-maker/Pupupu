# AGENT_COMMANDS — полезные copy‑paste команды

## Start full task

```text
# Read rules + master task
cat AGENTS.md
cat docs/ai/MASTER_TASK.md
cat docs/ai/CONTEXT_MAP.md
ls -la docs/ai/prompts

# Run verification (choose one)
./scripts/agent-verify.ps1
bash scripts/agent-verify.sh
```

## Continue after interruption

```text
# Inspect current repo state
git status --short
git --no-pager log --oneline -5

# Re-load context map before broad exploration
cat docs/ai/CONTEXT_MAP.md

# Re-run verification
./scripts/agent-verify.ps1
bash scripts/agent-verify.sh
```

## Force self-review

```text
# Review changed files
git status --short
git --no-pager diff

# Re-run tests
python -m pytest -q
python -m unittest discover -s tests -p "*_unittest.py"
```

## Fix CI/test failure

```text
# Run failing test suite locally
python -m pytest -q --tb=long

# If needed, narrow down
python -m pytest -q -k "<pattern>" --tb=long
```

## Stop random edits

```text
# Reset unstaged changes
git restore .

# Reset staged changes
git restore --staged .
```
