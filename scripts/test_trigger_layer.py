import json
import os
import tempfile
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import jinhua


CODEX_COMMON_OUTPUT_KEYS = {
    "continue",
    "decision",
    "hookSpecificOutput",
    "reason",
    "stopReason",
    "suppressOutput",
    "systemMessage",
}


def args_for(root: Path) -> Namespace:
    return Namespace(
        project_root=str(root),
        runtime_dir="",
        global_runtime_dir="",
        project_id="",
        agent_profile="",
    )


def test_input_correction_classifier() -> None:
    assert jinhua.classify_user_correction("不是，我说的是实现逻辑，不要写代码。")["input_state"] == "strong_user_correction"
    assert jinhua.classify_user_correction("帮我写一个 README。")["input_state"] == "none"
    assert (
        jinhua.classify_user_correction("你刚才没懂，我是要你改触发方式，不要改 Skill 内核。")["input_state"]
        == "strong_user_correction"
    )
    assert jinhua.classify_user_correction("再详细一点。")["input_state"] in {"none", "possible_user_correction"}
    assert jinhua.classify_user_correction("不要列表，写成一段。")["input_state"] in {"none", "possible_user_correction"}
    assert jinhua.classify_user_correction("agent为什么没自动判断啊？")["input_state"] == "strong_user_correction"
    assert jinhua.classify_user_correction("本来应该触发 jinhua.skill。")["input_state"] == "strong_user_correction"
    assert jinhua.classify_user_correction("不要只解释，应该直接生成提案。")["input_state"] == "strong_user_correction"
    result = jinhua.classify_user_correction("为什么没有自动触发 hook？")
    assert result["input_state"] == "strong_user_correction"
    assert "tool_skill_procedure_miss" in result["categories"]
    assert jinhua.classify_user_correction("继续。")["input_state"] == "none"
    assert jinhua.classify_user_correction("帮我润色一下。")["input_state"] == "none"


def test_internal_context_stays_short_and_safe() -> None:
    context = jinhua.classify_user_correction("你没懂，重新看我的要求。")["internal_context"]
    assert "Prioritize fixing the mismatch" in context
    assert "log-signal" not in context
    assert "propose" not in context
    assert len(context) < 260


def test_invocation_guard_deduplicates_same_turn() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        args = args_for(Path(tmp))
        first = jinhua.invocation_guard(args, "s1", "t1", "agent", "same reason", "cycle", mark=True)
        second = jinhua.invocation_guard(args, "s1", "t1", "stop", "same reason", "output_state", mark=False)
        assert first["decision"] == "allow"
        assert second["decision"] == "already_handled"


def test_agent_direct_call_is_allowed_once() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        args = args_for(Path(tmp))
        payload = {
            "session_id": "s1",
            "turn_id": "t2",
            "tool_name": "Bash",
            "tool_input": {
                "command": f'python "{Path(jinhua.__file__).resolve()}" --project-root "{tmp}" cycle'
            },
        }
        first = jinhua.codex_post_tool_use_output(payload, args)
        second = jinhua.codex_post_tool_use_output(payload, args)
        later_entry = {
            **payload,
            "tool_input": {
                "command": f'python "{Path(jinhua.__file__).resolve()}" --project-root "{tmp}" log-signal'
            },
        }
        third = jinhua.codex_post_tool_use_output(later_entry, args)
        assert first == {"continue": True}
        assert second == {"continue": True}
        assert third == {"continue": True}
        state = jinhua.read_guard_state(args)
        assert len(state["events"]) == 1
        assert state["events"][0]["entry"] == "cycle"


def test_post_tool_use_requires_authoritative_shell_command_input() -> None:
    command_text = "python scripts/jinhua.py cycle"
    with tempfile.TemporaryDirectory() as tmp:
        args = args_for(Path(tmp))
        payloads = [
            {
                "session_id": "s1",
                "turn_id": "prompt-mention",
                "prompt": f"Explain {command_text}",
                "tool_name": "Bash",
                "tool_input": {"command": "Get-Content README.md"},
            },
            {
                "session_id": "s1",
                "turn_id": "read-output",
                "tool_name": "Bash",
                "tool_input": {"command": "Get-Content README.md"},
                "tool_response": f"README example: {command_text}",
            },
            {
                "session_id": "s1",
                "turn_id": "error-output",
                "tool_name": "Bash",
                "tool_input": {"command": "Get-Content missing.md"},
                "tool_response": {"stderr": f"Failed near {command_text}"},
            },
            {
                "session_id": "s1",
                "turn_id": "search-pattern",
                "tool_name": "Bash",
                "tool_input": {"command": f'rg "{command_text}" README.md'},
            },
            {
                "session_id": "s1",
                "turn_id": "function-source",
                "tool_name": "functions.exec",
                "tool_input": f"await tools.shell_command({{command: '{command_text}'}})",
            },
            {
                "session_id": "s1",
                "turn_id": "nested-output",
                "tool_response": {"tool_input": {"command": command_text}},
            },
        ]
        for payload in payloads:
            assert jinhua.codex_post_tool_use_output(payload, args) == {"continue": True}
        assert not jinhua.invocation_guard_path(args).exists()


def test_real_shell_command_and_supported_wrappers_are_detected() -> None:
    assert jinhua.jinhua_entry_from_command("python scripts/jinhua.py cycle") == "cycle"
    assert jinhua.jinhua_entry_from_command("python scripts/jinhua.py --project-root . log-signal") == "log-signal"
    assert jinhua.jinhua_entry_from_command('powershell -Command "python scripts/jinhua.py global-cycle"') == "global-cycle"
    assert jinhua.jinhua_entry_from_command('rg "python scripts/jinhua.py cycle" README.md') == ""
    assert jinhua.jinhua_entry_from_command("Write-Output 'python scripts/jinhua.py cycle'") == ""


def test_authoritative_metadata_ignores_tool_response_fields() -> None:
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as fake:
        payload = {
            "cwd": tmp,
            "session_id": "real-session",
            "turn_id": "real-turn",
            "tool_response": {
                "cwd": fake,
                "session_id": "fake-session",
                "turn_id": "fake-turn",
            },
        }
        args = args_for(Path("."))
        assert jinhua.apply_payload_project_root(args, payload) is True
        assert Path(args.project_root) == Path(tmp).resolve()
        assert jinhua.hook_session_id(payload) == jinhua.method_hash("real-session")
        assert jinhua.hook_turn_id(payload) == jinhua.method_hash("real-turn")


def test_unknown_payload_does_not_select_output_project_or_write_guard() -> None:
    with tempfile.TemporaryDirectory() as fake:
        env = {key: "" for key in jinhua.HOOK_PROJECT_ENV_KEYS}
        args = args_for(Path("."))
        payload = {
            "tool_response": {
                "cwd": fake,
                "session_id": "fake-session",
                "turn_id": "fake-turn",
                "command": "python scripts/jinhua.py cycle",
            }
        }
        with patch.dict(os.environ, env, clear=False), patch.object(
            jinhua.Path,
            "cwd",
            return_value=jinhua.skill_root(),
        ):
            assert jinhua.apply_payload_project_root(args, payload) is False
        assert jinhua.codex_post_tool_use_output(payload, args) == {"continue": True}
        assert not (Path(fake) / ".jinhua" / "runtime" / "invocation-guard.json").exists()


def test_missing_session_or_turn_identity_does_not_write_guard() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        args = args_for(Path(tmp))
        command_payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "python scripts/jinhua.py cycle"},
        }
        prompt_payload = {"prompt": "普通问题"}
        assert jinhua.codex_post_tool_use_output(command_payload, args) == {"continue": True}
        assert jinhua.codex_user_prompt_submit_output(prompt_payload, args) == {"continue": True}
        assert not jinhua.invocation_guard_path(args).exists()


def test_claude_prompt_id_is_a_turn_identity() -> None:
    post_payload = {
        "session_id": "claude-session",
        "prompt_id": "claude-prompt",
        "tool_name": "Bash",
        "tool_input": {"command": "python scripts/jinhua.py cycle"},
    }
    stop_payload = {
        "session_id": "claude-session",
        "prompt_id": "claude-prompt",
        "stop_hook_active": False,
    }
    assert jinhua.hook_turn_id(post_payload) == jinhua.hook_turn_id(stop_payload)


def test_stop_does_not_require_or_parse_output_tail() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        args = args_for(Path(tmp))
        payload = {
            "session_id": "s1",
            "turn_id": "t3",
            "last_assistant_message": "Done.\n\noutput_state: jinhua_candidate\nvisibility: silent",
        }
        assert jinhua.codex_stop_output(payload, args) == {"continue": True}
        state = jinhua.read_guard_state(args)
        assert state["stop_tickets"] == []


def test_periodic_stop_is_per_session_and_light() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        args = args_for(Path(tmp))
        with patch.dict(os.environ, {"JINHUA_PERIODIC_STOP_INTERVAL": "1"}, clear=False):
            assert jinhua.periodic_stop_interval() == 8
            for index in range(1, 8):
                payload = {"session_id": "s1", "turn_id": f"u{index}", "prompt": "普通问题"}
                output = jinhua.codex_user_prompt_submit_output(payload, args)
                assert output == {"continue": True}
                state = jinhua.read_guard_state(args)
                assert state["sessions"][jinhua.hook_session_id(payload)]["periodic_stop_due"] is False

        due_payload = {"session_id": "s1", "turn_id": "u8", "prompt": "普通问题"}
        due_output = jinhua.codex_user_prompt_submit_output(due_payload, args)
        assert due_output == {"continue": True}
        state = jinhua.read_guard_state(args)
        assert state["sessions"][jinhua.hook_session_id(due_payload)]["periodic_stop_due"] is True

        other_session = {"session_id": "s2", "turn_id": "u1", "prompt": "普通问题"}
        other_output = jinhua.codex_user_prompt_submit_output(other_session, args)
        assert other_output == {"continue": True}
        state = jinhua.read_guard_state(args)
        other_state = state["sessions"][jinhua.hook_session_id(other_session)]
        assert other_state["turn_count"] == 1
        assert other_state["periodic_stop_due"] is False

        stop_payload = {"session_id": "s1", "turn_id": "a8", "last_assistant_message": "Done."}
        first_stop = jinhua.codex_stop_output(stop_payload, args)
        assert first_stop["decision"] == "block"
        context = first_stop["reason"]
        assert "Periodic jinhua check..." in context
        assert "prior conversation" in context
        assert len(context) < 170

        second_stop = jinhua.codex_stop_output(stop_payload, args)
        assert second_stop == {"continue": True}
        state = jinhua.read_guard_state(args)
        assert state["sessions"][jinhua.hook_session_id(stop_payload)]["periodic_stop_due"] is False


def test_periodic_stop_skips_when_jinhua_already_ran() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        args = args_for(Path(tmp))
        for index in range(1, 9):
            jinhua.codex_user_prompt_submit_output(
                {"session_id": "s1", "turn_id": f"u{index}", "prompt": "普通问题"},
                args,
            )
        stop_payload = {"session_id": "s1", "turn_id": "a8"}
        jinhua.invocation_guard(
            args,
            jinhua.hook_session_id(stop_payload),
            jinhua.hook_turn_id(stop_payload),
            "agent",
            "cycle",
            "cycle",
            mark=True,
        )
        assert jinhua.codex_stop_output(stop_payload, args) == {"continue": True}
        state = jinhua.read_guard_state(args)
        assert state["sessions"][jinhua.hook_session_id(stop_payload)]["periodic_stop_due"] is False


def test_codex_hook_config_uses_plugin_root_for_all_events() -> None:
    root = Path(jinhua.__file__).resolve().parents[1]
    config = json.loads((root / "hooks" / "codex-hooks.json").read_text(encoding="utf-8"))
    for event, script in {
        "UserPromptSubmit": "codex_user_prompt_submit.py",
        "PostToolUse": "codex_post_tool_use.py",
        "Stop": "codex_stop.py",
    }.items():
        hook = config["hooks"][event][0]["hooks"][0]
        assert "<jinhua-dir>" not in hook["command"]
        assert hook["command"] == f'python "${{CLAUDE_PLUGIN_ROOT}}/hooks/{script}"'
        assert hook["commandWindows"] == f'python "${{CLAUDE_PLUGIN_ROOT}}/hooks/{script}"'
    config_text = json.dumps(config).lower()
    assert "output state" not in config_text
    assert "periodic review" in config_text


def test_codex_payload_cwd_selects_runtime_project() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp)
        args = args_for(Path("."))
        payload = {
            "cwd": str(project),
            "session_id": "wrapper-session",
            "turn_id": "wrapper-turn",
            "prompt": "普通问题",
        }
        jinhua.apply_payload_project_root(args, payload)
        assert Path(args.project_root) == project.resolve()
        output = jinhua.codex_user_prompt_submit_output(payload, args)
        assert output == {"continue": True}
        guard_path = project / ".jinhua" / "runtime" / "invocation-guard.json"
        assert guard_path.exists()
        guard = json.loads(guard_path.read_text(encoding="utf-8"))
        assert guard["sessions"][jinhua.hook_session_id(payload)]["turn_count"] == 1


def test_hook_payload_accepts_utf8_bom() -> None:
    payload = {"cwd": "C:/tmp/jinhua-project", "session_id": "bom-session", "prompt": "普通问题"}
    parsed = jinhua.read_hook_payload("\ufeff" + json.dumps(payload))
    assert parsed["cwd"] == payload["cwd"]


def test_nested_codex_payload_cwd_selects_runtime_project() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp)
        args = args_for(Path("."))
        payload = {
            "event": {"context": {"cwd": str(project)}},
            "session_id": "nested-session",
            "turn_id": "nested-turn",
            "prompt": "普通问题",
        }
        assert jinhua.apply_payload_project_root(args, payload) is True
        assert Path(args.project_root) == project.resolve()
        output = jinhua.codex_user_prompt_submit_output(payload, args)
        assert output == {"continue": True}
        assert (project / ".jinhua" / "runtime" / "invocation-guard.json").exists()


def test_hook_does_not_use_plugin_directory_as_implicit_project() -> None:
    env = {key: "" for key in jinhua.HOOK_PROJECT_ENV_KEYS}
    with patch.dict(os.environ, env, clear=False), patch.object(
        jinhua.Path,
        "cwd",
        return_value=jinhua.skill_root(),
    ):
        args = args_for(Path("."))
        payload = {"session_id": "no-root-session", "turn_id": "no-root-turn", "prompt": "普通问题"}
        assert jinhua.apply_payload_project_root(args, payload) is False
        output = jinhua.codex_user_prompt_submit_output(payload, args)
        assert output == {"continue": True}


def test_stop_hook_active_never_blocks_or_consumes_due() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        args = args_for(Path(tmp))
        for index in range(1, 9):
            jinhua.codex_user_prompt_submit_output(
                {"session_id": "s1", "turn_id": f"u{index}", "prompt": "普通问题"},
                args,
            )
        payload = {
            "session_id": "s1",
            "turn_id": "active-stop",
            "stop_hook_active": True,
            "last_assistant_message": "Done.",
        }
        output = jinhua.codex_stop_output(payload, args)
        assert output == {"continue": True}
        state = jinhua.read_guard_state(args)
        assert state["sessions"][jinhua.hook_session_id(payload)]["periodic_stop_due"] is True


def test_stop_ignores_fake_active_flag_in_tool_response() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        args = args_for(Path(tmp))
        for index in range(1, 9):
            jinhua.codex_user_prompt_submit_output(
                {"session_id": "s1", "turn_id": f"u{index}", "prompt": "普通问题"},
                args,
            )
        payload = {
            "session_id": "s1",
            "turn_id": "real-stop",
            "stop_hook_active": False,
            "tool_response": {"stop_hook_active": True},
        }
        output = jinhua.codex_stop_output(payload, args)
        assert output["decision"] == "block"
        assert "Periodic jinhua check..." in output["reason"]


def test_hook_outputs_only_use_codex_wire_keys() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        args = args_for(Path(tmp))
        prompt_output = jinhua.codex_user_prompt_submit_output(
            {"cwd": tmp, "session_id": "s1", "turn_id": "t1", "prompt": "你没懂，重新看要求"},
            args,
        )
        post_output = jinhua.codex_post_tool_use_output(
            {"cwd": tmp, "session_id": "s1", "turn_id": "t1", "tool_input": "python jinhua.py cycle"},
            args,
        )
        stop_output = jinhua.codex_stop_output(
            {"cwd": tmp, "session_id": "s1", "turn_id": "t2", "last_assistant_message": "Done."},
            args,
        )
        for output in (prompt_output, post_output, stop_output):
            assert set(output).issubset(CODEX_COMMON_OUTPUT_KEYS)
        assert "jinhua" not in prompt_output
        assert "jinhua" not in post_output
        assert "jinhua" not in stop_output
        assert "hookSpecificOutput" in prompt_output
        assert "hookSpecificOutput" not in stop_output


def test_ready_attention_surfaces_ready_clusters_without_mutating_ledger() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        args = args_for(Path(tmp))
        jinhua.initialize_runtime(args, quiet=True)
        jinhua.write_cluster_state(args, {
            "schema_version": "3.0",
            "updated_at": "",
            "clusters": {
                "other:ready_example": {
                    "cluster_key": "other:ready_example",
                    "operator": "other",
                    "signal_count": 3,
                    "strength_sum": 5,
                    "sample_signal_ids": [],
                    "last_seen": "",
                    "status": "ready",
                    "ready_reason": "signal_count >= 3",
                }
            },
        })

        payload = {"session_id": "s1", "turn_id": "u1", "prompt": "普通问题"}
        output = jinhua.codex_user_prompt_submit_output(payload, args)
        context = output["hookSpecificOutput"]["additionalContext"]
        assert "ready clusters" in context
        assert "Run cycle" in context
        assert "create one proposal or state a concrete skip reason" in context
        assert jinhua.read_jsonl(jinhua.data_dir(args) / "signals.jsonl") == []
        assert jinhua.read_jsonl(jinhua.data_dir(args) / "proposals.jsonl") == []


def test_ready_attention_pending_gate_takes_priority() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        args = args_for(Path(tmp))
        jinhua.initialize_runtime(args, quiet=True)
        jinhua.write_cluster_state(args, {
            "schema_version": "3.0",
            "updated_at": "",
            "clusters": {
                "other:ready_example": {
                    "cluster_key": "other:ready_example",
                    "operator": "other",
                    "status": "ready",
                }
            },
        })
        jinhua.append_jsonl(jinhua.data_dir(args) / "proposals.jsonl", {
            "id": "prop_test",
            "cluster_key": "other:ready_example",
            "status": "pending_user_gate",
        })

        payload = {"session_id": "s1", "turn_id": "u1", "prompt": "普通问题"}
        output = jinhua.codex_user_prompt_submit_output(payload, args)
        context = output["hookSpecificOutput"]["additionalContext"]
        assert "pending user gates" in context
        assert "surface one gate" in context


def test_removed_trigger_commands_are_absent() -> None:
    help_text = jinhua.build_parser().format_help()
    for command in ["wake-check", "hook-user-prompt-submit", "parse-output-state"]:
        assert command not in help_text
    assert not hasattr(jinhua, "parse_output_state")
    assert not hasattr(jinhua, "wake_check_result")


def test_old_hook_is_not_manifest_primary_path() -> None:
    root = Path(jinhua.__file__).resolve().parents[1]
    codex_manifest = (root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    claude_manifest = (root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    assert "hooks/codex-hooks.json" in codex_manifest
    assert "claude-codex-hooks.json" not in codex_manifest
    assert "claude-codex-hooks.json" not in claude_manifest


if __name__ == "__main__":
    test_input_correction_classifier()
    test_internal_context_stays_short_and_safe()
    test_invocation_guard_deduplicates_same_turn()
    test_agent_direct_call_is_allowed_once()
    test_post_tool_use_requires_authoritative_shell_command_input()
    test_real_shell_command_and_supported_wrappers_are_detected()
    test_authoritative_metadata_ignores_tool_response_fields()
    test_unknown_payload_does_not_select_output_project_or_write_guard()
    test_missing_session_or_turn_identity_does_not_write_guard()
    test_claude_prompt_id_is_a_turn_identity()
    test_stop_does_not_require_or_parse_output_tail()
    test_periodic_stop_is_per_session_and_light()
    test_periodic_stop_skips_when_jinhua_already_ran()
    test_codex_hook_config_uses_plugin_root_for_all_events()
    test_codex_payload_cwd_selects_runtime_project()
    test_hook_payload_accepts_utf8_bom()
    test_nested_codex_payload_cwd_selects_runtime_project()
    test_hook_does_not_use_plugin_directory_as_implicit_project()
    test_stop_hook_active_never_blocks_or_consumes_due()
    test_stop_ignores_fake_active_flag_in_tool_response()
    test_hook_outputs_only_use_codex_wire_keys()
    test_ready_attention_surfaces_ready_clusters_without_mutating_ledger()
    test_ready_attention_pending_gate_takes_priority()
    test_removed_trigger_commands_are_absent()
    test_old_hook_is_not_manifest_primary_path()
    print("trigger-layer tests passed")
