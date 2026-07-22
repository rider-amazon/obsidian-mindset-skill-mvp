#!/usr/bin/env python3
"""Resolve Obsidian Mindset task routes from Prompt JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


QUESTION_REFERENCE = "references/question-note/reference.md"
COMPARE_REFERENCE = "references/compare-canvas/reference.md"
OPEN_REFERENCE = "references/open-route-reference.md"

VALID_ACTIONS = {"create", "answer", "update", "keep"}
VALID_ROUTES = {"question_note", "compare_canvas", "open_route"}
VALID_REQUEST_ROUTES = VALID_ROUTES | {None}
VALID_CONFIDENCE = {"high", "medium", "low"}
STANDARD_ROUTES = {"question_note", "compare_canvas"}


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(f"Invalid arguments: {message}")


def parse_args() -> argparse.Namespace:
    parser = JsonArgumentParser(
        description="Resolve routes for an Obsidian Mindset Prompt JSON queue."
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Temporary Prompt JSON or Update Prompt JSON file.",
    )
    return parser.parse_args()


def require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"Field '{field}' must be a JSON object.")
    return value


def require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"Field '{field}' must be a non-empty string.")
    return value


def validate_optional_string(value: Any, field: str) -> None:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        raise TypeError(f"Field '{field}' must be a non-empty string or null.")


def validate_input(payload: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    request = require_object(payload.get("request"), "request")
    task_shape = request.get("task_shape")
    if task_shape not in {"single", "multi"}:
        raise ValueError("Field 'request.task_shape' must be 'single' or 'multi'.")

    vault_root = request.get("vault_root")
    validate_optional_string(vault_root, "request.vault_root")

    raw_queue = payload.get("task_queue")
    if not isinstance(raw_queue, list) or not raw_queue:
        raise TypeError("Field 'task_queue' must be a non-empty JSON array.")
    if task_shape == "single" and len(raw_queue) != 1:
        raise ValueError("A single request must contain exactly one task.")
    if task_shape == "multi" and len(raw_queue) < 2:
        raise ValueError("A multi request must contain at least two tasks.")

    tasks: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, raw_task in enumerate(raw_queue):
        task = require_object(raw_task, f"task_queue[{index}]")
        task_id = require_string(task.get("id"), f"task_queue[{index}].id")
        if task_id in seen_ids:
            raise ValueError(f"Duplicate task id: {task_id}")
        seen_ids.add(task_id)

        operation = require_object(
            task.get("operation"), f"task_queue[{index}].operation"
        )
        action = operation.get("action")
        if action not in VALID_ACTIONS:
            raise ValueError(
                f"Invalid action for task '{task_id}': {action!r}."
            )
        validate_optional_string(
            operation.get("target_path"),
            f"task_queue[{index}].operation.target_path",
        )
        overwrite_authorized = operation.get("overwrite_authorized")
        if not isinstance(overwrite_authorized, bool):
            raise TypeError(
                f"Field 'task_queue[{index}].operation.overwrite_authorized' "
                "must be a JSON boolean."
            )
        validate_optional_string(
            operation.get("overwrite_reason"),
            f"task_queue[{index}].operation.overwrite_reason",
        )

        intent = require_object(task.get("intent"), f"task_queue[{index}].intent")
        request_route = intent.get("request_route")
        if request_route not in VALID_REQUEST_ROUTES:
            raise ValueError(
                f"Invalid request_route for task '{task_id}': {request_route!r}."
            )
        task_candidate = intent.get("task_candidate")
        if task_candidate not in VALID_ROUTES:
            raise ValueError(
                f"Invalid task_candidate for task '{task_id}': {task_candidate!r}."
            )
        confidence = intent.get("confidence")
        if confidence not in VALID_CONFIDENCE:
            raise ValueError(
                f"Invalid confidence for task '{task_id}': {confidence!r}."
            )
        tasks.append(task)

    return request, tasks


def blocked(task_id: str, reason: str) -> dict[str, Any]:
    return {"id": task_id, "reference": None, "reason": reason}


def matched(task_id: str, reference: str | None) -> dict[str, Any]:
    return {"id": task_id, "reference": reference, "reason": None}


def resolve_vault_root(vault_root: str | None) -> tuple[Path | None, str | None]:
    if vault_root is None:
        return None, "文件任务缺少唯一、已确认的 request.vault_root。"

    vault_path = Path(vault_root)
    if not vault_path.is_absolute():
        return None, f"request.vault_root 必须是绝对路径：{vault_root}"
    try:
        resolved_vault = vault_path.resolve(strict=True)
    except (FileNotFoundError, OSError):
        return None, f"request.vault_root 不是真实存在的目录：{vault_root}"
    if not resolved_vault.is_dir():
        return None, f"request.vault_root 不是真实存在的目录：{vault_root}"
    return resolved_vault, None


def resolve_target_in_vault(
    target_path: str | None,
    vault_path: Path,
    *,
    action: str,
) -> tuple[Path | None, str | None]:
    label = "更新目标" if action == "update" else "keep 目标"
    if target_path is None:
        return None, f"{label}不唯一或无法定位。"

    raw_target = Path(target_path)
    if not raw_target.is_absolute():
        return None, f"{label}必须使用绝对路径：{target_path}"
    try:
        resolved_target = raw_target.resolve(strict=True)
    except (FileNotFoundError, OSError):
        return None, f"{label}不存在：{target_path}"
    if not resolved_target.is_file():
        return None, f"{label}不存在：{target_path}"
    if not resolved_target.is_relative_to(vault_path):
        return None, f"{label}不在已确认的 request.vault_root 内：{target_path}"
    return resolved_target, None


def resolve_task(task: dict[str, Any], vault_root: str | None) -> dict[str, Any]:
    task_id = task["id"]
    operation = task["operation"]
    intent = task["intent"]

    action = operation["action"]
    target_path = operation.get("target_path")
    request_route = intent.get("request_route")
    task_candidate = intent["task_candidate"]
    confidence = intent["confidence"]

    if (
        request_route in STANDARD_ROUTES
        and request_route != task_candidate
    ):
        return blocked(
            task_id,
            f"显式入口 {request_route} 与任务候选 {task_candidate} 不匹配。",
        )

    if request_route in STANDARD_ROUTES and confidence == "low":
        return blocked(
            task_id,
            f"显式标准入口 {request_route} 的意图置信度为 low。",
        )

    resolved_vault: Path | None = None
    if action in {"create", "update", "keep"}:
        resolved_vault, vault_error = resolve_vault_root(vault_root)
        if vault_error is not None:
            return blocked(task_id, vault_error)

    if action == "update":
        if confidence == "low":
            return blocked(task_id, "更新目标或修改意图的置信度为 low。")
        _, target_error = resolve_target_in_vault(
            target_path,
            resolved_vault,
            action=action,
        )
        if target_error is not None:
            return blocked(task_id, target_error)
        if request_route == "open_route":
            return blocked(task_id, "open route 不允许更新已有文件。")
        if task_candidate == "open_route":
            return blocked(task_id, "现有标准能力无法安全更新该文件。")

    if action == "keep":
        _, target_error = resolve_target_in_vault(
            target_path,
            resolved_vault,
            action=action,
        )
        if target_error is not None:
            return blocked(task_id, target_error)
        return matched(task_id, None)

    if (
        request_route is None
        and action in {"create", "answer"}
        and confidence == "low"
    ):
        return matched(task_id, OPEN_REFERENCE)

    if task_candidate == "question_note" and action in {"create", "update"}:
        return matched(task_id, QUESTION_REFERENCE)

    if task_candidate == "compare_canvas" and action in {"create", "update"}:
        return matched(task_id, COMPARE_REFERENCE)

    if task_candidate == "open_route" and action in {"create", "answer"}:
        return matched(task_id, OPEN_REFERENCE)

    return blocked(
        task_id,
        f"operation.action={action} 与 task_candidate={task_candidate} 不兼容。",
    )


def resolve_routes(payload: dict[str, Any]) -> dict[str, Any]:
    request, tasks = validate_input(payload)
    vault_root = request.get("vault_root")
    routes = [resolve_task(task, vault_root) for task in tasks]
    return {
        "ok": all(route["reason"] is None for route in routes),
        "routes": routes,
    }


def load_input(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise TypeError("Input file must contain a JSON object.")
    return data


def main() -> int:
    try:
        args = parse_args()
        result = resolve_routes(load_input(args.input))
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return 0
    except Exception as exc:
        result = {"ok": False, "error": "invalid_input", "message": str(exc)}
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
