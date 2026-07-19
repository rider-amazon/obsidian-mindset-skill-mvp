#!/usr/bin/env python3
"""Generate a deterministic Obsidian compare canvas."""

from __future__ import annotations

import argparse
import json
import math
import re
import tempfile
import unicodedata
from pathlib import Path
from typing import Any


def sanitize_filename(value: str) -> str:
    value = re.sub(r'[<>:"/\\|?*]+', "_", value.strip())
    value = re.sub(r"\s+", "_", value)
    value = re.sub(r"_+", "_", value)
    return value.strip("._") or "Compare"


STRING_FIELDS = {
    "title",
    "file_stem",
    "left",
    "right",
    "question",
    "summary",
    "overwrite_reason",
    "left_subtitle",
    "right_subtitle",
}
STRING_LIST_FIELDS = {"same_points", "left_points", "right_points", "related"}


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
    if "force" in spec and not isinstance(spec["force"], bool):
        raise TypeError("Field 'force' must be a JSON boolean.")
    if "overwrite_authorized" in spec and not isinstance(spec["overwrite_authorized"], bool):
        raise TypeError("Field 'overwrite_authorized' must be a JSON boolean.")


def load_spec(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("Spec file must contain a JSON object.")
    validate_spec(data)
    return data


def parse_related(raw_items: list[str]) -> list[dict[str, str]]:
    related: list[dict[str, str]] = []
    for raw in raw_items:
        parts = [part.strip() for part in raw.split("|")]
        if not parts or not parts[0]:
            continue
        while len(parts) < 4:
            parts.append("")
        related.append(
            {
                "name": parts[0],
                "description": parts[1],
                "left_label": parts[2] or "相关",
                "right_label": parts[3] or "相关",
            }
        )
    return related


def format_bullets(items: list[str]) -> str:
    cleaned = [item.strip() for item in items if item.strip()]
    if not cleaned:
        return "- "
    return "\n".join(f"- {item}" for item in cleaned)


def linked_concept(name: str, subtitle: str | None) -> str:
    lines = [f"[[{name.strip()}]]"]
    if subtitle and subtitle.strip():
        lines.append(subtitle.strip())
    return "\n".join(lines)


def related_context_text(item: dict[str, str]) -> str:
    lines = [f"[[{item['name'].strip()}]]"]
    description = item.get("description", "").strip()
    if description:
        lines.append(description)

    left_label = item.get("left_label", "").strip()
    right_label = item.get("right_label", "").strip()
    if left_label or right_label:
        lines.append("")
    if left_label:
        lines.append(f"左侧关系：{left_label}")
    if right_label:
        lines.append(f"右侧关系：{right_label}")
    return "\n".join(lines)


def estimate_text_height(
    text: str,
    *,
    min_height: int,
    width: int,
    line_height: int = 32,
    padding: int = 44,
) -> int:
    """Estimate rendered height with separate CJK and Latin width models."""
    usable_width = max(width - 40, 80)
    line_count = sum(
        estimate_wrapped_lines(line, usable_width)
        for line in (text.splitlines() or [""])
    )
    return max(min_height, line_count * line_height + padding)


def estimated_character_width(char: str) -> float:
    """Return an approximate Obsidian Canvas character width in pixels."""
    if char.isspace():
        return 5.0
    if unicodedata.east_asian_width(char) in {"W", "F"}:
        return 17.0
    if char.isascii():
        if unicodedata.category(char).startswith("P"):
            return 7.0
        return 8.5
    if unicodedata.east_asian_width(char) == "A":
        return 12.0
    return 10.0


def estimate_wrapped_lines(line: str, usable_width: int) -> int:
    """Estimate wrapping while keeping Latin words intact when possible."""
    if not line:
        return 1

    tokens = re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]|[A-Za-z0-9_./:+-]+|\s+|.", line)
    lines = 1
    occupied = 0.0

    for token in tokens:
        if token.isspace():
            token_width = estimated_character_width(" ")
            if occupied and occupied + token_width <= usable_width:
                occupied += token_width
            continue

        token_width = sum(estimated_character_width(char) for char in token)
        if occupied and occupied + token_width > usable_width:
            lines += 1
            occupied = 0.0

        if token_width <= usable_width:
            occupied += token_width
            continue

        for char in token:
            char_width = estimated_character_width(char)
            if occupied and occupied + char_width > usable_width:
                lines += 1
                occupied = 0.0
            occupied += char_width

    return lines


def build_text_node(
    node_id: str,
    x: int,
    y: int,
    width: int,
    height: int,
    text: str,
    color: str,
) -> dict[str, Any]:
    return {
        "id": node_id,
        "type": "text",
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "text": text,
        "color": color,
    }


def build_edge(
    edge_id: str,
    from_node: str,
    from_side: str,
    to_node: str,
    to_side: str,
    label: str,
    color: str,
) -> dict[str, Any]:
    return {
        "id": edge_id,
        "fromNode": from_node,
        "fromSide": from_side,
        "toNode": to_node,
        "toSide": to_side,
        "label": label,
        "toEnd": "arrow",
        "color": color,
    }


def parse_args() -> argparse.Namespace:
    parser = JsonArgumentParser(
        description="Generate a compare canvas in 10_Maps/."
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
    parser.add_argument("--title", help="Canvas title.")
    parser.add_argument("--file-stem", help="Optional file name without extension.")
    parser.add_argument("--left", help="Left concept.")
    parser.add_argument("--right", help="Right concept.")
    parser.add_argument("--question", help="Core compare question.")
    parser.add_argument("--summary", help="One-line judgment shown on the top-right note.")
    parser.add_argument("--left-subtitle", help="Subtitle shown under the left concept.")
    parser.add_argument("--right-subtitle", help="Subtitle shown under the right concept.")
    parser.add_argument(
        "--same-point",
        action="append",
        default=[],
        help="Shared property. Repeatable.",
    )
    parser.add_argument(
        "--left-point",
        action="append",
        default=[],
        help="Left-only property. Repeatable.",
    )
    parser.add_argument(
        "--right-point",
        action="append",
        default=[],
        help="Right-only property. Repeatable.",
    )
    parser.add_argument(
        "--related",
        action="append",
        default=[],
        help="Related node in '名称|说明|左侧标签|右侧标签' format. Repeatable.",
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
        "left": args.left or spec.get("left"),
        "right": args.right or spec.get("right"),
        "question": args.question or spec.get("question"),
        "summary": args.summary if args.summary is not None else spec.get("summary"),
        "left_subtitle": (
            args.left_subtitle
            if args.left_subtitle is not None
            else spec.get("left_subtitle")
        ),
        "right_subtitle": (
            args.right_subtitle
            if args.right_subtitle is not None
            else spec.get("right_subtitle")
        ),
        "same_points": (
            args.same_point if args.same_point else spec.get("same_points") or []
        ),
        "left_points": (
            args.left_point if args.left_point else spec.get("left_points") or []
        ),
        "right_points": (
            args.right_point
            if args.right_point
            else spec.get("right_points") or []
        ),
        "related": parse_related(args.related)
        if args.related
        else parse_related(spec.get("related") or []),
        "force": args.force,
        "overwrite_authorized": spec.get("overwrite_authorized", False),
        "overwrite_reason": spec.get("overwrite_reason"),
    }
    return payload


def validate_payload(payload: dict[str, Any]) -> None:
    required = ["title", "left", "right", "question"]
    for field in required:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Field '{field}' must be a non-empty string.")
    vault = payload["vault"]
    if not isinstance(vault, Path) or not vault.exists() or not vault.is_dir():
        raise ValueError("Field 'vault' must point to an existing directory.")
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


def choose_canvas_layout(
    *,
    title_height: int,
    summary_height: int,
    concept_height: int,
    same_height: int,
    left_detail_text: str,
    right_detail_text: str,
    related: list[dict[str, str]],
) -> dict[str, Any]:
    """Choose a compact layout from content-dependent width and grid candidates."""
    group_x = 40
    group_y = 40
    top_row_y = 90
    concept_y = top_row_y + max(title_height, summary_height) + 70
    detail_y = concept_y + max(concept_height, same_height) + 110
    target_aspect_ratio = 1.35
    candidates: list[dict[str, Any]] = []

    for detail_width in (360, 440, 520, 600):
        left_detail_height = estimate_text_height(
            left_detail_text, min_height=210, width=detail_width
        )
        right_detail_height = estimate_text_height(
            right_detail_text, min_height=210, width=detail_width
        )
        main_bottom = detail_y + max(left_detail_height, right_detail_height)
        base_group_width = max(1380, detail_width * 2 + 260)

        grid_options: list[dict[str, Any]] = []
        if not related:
            grid_options.append(
                {
                    "related_width": 0,
                    "columns": 0,
                    "row_heights": [],
                    "group_width": base_group_width,
                    "content_bottom": main_bottom,
                    "related_y": 0,
                    "rows": 0,
                }
            )
        else:
            related_y = main_bottom + 140
            for related_width in (280, 340, 400):
                for columns in range(1, min(4, len(related)) + 1):
                    column_gap = 80
                    row_gap = 70
                    grid_width = (
                        columns * related_width + (columns - 1) * column_gap
                    )
                    group_width = max(base_group_width, grid_width + 100)
                    row_heights: list[int] = []
                    for row_start in range(0, len(related), columns):
                        row_items = related[row_start : row_start + columns]
                        row_heights.append(
                            max(
                                estimate_text_height(
                                    related_context_text(item),
                                    min_height=95,
                                    width=related_width,
                                )
                                for item in row_items
                            )
                        )
                    rows = len(row_heights)
                    content_bottom = (
                        related_y
                        + sum(row_heights)
                        + max(rows - 1, 0) * row_gap
                    )
                    grid_options.append(
                        {
                            "related_width": related_width,
                            "columns": columns,
                            "row_heights": row_heights,
                            "group_width": group_width,
                            "content_bottom": content_bottom,
                            "related_y": related_y,
                            "rows": rows,
                        }
                    )

        for grid in grid_options:
            group_width = grid["group_width"]
            group_height = grid["content_bottom"] - group_y + 80
            aspect_ratio = group_width / group_height
            area = group_width * group_height
            score = (
                abs(math.log(aspect_ratio / target_aspect_ratio))
                + area / 50_000_000
                + grid["rows"] * 0.015
            )
            candidates.append(
                {
                    **grid,
                    "score": score,
                    "group_x": group_x,
                    "group_y": group_y,
                    "group_height": group_height,
                    "top_row_y": top_row_y,
                    "concept_y": concept_y,
                    "detail_y": detail_y,
                    "detail_width": detail_width,
                    "left_detail_height": left_detail_height,
                    "right_detail_height": right_detail_height,
                }
            )

    return min(candidates, key=lambda candidate: candidate["score"])


def build_canvas(payload: dict[str, Any]) -> dict[str, Any]:
    title = str(payload["title"]).strip()
    left = str(payload["left"]).strip()
    right = str(payload["right"]).strip()
    question = str(payload["question"]).strip()
    summary = str(payload["summary"]).strip() if payload.get("summary") else ""
    left_subtitle = payload.get("left_subtitle")
    right_subtitle = payload.get("right_subtitle")
    same_points = payload["same_points"]
    left_points = payload["left_points"]
    right_points = payload["right_points"]
    related = payload["related"]

    title_text = f"**核心问题**\n{question}"
    summary_text = f"**一句话判断**\n{summary or '- '}"
    left_text = linked_concept(left, str(left_subtitle) if left_subtitle else None)
    right_text = linked_concept(right, str(right_subtitle) if right_subtitle else None)
    same_text = f"**共同点**\n{format_bullets(same_points)}"
    left_detail_text = f"**{left} 更强调**\n{format_bullets(left_points)}"
    right_detail_text = f"**{right} 更强调**\n{format_bullets(right_points)}"

    title_height = estimate_text_height(title_text, min_height=110, width=420)
    summary_height = estimate_text_height(summary_text, min_height=120, width=250)
    concept_height = max(
        estimate_text_height(left_text, min_height=100, width=280),
        estimate_text_height(right_text, min_height=100, width=280),
    )
    same_height = estimate_text_height(same_text, min_height=150, width=450)
    layout = choose_canvas_layout(
        title_height=title_height,
        summary_height=summary_height,
        concept_height=concept_height,
        same_height=same_height,
        left_detail_text=left_detail_text,
        right_detail_text=right_detail_text,
        related=related,
    )

    group_x = layout["group_x"]
    group_y = layout["group_y"]
    group_width = layout["group_width"]
    group_center_x = group_x + group_width // 2
    concept_y = layout["concept_y"]
    detail_y = layout["detail_y"]
    detail_width = layout["detail_width"]

    nodes: list[dict[str, Any]] = [
        {
            "id": "g1",
            "type": "group",
            "x": group_x,
            "y": group_y,
            "width": group_width,
            "height": layout["group_height"],
            "label": title,
            "color": "5",
        },
        build_text_node(
            "title",
            group_center_x - 210,
            layout["top_row_y"],
            420,
            title_height,
            title_text,
            "2",
        ),
        build_text_node(
            "left",
            group_x + 80,
            concept_y,
            280,
            concept_height,
            left_text,
            "4",
        ),
        build_text_node(
            "right",
            group_x + group_width - 360,
            concept_y,
            280,
            concept_height,
            right_text,
            "4",
        ),
        build_text_node(
            "same",
            group_center_x - 225,
            concept_y - 10,
            450,
            same_height,
            same_text,
            "3",
        ),
        build_text_node(
            "left_details",
            group_x + 50,
            detail_y,
            detail_width,
            layout["left_detail_height"],
            left_detail_text,
            "6",
        ),
        build_text_node(
            "right_details",
            group_x + group_width - 50 - detail_width,
            detail_y,
            detail_width,
            layout["right_detail_height"],
            right_detail_text,
            "6",
        ),
        build_text_node(
            "summary",
            group_x + group_width - 350,
            layout["top_row_y"],
            250,
            summary_height,
            summary_text,
            "1",
        ),
    ]

    edges: list[dict[str, Any]] = [
        build_edge("e1", "left", "right", "same", "left", "共同点", "4"),
        build_edge("e2", "right", "left", "same", "right", "共同点", "4"),
        build_edge("e3", "left", "bottom", "left_details", "top", "差异", "6"),
        build_edge("e4", "right", "bottom", "right_details", "top", "差异", "6"),
    ]

    if related:
        related_width = layout["related_width"]
        columns = layout["columns"]
        column_gap = 80
        row_gap = 70
        grid_width = columns * related_width + (columns - 1) * column_gap
        start_x = group_center_x - grid_width // 2
        row_heights = layout["row_heights"]
        for index, item in enumerate(related, start=1):
            node_id = f"related_{index}"
            zero_index = index - 1
            row = zero_index // columns
            column = zero_index % columns
            x = start_x + column * (related_width + column_gap)
            y = layout["related_y"] + sum(row_heights[:row]) + row * row_gap
            text = related_context_text(item)
            node_height = estimate_text_height(
                text, min_height=95, width=related_width
            )
            nodes.append(
                build_text_node(node_id, x, y, related_width, node_height, text, "5")
            )
            if len(related) <= 3:
                edges.append(
                    build_edge(
                        f"e_related_{index}",
                        node_id,
                        "top",
                        "same",
                        "bottom",
                        "相关背景",
                        "5",
                    )
                )

    validate_canvas_layout(nodes)
    return {"nodes": nodes, "edges": edges}


def rectangles_overlap(left: dict[str, Any], right: dict[str, Any], margin: int = 20) -> bool:
    return not (
        left["x"] + left["width"] + margin <= right["x"]
        or right["x"] + right["width"] + margin <= left["x"]
        or left["y"] + left["height"] + margin <= right["y"]
        or right["y"] + right["height"] + margin <= left["y"]
    )


def validate_canvas_layout(nodes: list[dict[str, Any]]) -> None:
    group = next(node for node in nodes if node["id"] == "g1")
    content_nodes = [node for node in nodes if node["id"] != "g1"]
    for node in content_nodes:
        if (
            node["x"] < group["x"]
            or node["y"] < group["y"]
            or node["x"] + node["width"] > group["x"] + group["width"]
            or node["y"] + node["height"] > group["y"] + group["height"]
        ):
            raise ValueError(f"Canvas node '{node['id']}' exceeds the group bounds.")
    for index, left_node in enumerate(content_nodes):
        for right_node in content_nodes[index + 1 :]:
            if rectangles_overlap(left_node, right_node):
                raise ValueError(
                    f"Canvas nodes '{left_node['id']}' and '{right_node['id']}' overlap."
                )


def write_canvas(payload: dict[str, Any]) -> Path:
    vault = Path(payload["vault"]).resolve()
    target_dir = vault / "10_Maps"
    target_dir.mkdir(parents=True, exist_ok=True)

    base = payload["file_stem"] or payload["title"]
    target = target_dir / f"{sanitize_filename(str(base))}.canvas"
    force = bool(payload["force"])
    if target.exists() and not force:
        raise FileExistsError(
            f"Target file already exists: {target}. Refuse to overwrite without "
            "explicit user authorization."
        )

    content = json.dumps(build_canvas(payload), ensure_ascii=False, indent=2)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="\n",
        dir=target_dir,
        prefix=f".{target.stem}.",
        suffix=".tmp",
        delete=False,
    ) as temp_file:
        temp_file.write(content + "\n")
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
        target = write_canvas(payload)
        result = {
            "ok": True,
            "path": str(target),
            "title": payload["title"],
            "left": payload["left"],
            "right": payload["right"],
            "layout_valid": True,
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
