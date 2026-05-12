#!/usr/bin/env bash
# Release preflight check — verifies a built portable bundle for forbidden artifacts.
# Usage: bash scripts/release-preflight.sh [path-to-bundle-dir]
#
# If no path is given, defaults to ./bundle/DedZapret

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

errors=0
warnings=0

BUNDLE_DIR="${1:-./bundle/DedZapret}"

if [ ! -d "$BUNDLE_DIR" ]; then
    echo -e "${RED}FAIL: Bundle directory not found: $BUNDLE_DIR${NC}"
    echo "Usage: bash scripts/release-preflight.sh [path-to-bundle-dir]"
    exit 1
fi

echo "=== Release preflight check ==="
echo "Bundle dir: $BUNDLE_DIR"
echo ""

# --- Required files ---
check_required() {
    local path="$1"
    local label="${2:-$path}"
    if [ -f "$BUNDLE_DIR/$path" ] || [ -d "$BUNDLE_DIR/$path" ]; then
        echo -e "  ${GREEN}OK${NC} $label"
    else
        echo -e "  ${RED}MISSING${NC} $label"
        errors=$((errors + 1))
    fi
}

echo "--- Required items ---"
check_required "DedZapret.exe"  "DedZapret.exe"
check_required "DedZapretData/config.yaml"   "config.yaml"
check_required "DedZapretData/sources.yaml"  "sources.yaml"
check_required "DedZapretData/data/lists"    "data/lists directory"
check_required "DedZapretData/data/strategies/builtin" "data/strategies/builtin directory"
check_required "DedZapretData/data/strategies/custom" "data/strategies/custom directory"
check_required "DedZapretData/data/strategies/custom/KEEP.txt" "data/strategies/custom/KEEP.txt marker"
check_required "DedZapretData/data/strategies/generated" "data/strategies/generated directory"
check_required "DedZapretData/data/strategies/generated/KEEP.txt" "data/strategies/generated/KEEP.txt marker"
check_required "DedZapretData/data/strategies/generated/flowseal" "data/strategies/generated/flowseal directory"
check_required "DedZapretData/data/upstreams/flowseal" "data/upstreams/flowseal directory"
check_required "DedZapretData/data/upstreams/flowseal/general.bat" "data/upstreams/flowseal/general.bat"
check_required "DedZapretData/runtime/zapret" "runtime/zapret directory"
check_required "bin/sing-box/sing-box.exe" "bin/sing-box/sing-box.exe"

# --- Forbidden patterns ---
check_forbidden_pattern() {
    local pattern="$1"
    local label="$2"
    local count
    count=$(find "$BUNDLE_DIR" -path "$pattern" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$count" -gt 0 ]; then
        echo -e "  ${RED}FAIL${NC} Found $count forbidden item(s): $label"
        find "$BUNDLE_DIR" -path "$pattern" 2>/dev/null | head -5 | while read -r f; do
            echo "       $f"
        done
        errors=$((errors + 1))
    else
        echo -e "  ${GREEN}OK${NC} No $label"
    fi
}

echo ""
echo "--- Forbidden macOS metadata ---"
check_forbidden_pattern "*/__MACOSX/*"       "__MACOSX files"
check_forbidden_pattern "*/.DS_Store"        ".DS_Store files"
check_forbidden_pattern "*/._*"              "AppleDouble ._* files"

echo ""
echo "--- Forbidden stale runtime state ---"
check_forbidden_pattern "*/session_*.jsonl"  "session jsonl files"
check_forbidden_pattern "*/report_*.zip"     "report zip files"
check_forbidden_pattern "*/zapret_manager.log" "old app log"
check_forbidden_pattern "*/winws_stdout*.log" "winws stdout logs"
check_forbidden_pattern "*/winws_stderr*.log" "winws stderr logs"

echo ""
echo "--- Forbidden stale state files ---"
# Note: logs/state directories are not created by workflow
# Only forbid actual state files if they exist
check_forbidden_pattern "*/data/state/state.json" "state.json (generated on first run)"
check_forbidden_pattern "*/data/state/current.json" "current.json (generated on first run)"

echo ""
echo "--- Forbidden local absolute paths ---"
local_path_count=0
while IFS= read -r -d '' file; do
    # Only check text-like files for local paths, not binary files
    case "$file" in
        *.txt|*.json|*.yaml|*.yml|*.ini|*.cfg|*.conf|*.bat|*.cmd|*.ps1|*.md|*.py|*.toml|*.xml|*.log)
            if grep -l "C:\\\\Users\\\\" "$file" 2>/dev/null; then
                if [ "$local_path_count" -eq 0 ]; then
                    echo -e "  ${RED}FAIL${NC} Files containing C:\\Users\\ paths:"
                fi
                echo "       $file"
                local_path_count=$((local_path_count + 1))
            fi
            ;;
        *.exe|*.dll|*.sys|*.bin|*.dat|*.zip|*.7z)
            # Skip binary files - do not scan for local paths
            ;;
        *)
            # Skip other non-text files
            ;;
    esac
done < <(find "$BUNDLE_DIR" -type f -print0 2>/dev/null)
if [ "$local_path_count" -eq 0 ]; then
    echo -e "  ${GREEN}OK${NC} No C:\\Users\\ paths"
fi
errors=$((errors + local_path_count))

# also forbid /Users/ (macOS developer paths) inside text files
macos_path_count=0
while IFS= read -r -d '' file; do
    if grep -l "/Users/" "$file" 2>/dev/null; then
        if [ "$macos_path_count" -eq 0 ]; then
            echo -e "  ${RED}FAIL${NC} Files containing /Users/ paths:"
        fi
        echo "       $file"
        macos_path_count=$((macos_path_count + 1))
    fi
done < <(find "$BUNDLE_DIR" -type f -print0 2>/dev/null)
if [ "$macos_path_count" -eq 0 ]; then
    echo -e "  ${GREEN}OK${NC} No /Users/ paths"
fi
errors=$((errors + macos_path_count))

# --- Summary ---
echo ""
echo "========================"
if [ "$errors" -gt 0 ]; then
    echo -e "${RED}FAILED: $errors error(s) found${NC}"
    exit 1
else
    echo -e "${GREEN}PASSED: All checks passed${NC}"
    exit 0
fi