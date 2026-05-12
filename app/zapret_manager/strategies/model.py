from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional


class CommandType(str, Enum):
    WINWS = "winws"
    ZAPRET = "zapret"
    DOH = "doh"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Command:
    type: CommandType
    command: str


@dataclass
class Strategy:
    id: str
    name: str
    commands: list[Command]
    engine: str = "winws"
    source_file: str = ""
    upstream: str = ""
    kind: str = "base"
    # Validation status
    is_valid: bool = True
    validation_errors: list[str] = field(default_factory=list)
    missing_assets: list[str] = field(default_factory=list)
    unresolved_placeholders: list[str] = field(default_factory=list)

    @staticmethod
    def from_json(data: dict[str, Any]) -> "Strategy":
        commands = []
        for cmd_data in data.get("commands", []):
            cmd_type = CommandType(cmd_data.get("type", "unknown"))
            command_str = cmd_data.get("command", "")
            commands.append(Command(type=cmd_type, command=command_str))

        return Strategy(
            id=str(data.get("id", "")),
            name=str(data["name"]),
            commands=commands,
            source_file=str(data.get("source_file", "")),
            upstream=str(data.get("upstream", "")),
            kind=str(data.get("kind", "base")),
            is_valid=bool(data.get("is_valid", True)),
            validation_errors=[str(x) for x in (data.get("validation_errors") or [])],
            missing_assets=[str(x) for x in (data.get("missing_assets") or [])],
            unresolved_placeholders=[str(x) for x in (data.get("unresolved_placeholders") or [])],
        )

    def to_json(self) -> dict[str, Any]:
        commands_json = []
        for cmd in self.commands:
            commands_json.append({"type": cmd.type.value, "command": cmd.command})

        return {
            "id": self.id,
            "name": self.name,
            "commands": commands_json,
            "source_file": self.source_file,
            "upstream": self.upstream,
            "kind": self.kind,
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
            "missing_assets": self.missing_assets,
            "unresolved_placeholders": self.unresolved_placeholders,
        }

    @property
    def args(self) -> List[str]:
        """Backward-compatible property: returns command strings."""
        return [cmd.command for cmd in self.commands]

    def get_full_args(self) -> List[str]:
        """Extracts and returns all command strings from the strategy."""
        return self.args

