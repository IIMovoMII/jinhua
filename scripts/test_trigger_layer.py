import tempfile
from argparse import Namespace
from pathlib import Path

import jinhua


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


def test_output_state_parse_and_strip() -> None:
    ok = jinhua.parse_output_state("Done.\n\noutput_state: ok\nvisibility: silent\n")
    assert ok["valid"] is True
    assert ok["output_state"] == "ok"
    assert ok["user_visible_text"] == "Done."

    candidate = jinhua.parse_output_state(
        "正文\n\noutput_state: jinhua_candidate\nvisibility: silent\nreason: 这次纠错可能暴露出可复用方法论经验\n"
    )
    assert candidate["valid"] is True
    assert candidate["output_state"] == "jinhua_candidate"
    assert candidate["reason"] == "这次纠错可能暴露出可复用方法论经验"
    assert "output_state" not in candidate["user_visible_text"]


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
            "tool_input": f'python "{Path(jinhua.__file__).resolve()}" --project-root "{tmp}" cycle',
        }
        first = jinhua.codex_post_tool_use_output(payload, args)
        second = jinhua.codex_post_tool_use_output(payload, args)
        assert first["jinhua"]["invocation_guard"]["decision"] == "allow"
        assert second["jinhua"]["invocation_guard"]["decision"] == "skip_duplicate"


def test_stop_missing_tail_tickets_once() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        args = args_for(Path(tmp))
        payload = {"session_id": "s1", "turn_id": "t3", "last_assistant_message": "Done."}
        first = jinhua.codex_stop_output(payload, args)
        second = jinhua.codex_stop_output(payload, args)
        assert first["jinhua"]["missing_tail_ticketed"] is True
        assert second["jinhua"]["missing_tail_ticketed"] is False


def test_periodic_stop_is_per_session_and_light() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        args = args_for(Path(tmp))
        for index in range(1, 8):
            payload = {"session_id": "s1", "turn_id": f"u{index}", "prompt": "普通问题"}
            output = jinhua.codex_user_prompt_submit_output(payload, args)
            assert output["jinhua"]["turn_state"]["periodic_stop_due"] is False

        due_payload = {"session_id": "s1", "turn_id": "u8", "prompt": "普通问题"}
        due_output = jinhua.codex_user_prompt_submit_output(due_payload, args)
        assert due_output["jinhua"]["turn_state"]["periodic_stop_due"] is True

        other_session = {"session_id": "s2", "turn_id": "u1", "prompt": "普通问题"}
        other_output = jinhua.codex_user_prompt_submit_output(other_session, args)
        assert other_output["jinhua"]["turn_state"]["turn_count"] == 1
        assert other_output["jinhua"]["turn_state"]["periodic_stop_due"] is False

        stop_payload = {"session_id": "s1", "turn_id": "a8", "last_assistant_message": "Done."}
        first_stop = jinhua.codex_stop_output(stop_payload, args)
        assert first_stop["jinhua"]["periodic_stop"]["due"] is True
        context = first_stop["hookSpecificOutput"]["additionalContext"]
        assert "prior conversation" in context
        assert len(context) < 170

        second_stop = jinhua.codex_stop_output(stop_payload, args)
        assert "periodic_stop" not in second_stop["jinhua"]


def test_ready_attention_surfaces_ready_clusters_without_mutating_ledger() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        args = args_for(Path(tmp))
        jinhua.initialize_runtime(args, quiet=True)
        jinhua.write_cluster_state(args, {
            "schema_version": "2.0",
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
            "schema_version": "2.0",
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


def test_stop_candidate_skips_when_turn_already_called_jinhua() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        args = args_for(Path(tmp))
        payload = {
            "session_id": "s1",
            "turn_id": "t4",
            "last_assistant_message": "Done.\n\noutput_state: jinhua_candidate\nvisibility: silent\nreason: reusable correction",
        }
        jinhua.invocation_guard(
            args,
            jinhua.hook_session_id(payload),
            jinhua.hook_turn_id(payload),
            "agent",
            "cycle",
            "cycle",
            mark=True,
        )
        output = jinhua.codex_stop_output(payload, args)
        assert output["jinhua"]["invocation_guard"]["decision"] == "already_handled"
        assert "hookSpecificOutput" not in output


def test_legacy_wake_check_is_not_primary_but_still_works() -> None:
    assert jinhua.wake_check_result("为什么没触发jinhua.skill？")["legacy"] is True
    assert jinhua.wake_check_result("Fix the typo in the heading.")["should_route"] is False


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
    test_output_state_parse_and_strip()
    test_invocation_guard_deduplicates_same_turn()
    test_agent_direct_call_is_allowed_once()
    test_stop_missing_tail_tickets_once()
    test_periodic_stop_is_per_session_and_light()
    test_ready_attention_surfaces_ready_clusters_without_mutating_ledger()
    test_ready_attention_pending_gate_takes_priority()
    test_stop_candidate_skips_when_turn_already_called_jinhua()
    test_legacy_wake_check_is_not_primary_but_still_works()
    test_old_hook_is_not_manifest_primary_path()
    print("trigger-layer tests passed")
