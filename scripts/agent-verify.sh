#!/usr/bin/env bash
set -euo pipefail

echo "Agent verification starting"
echo "cwd: $(pwd)"

if command -v git >/dev/null 2>&1; then
  echo "git: $(git --version)"
  git status --short || true
fi

has_python_project=0
if [[ -f "pyproject.toml" || -f "requirements.txt" || -f "setup.py" || -d "tests" ]]; then
  has_python_project=1
fi

if [[ "$has_python_project" -eq 1 ]] && command -v python >/dev/null 2>&1; then
  echo "python: $(python --version)"
  python -m compileall .

  if [[ -d "tests" ]]; then
    python -m unittest discover -s tests -p "*_unittest.py"
  fi

  if [[ -f "pytest.ini" ]] || ([[ -f "pyproject.toml" ]] && grep -qi "pytest" pyproject.toml); then
    python -m pytest -q
  fi
fi

if [[ -f "package.json" ]] && command -v npm >/dev/null 2>&1; then
  echo "node: $(node --version 2>/dev/null || true)"
  echo "npm: $(npm --version)"
  if [[ -f "package-lock.json" ]]; then
    npm ci
  else
    npm install
  fi
  if node -e 'const p=require("./package.json");process.exit(p.scripts&&p.scripts.lint?0:1)'; then
    npm run lint
  fi
  if node -e 'const p=require("./package.json");process.exit(p.scripts&&p.scripts.test?0:1)'; then
    npm test
  fi
  if node -e 'const p=require("./package.json");process.exit(p.scripts&&p.scripts.build?0:1)'; then
    npm run build
  fi
fi

if command -v dotnet >/dev/null 2>&1; then
  if ls ./*.csproj >/dev/null 2>&1 || find . -maxdepth 4 -name "*.csproj" | head -n 1 | grep -q .; then
    echo "dotnet: $(dotnet --version)"
    dotnet restore
    dotnet build --no-restore
    dotnet test --no-build
  fi
fi

if [[ -f "Cargo.toml" ]] && command -v cargo >/dev/null 2>&1; then
  echo "cargo: $(cargo --version)"
  cargo test
fi

echo "Agent verification passed"
