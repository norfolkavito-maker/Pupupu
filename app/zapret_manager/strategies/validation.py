from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.zapret_manager.core.app_context import AppContext

from app.zapret_manager.core.assets import (
    AssetKind,
    find_asset_candidates,
    validate_asset_exists,
)
from app.zapret_manager.strategies.model import Strategy, CommandType, Command


@dataclass
class StrategyValidationResult:
    is_valid: bool = False
    errors: list[str] = field(default_factory=list)
    missing_assets: list[str] = field(default_factory=list)
    unresolved_placeholders: list[str] = field(default_factory=list)
    resolved_command_paths: dict[str, Path] = field(default_factory=dict)


class StrategyValidator:
    def __init__(self, ctx: "AppContext"):
        self.ctx = ctx

    def validate(self, strategy: Strategy) -> StrategyValidationResult:
        errors: list[str] = []
        missing_assets: list[str] = []
        unresolved_placeholders: list[str] = []
        resolved_command_paths: dict[str, Path] = {}

        if not strategy.name:
            errors.append("Strategy name is missing.")

        if not strategy.id:
            errors.append("Strategy ID is missing.")

        # Start with any missing_assets already normalized from required_assets
        missing_assets.extend(strategy.missing_assets)

        for cmd in strategy.commands:
            if not cmd.type:
                errors.append(f"Command type is missing for command '{cmd.command}'.")
                continue

            # Validate command structure (basic check for now)
            if cmd.type in [CommandType.WINWS, CommandType.ZAPRET, CommandType.DOH]:
                if not cmd.command:
                    errors.append(f"Command string is missing for type '{cmd.type.value}'.")

                # Parse command for placeholder patterns and validate referenced assets
                cmd_str = cmd.command or ""
                for placeholder in ["{DATA}", "{RUNTIME}", "{LISTS}", "{MGR_LISTS}", "{FLOWSEAL_LISTS}", "{FLOWSEAL_BIN}", "{FAKE}"]:
                    if placeholder in cmd_str:
                        # These are known valid placeholders - skip resolution check
                        continue

                # For {FAKE:filename.bin} patterns, validate the fake asset exists
                import re
                fake_pattern = r"\{FAKE:([^}]+)\}"
                for match in re.finditer(fake_pattern, cmd_str):
                    fake_name = match.group(1)
                    ok, status, path = validate_asset_exists(self.ctx, kind="fake", name=fake_name)
                    if not ok:
                        missing_assets.append(str(path))
                        errors.append(f"Missing fake asset: {fake_name} ({status})")
                    else:
                        resolved_command_paths[f"{{FAKE:{fake_name}}}"] = path

        is_valid = not (errors or missing_assets or unresolved_placeholders)
        return StrategyValidationResult(
            is_valid=is_valid,
            errors=errors,
            missing_assets=missing_assets,
            unresolved_placeholders=unresolved_placeholders,
            resolved_command_paths=resolved_command_paths,
        )

    def validate_all_strategies_in_dir(self, directory: Path) -> dict[str, "StrategyValidationResult"]:
        results: dict[str, "StrategyValidationResult"] = {}
        return results
