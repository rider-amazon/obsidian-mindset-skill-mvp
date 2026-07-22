from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import resolve_route  # noqa: E402


def task(
    task_id: str = "task_1",
    *,
    action: str = "create",
    target_path: str | None = None,
    request_route: str | None = None,
    candidate: str = "question_note",
    confidence: str = "high",
) -> dict:
    return {
        "id": task_id,
        "invoke": {"raw_user_request": "测试请求", "summary": "测试任务"},
        "operation": {
            "action": action,
            "target_path": target_path,
            "overwrite_authorized": action == "update",
            "overwrite_reason": "用户明确要求修改" if action == "update" else None,
        },
        "intent": {
            "request_route": request_route,
            "task_candidate": candidate,
            "confidence": confidence,
        },
    }


def payload(tasks: list[dict], vault_root: str | None) -> dict:
    return {
        "request": {
            "raw_user_request": "完整测试请求",
            "summary": "路由测试",
            "task_shape": "single" if len(tasks) == 1 else "multi",
            "vault_root": vault_root,
        },
        "task_queue": tasks,
    }


class ResolveRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.vault = self.root / "vault"
        self.vault.mkdir()
        maps = self.vault / "10_Maps"
        maps.mkdir()
        self.canvas = maps / "compare.canvas"
        self.canvas.write_text('{"nodes": [], "edges": []}', encoding="utf-8")
        self.outside = self.root / "outside.canvas"
        self.outside.write_text('{"nodes": [], "edges": []}', encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def resolve(self, one_task: dict, vault: str | None = "default") -> dict:
        vault_root = str(self.vault) if vault == "default" else vault
        return resolve_route.resolve_routes(payload([one_task], vault_root))

    def test_standard_question_and_compare_routes(self) -> None:
        question = self.resolve(task(candidate="question_note"))
        compare = self.resolve(task(candidate="compare_canvas"))
        self.assertEqual(
            question["routes"][0]["reference"], resolve_route.QUESTION_REFERENCE
        )
        self.assertEqual(
            compare["routes"][0]["reference"], resolve_route.COMPARE_REFERENCE
        )

    def test_explicit_standard_route_conflict_blocks(self) -> None:
        result = self.resolve(
            task(request_route="compare_canvas", candidate="question_note")
        )
        self.assertFalse(result["ok"])
        self.assertIsNone(result["routes"][0]["reference"])
        self.assertIn("不匹配", result["routes"][0]["reason"])

    def test_explicit_standard_low_confidence_blocks(self) -> None:
        result = self.resolve(
            task(
                request_route="question_note",
                candidate="question_note",
                confidence="low",
            )
        )
        self.assertFalse(result["ok"])
        self.assertIn("low", result["routes"][0]["reason"])

    def test_file_task_without_vault_blocks_before_fallback(self) -> None:
        result = self.resolve(
            task(candidate="question_note", confidence="low"), vault=None
        )
        self.assertFalse(result["ok"])
        self.assertIn("vault_root", result["routes"][0]["reason"])

    def test_file_task_requires_real_absolute_vault(self) -> None:
        relative = self.resolve(task(candidate="question_note"), vault="vault")
        missing = self.resolve(
            task(candidate="question_note"),
            vault=str(self.root / "missing-vault"),
        )
        self.assertFalse(relative["ok"])
        self.assertIn("绝对路径", relative["routes"][0]["reason"])
        self.assertFalse(missing["ok"])
        self.assertIn("真实存在的目录", missing["routes"][0]["reason"])

    def test_implicit_low_confidence_answer_falls_back_to_open(self) -> None:
        result = self.resolve(
            task(action="answer", candidate="question_note", confidence="low"),
            vault=None,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(
            result["routes"][0]["reference"], resolve_route.OPEN_REFERENCE
        )

    def test_implicit_low_confidence_create_falls_back_to_open(self) -> None:
        result = self.resolve(task(candidate="compare_canvas", confidence="low"))
        self.assertTrue(result["ok"])
        self.assertEqual(
            result["routes"][0]["reference"], resolve_route.OPEN_REFERENCE
        )

    def test_update_requires_existing_unique_target(self) -> None:
        missing = str(self.vault / "10_Maps" / "missing.canvas")
        result = self.resolve(
            task(action="update", target_path=missing, candidate="compare_canvas")
        )
        self.assertFalse(result["ok"])
        self.assertIn("不存在", result["routes"][0]["reason"])

        no_target = self.resolve(
            task(action="update", target_path=None, candidate="compare_canvas")
        )
        self.assertFalse(no_target["ok"])
        self.assertIn("无法定位", no_target["routes"][0]["reason"])

    def test_update_target_must_stay_inside_confirmed_vault(self) -> None:
        outside = self.resolve(
            task(
                action="update",
                target_path=str(self.outside),
                candidate="compare_canvas",
            )
        )
        escaped = self.resolve(
            task(
                action="update",
                target_path=str(
                    self.vault / "10_Maps" / ".." / ".." / self.outside.name
                ),
                candidate="compare_canvas",
            )
        )
        self.assertFalse(outside["ok"])
        self.assertIn("vault_root 内", outside["routes"][0]["reason"])
        self.assertFalse(escaped["ok"])
        self.assertIn("vault_root 内", escaped["routes"][0]["reason"])

    def test_implicit_low_confidence_update_blocks(self) -> None:
        result = self.resolve(
            task(
                action="update",
                target_path=str(self.canvas),
                candidate="compare_canvas",
                confidence="low",
            )
        )
        self.assertFalse(result["ok"])
        self.assertIn("low", result["routes"][0]["reason"])

    def test_standard_update_routes_to_matching_reference(self) -> None:
        compare = self.resolve(
            task(
                action="update",
                target_path=str(self.canvas),
                candidate="compare_canvas",
            )
        )
        self.assertTrue(compare["ok"])
        self.assertEqual(
            compare["routes"][0]["reference"], resolve_route.COMPARE_REFERENCE
        )

    def test_open_route_cannot_update(self) -> None:
        result = self.resolve(
            task(
                action="update",
                target_path=str(self.canvas),
                request_route="open_route",
                candidate="compare_canvas",
            )
        )
        self.assertFalse(result["ok"])
        self.assertIn("open route", result["routes"][0]["reason"])

    def test_open_candidate_cannot_update(self) -> None:
        result = self.resolve(
            task(
                action="update",
                target_path=str(self.canvas),
                candidate="open_route",
            )
        )
        self.assertFalse(result["ok"])
        self.assertIn("无法安全更新", result["routes"][0]["reason"])

    def test_keep_has_no_reference_or_reason(self) -> None:
        result = self.resolve(
            task(
                action="keep",
                target_path=str(self.canvas),
                candidate="compare_canvas",
            )
        )
        self.assertTrue(result["ok"])
        self.assertEqual(
            result["routes"][0],
            {"id": "task_1", "reference": None, "reason": None},
        )

        missing = self.resolve(
            task(
                action="keep",
                target_path=str(self.vault / "missing.canvas"),
                candidate="compare_canvas",
            )
        )
        self.assertFalse(missing["ok"])
        self.assertIn("不存在", missing["routes"][0]["reason"])

    def test_keep_requires_confirmed_vault_boundary(self) -> None:
        outside = self.resolve(
            task(
                action="keep",
                target_path=str(self.outside),
                candidate="compare_canvas",
            )
        )
        no_vault = self.resolve(
            task(
                action="keep",
                target_path=str(self.canvas),
                candidate="compare_canvas",
            ),
            vault=None,
        )
        self.assertFalse(outside["ok"])
        self.assertIn("vault_root 内", outside["routes"][0]["reason"])
        self.assertFalse(no_vault["ok"])
        self.assertIn("vault_root", no_vault["routes"][0]["reason"])

    def test_open_route_accepts_create_and_answer(self) -> None:
        create = self.resolve(task(action="create", candidate="open_route"))
        answer = self.resolve(
            task(action="answer", candidate="open_route"), vault=None
        )
        self.assertTrue(create["ok"])
        self.assertTrue(answer["ok"])
        self.assertEqual(create["routes"][0]["reference"], resolve_route.OPEN_REFERENCE)
        self.assertEqual(answer["routes"][0]["reference"], resolve_route.OPEN_REFERENCE)

    def test_incompatible_action_and_candidate_blocks(self) -> None:
        result = self.resolve(
            task(action="answer", candidate="question_note"), vault=None
        )
        self.assertFalse(result["ok"])
        self.assertIn("不兼容", result["routes"][0]["reason"])

    def test_multi_queue_is_fully_routed_and_blocks_as_a_whole(self) -> None:
        tasks = [
            task("task_1", candidate="question_note"),
            task(
                "task_2",
                request_route="compare_canvas",
                candidate="question_note",
            ),
        ]
        result = resolve_route.resolve_routes(payload(tasks, str(self.vault)))
        self.assertFalse(result["ok"])
        self.assertEqual([item["id"] for item in result["routes"]], ["task_1", "task_2"])
        self.assertEqual(result["routes"][0]["reference"], resolve_route.QUESTION_REFERENCE)
        self.assertIsNotNone(result["routes"][1]["reason"])

    def test_cli_reads_temporary_input_and_returns_one_line(self) -> None:
        input_path = self.vault / "route-input.json"
        input_path.write_text(
            json.dumps(
                payload([task(candidate="compare_canvas")], str(self.vault)),
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        completed = subprocess.run(
            [sys.executable, str(SCRIPTS / "resolve_route.py"), "--input", str(input_path)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(len(completed.stdout.splitlines()), 1)
        result = json.loads(completed.stdout)
        self.assertTrue(result["ok"])
        self.assertTrue(input_path.exists())

    def test_cli_blocks_existing_update_target_outside_vault(self) -> None:
        input_path = self.root / "outside-route-input.json"
        input_path.write_text(
            json.dumps(
                payload(
                    [
                        task(
                            action="update",
                            target_path=str(self.outside),
                            candidate="compare_canvas",
                        )
                    ],
                    str(self.vault),
                ),
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        completed = subprocess.run(
            [sys.executable, str(SCRIPTS / "resolve_route.py"), "--input", str(input_path)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(completed.returncode, 0)
        result = json.loads(completed.stdout)
        self.assertFalse(result["ok"])
        self.assertIsNone(result["routes"][0]["reference"])
        self.assertIn("vault_root 内", result["routes"][0]["reason"])

    def test_invalid_schema_returns_cli_error(self) -> None:
        input_path = self.vault / "invalid-input.json"
        input_path.write_text("{}", encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(SCRIPTS / "resolve_route.py"), "--input", str(input_path)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(completed.returncode, 1)
        result = json.loads(completed.stdout)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "invalid_input")


if __name__ == "__main__":
    unittest.main()
