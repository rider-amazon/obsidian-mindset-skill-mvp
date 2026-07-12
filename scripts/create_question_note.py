#!/usr/bin/env python3
"""Create a standardized Obsidian question note."""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path
from typing import Any


DEFAULT_STATUS = "unresolved"
VALID_STATUSES = {"unresolved", "partial", "answered", "converted_to_concept"}


def sanitize_filename(value: str) -> str:
    value = re.sub(r'[<>:"/\\|?*]+', "_", value.strip())
    value = re.sub(r"\s+", "_", value)
    value = re.sub(r"_+", "_", value)
    return value.strip("._") or "新问题"


def normalize_link(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        return ""
    if stripped.startswith("[[") and stripped.endswith("]]"):
        return stripped
    return f"[[{stripped}]]"


STRING_FIELDS = {
    "title",
    "file_stem",
    "question",
    "understanding",
    "answer",
    "overwrite_reason",
    "status",
}
STRING_LIST_FIELDS = {"understanding_points", "related", "next_steps"}
BOOLEAN_FIELDS = {"force", "overwrite_authorized"}


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(f"Invalid arguments: {message}")


def validate_spec(spec: dict[str, Any]) -> None:
    for field in STRING_FIELDS:
        if field in spec and spec[field] is not None and not isinstance(spec[field], str):
            raise TypeError(f"Field '{field}' must be a string or null.")
    for field in STRING_LIST_FIELDS:
        if field not in spec or spec[field] is None:
            continue
        value = spec[field]
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise TypeError(f"Field '{field}' must be an array of strings.")
    for field in BOOLEAN_FIELDS:
        if field in spec and not isinstance(spec[field], bool):
            raise TypeError(f"Field '{field}' must be a JSON boolean.")


def load_spec(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("Spec file must contain a JSON object.")
    validate_spec(data)
    return data


def parse_args() -> argparse.Namespace:
    parser = JsonArgumentParser(
        description="Generate a standardized question note in 30_Questions/."
    )
    parser.add_argument(
        "--vault",
        type=Path,
        required=True,
        help="Obsidian vault root. This argument is required.",
    )
    parser.add_argument(
        "--spec",
        type=Path,
        help="Optional JSON spec file. Explicit CLI flags override spec values.",
    )
    parser.add_argument("--title", help="Question title shown inside the note.")
    parser.add_argument("--file-stem", help="Optional file name without extension.")
    parser.add_argument("--question", help="Original user question.")
    parser.add_argument("--understanding", help="Current understanding paragraph.")
    parser.add_argument(
        "--understanding-point",
        action="append",
        default=[],
        help="Additional bullet under current understanding. Repeatable.",
    )
    parser.add_argument("--answer", help="Structured answer block.")
    parser.add_argument(
        "--related",
        action="append",
        default=[],
        help="Related concept name. Repeatable.",
    )
    parser.add_argument(
        "--status",
        default=None,
        help="Question status: unresolved / partial / answered / converted_to_concept.",
    )
    parser.add_argument(
        "--next-step",
        action="append",
        default=[],
        help="Next action bullet. Repeatable.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the target file if it already exists.",
    )
    return parser.parse_args()


def merge_args_with_spec(args: argparse.Namespace) -> dict[str, Any]:
    spec: dict[str, Any] = {}
    if args.spec:
        spec = load_spec(args.spec)

    payload: dict[str, Any] = {
        "vault": args.vault,
        "title": args.title or spec.get("title"),
        "file_stem": args.file_stem or spec.get("file_stem"),
        "question": args.question or spec.get("question"),
        "understanding": args.understanding
        if args.understanding is not None
        else spec.get("understanding"),
        "understanding_points": (
            args.understanding_point
            if args.understanding_point
            else spec.get("understanding_points") or []
        ),
        "answer": args.answer if args.answer is not None else spec.get("answer"),
        "related": args.related if args.related else spec.get("related") or [],
        "status": args.status or spec.get("status") or DEFAULT_STATUS,
        "next_steps": (
            args.next_step if args.next_step else spec.get("next_steps") or []
        ),
        "force": args.force,
        "overwrite_authorized": spec.get("overwrite_authorized", False),
        "overwrite_reason": spec.get("overwrite_reason"),
    }
    return payload


def validate_payload(payload: dict[str, Any]) -> None:
    for field in ("title", "question"):
        value = payload[field]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Field '{field}' must be a non-empty string.")
    vault = payload["vault"]
    if not isinstance(vault, Path) or not vault.exists() or not vault.is_dir():
        raise ValueError("Field 'vault' must point to an existing directory.")
    status = payload["status"]
    if status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid status: {status}. Expected one of {sorted(VALID_STATUSES)}."
        )
    if payload["force"]:
        if payload.get("overwrite_authorized") is not True:
            raise PermissionError(
                "Overwrite requires user authorization recorded as "
                "'overwrite_authorized': true in the spec."
            )
        reason = payload.get("overwrite_reason")
        if not isinstance(reason, str) or not reason.strip():
            raise PermissionError(
                "Overwrite requires a non-empty 'overwrite_reason' in the spec."
            )


def format_block(text: str | None) -> list[str]:
    if not text:
        return [""]
    return text.rstrip().splitlines() or [""]


def build_content(payload: dict[str, Any]) -> str:
    title = str(payload["title"]).strip()
    question = str(payload["question"]).strip()
    understanding = payload["understanding"]
    understanding_points = payload["understanding_points"]
    answer = payload["answer"]
    related = payload["related"]
    next_steps = payload["next_steps"]
    status = str(payload["status"]).strip()

    lines: list[str] = [f"# {title}", "", "## 原始问题", "", question, ""]

    lines.extend(["## 当前理解", ""])
    if understanding:
        lines.extend(format_block(str(understanding)))
    if understanding_points:
        if understanding:
            lines.append("")
        lines.extend(f"- {point.strip()}" for point in understanding_points if point.strip())
    if not understanding and not understanding_points:
        lines.append("")
    lines.append("")

    lines.extend(["## 当前回答", ""])
    lines.extend(format_block(str(answer) if answer is not None else None))
    lines.append("")

    lines.extend(["## 相关概念", ""])
    if related:
        lines.extend(f"- {normalize_link(item)}" for item in related if item.strip())
    else:
        lines.append("- ")
    lines.append("")

    lines.extend(["## 状态", "", status, "", "## 下一步动作", ""])
    if next_steps:
        lines.extend(f"- {item.strip()}" for item in next_steps if item.strip())
    else:
        lines.append("- ")
    lines.append("")

    return "\n".join(lines)


def write_note(payload: dict[str, Any]) -> Path:
    vault = Path(payload["vault"]).resolve()
    target_dir = vault / "30_Questions"
    target_dir.mkdir(parents=True, exist_ok=True)

    file_stem = payload["file_stem"] or sanitize_filename(str(payload["title"]))
    target = target_dir / f"{sanitize_filename(str(file_stem))}.md"

    force = bool(payload["force"])
    if target.exists() and not force:
        raise FileExistsError(
            f"Target file already exists: {target}. Refuse to overwrite without "
            "explicit user authorization."
        )

    content = build_content(payload)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="\n",
        dir=target_dir,
        prefix=f".{target.stem}.",
        suffix=".tmp",
        delete=False,
    ) as temp_file:
        temp_file.write(content)
        temp_path = Path(temp_file.name)

    try:
        if force:
            temp_path.replace(target)
        else:
            temp_path.rename(target)
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise
    return target


def main() -> int:
    try:
        args = parse_args()
        payload = merge_args_with_spec(args)
        validate_payload(payload)
        target = write_note(payload)
        result = {
            "ok": True,
            "path": str(target),
            "title": payload["title"],
            "status": payload["status"],
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        if isinstance(exc, FileExistsError):
            error = "target_exists"
        elif isinstance(exc, PermissionError):
            error = "overwrite_not_authorized"
        else:
            error = "invalid_input"
        print(
            json.dumps(
                {"ok": False, "error": error, "message": str(exc)},
                ensure_ascii=False,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
