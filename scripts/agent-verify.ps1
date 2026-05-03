$ErrorActionPreference = "Stop"

Write-Host "Agent verification starting"
Write-Host ("cwd: " + (Get-Location).Path)

if (Get-Command git -ErrorAction SilentlyContinue) {
  git --version | Write-Host
  try {
    git status --short | Write-Host
  } catch {
    Write-Host "git status failed (ignored)"
  }
}

$hasPythonProject = $false
if (Test-Path "pyproject.toml") { $hasPythonProject = $true }
if (Test-Path "requirements.txt") { $hasPythonProject = $true }
if (Test-Path "setup.py") { $hasPythonProject = $true }
if (Test-Path "tests") { $hasPythonProject = $true }

if ($hasPythonProject -and (Get-Command python -ErrorAction SilentlyContinue)) {
  python --version
  python -m compileall .

  if (Test-Path "tests") {
    python -m unittest discover -s tests -p "*_unittest.py"
  }

  $hasPytest = $false
  if (Test-Path "pytest.ini") { $hasPytest = $true }
  if (Test-Path "pyproject.toml") {
    $pp = Get-Content "pyproject.toml" -Raw
    if ($pp -match "pytest") { $hasPytest = $true }
  }

  if ($hasPytest) {
    python -m pytest -q
  }
}

if ((Test-Path "package.json") -and (Get-Command npm -ErrorAction SilentlyContinue)) {
  try { node --version | Write-Host } catch { }
  npm --version | Write-Host

  if (Test-Path "package-lock.json") {
    npm ci
  } else {
    npm install
  }

  $pkg = Get-Content "package.json" -Raw | ConvertFrom-Json
  if ($pkg.scripts -and $pkg.scripts.lint) { npm run lint }
  if ($pkg.scripts -and $pkg.scripts.test) { npm test }
  if ($pkg.scripts -and $pkg.scripts.build) { npm run build }
}

if (Get-Command dotnet -ErrorAction SilentlyContinue) {
  $csproj = Get-ChildItem -Recurse -Filter "*.csproj" -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($csproj) {
    dotnet --version | Write-Host
    dotnet restore
    dotnet build --no-restore
    dotnet test --no-build
  }
}

if ((Test-Path "Cargo.toml") -and (Get-Command cargo -ErrorAction SilentlyContinue)) {
  cargo --version | Write-Host
  cargo test
}

Write-Host "Agent verification passed"
