import json
import subprocess
import sys
import tempfile
from argparse import Namespace
from pathlib import Path

import jinhua


SCRIPT = Path(jinhua.__file__).resolve()


def args_for(root: Path, global_root: Path | None = None, project_id: str = "") -> Namespace:
    return Namespace(
        project_root=str(root),
        runtime_dir="",
        global_runtime_dir=str(global_root) if global_root else "",
        project_id=project_id,
        agent_profile="codex",
        allow_skill_source_runtime=False,
    )


def run_cli(
    root: Path,
    *arguments: str,
    global_root: Path | None = None,
    project_id: str = "",
    expect: int = 0,
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(SCRIPT), "--project-root", str(root)]
    if global_root:
        command.extend(["--global-runtime-dir", str(global_root)])
    if project_id:
        command.extend(["--project-id", project_id])
    command.extend(arguments)
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", check=False)
    assert result.returncode == expect, result.stdout + result.stderr
    return result


def log_signal(
    root: Path,
    cluster_key: str,
    strength: int,
    *,
    global_root: Path | None = None,
    project_id: str = "",
    immediate: bool = False,
    source_type: str = "user_correction",
    action: str = "verify the reusable method before claiming success",
) -> None:
    command = [
        "log-signal",
        "--source-type",
        source_type,
        "--summary",
        "Verify the reusable method before claiming success",
        "--operator",
        cluster_key.split(":", 1)[0],
        "--cluster-key",
        cluster_key,
        "--context",
        "testing the deterministic core loop",
        "--strength",
        str(strength),
        "--trigger",
        "a reusable workflow claim needs verification",
        "--action",
        action,
        "--transfer-conditions",
        "coding agent workflows",
        "--negative-cases",
        "one-off content edits",
        "--verification-path",
        "inspect the resulting state",
        "--auto-init",
    ]
    if immediate:
        command.append("--immediate")
    run_cli(root, *command, global_root=global_root, project_id=project_id)


def cluster(root: Path, key: str) -> dict:
    state = json.loads((root / ".jinhua" / "data" / "cluster-state.json").read_text(encoding="utf-8"))
    return state["clusters"][key]


def test_initialization_and_local_thresholds() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        run_cli(root, "init")
        data = root / ".jinhua" / "data"
        assert json.loads((data / "evolution-state.json").read_text(encoding="utf-8"))["schema_version"] == "3.0"
        assert json.loads((data / "cluster-state.json").read_text(encoding="utf-8"))["schema_version"] == "3.0"
        assert not (data / "crystallized-operators.jsonl").exists()

        count_key = "verification_path:count_threshold"
        for _ in range(2):
            log_signal(root, count_key, 1)
            assert cluster(root, count_key)["status"] == "active"
        log_signal(root, count_key, 1)
        assert cluster(root, count_key)["status"] == "ready"

        strength_key = "verification_path:strength_threshold"
        log_signal(root, strength_key, 3)
        log_signal(root, strength_key, 2)
        assert cluster(root, strength_key)["signal_count"] == 2
        assert cluster(root, strength_key)["status"] == "ready"

        immediate_key = "verification_path:immediate_threshold"
        log_signal(root, immediate_key, 1, immediate=True)
        assert cluster(root, immediate_key)["status"] == "ready"


def test_complete_proposal_apply_revision_and_cooldown() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        key = "constraint_recognition:project_rule_flow"
        for _ in range(3):
            log_signal(root, key, 1)

        incomplete = run_cli(
            root,
            "propose",
            "--cluster-key",
            key,
            "--placement",
            "project_rule",
            "--target",
            "AGENTS.md",
            "--patch",
            "## Verify First\n\nVerify before claiming success.",
            expect=2,
        )
        assert "--risk" in incomplete.stderr

        run_cli(
            root,
            "propose",
            "--cluster-key",
            key,
            "--placement",
            "project_rule",
            "--target",
            "AGENTS.md",
            "--patch",
            "## Verify First\n\nVerify before claiming success.",
            "--risk",
            "May add unnecessary checks to trivial edits.",
        )
        data = root / ".jinhua" / "data"
        proposals = jinhua.read_jsonl(data / "proposals.jsonl")
        proposal_id = proposals[-1]["id"]
        assert proposals[-1]["status"] == "pending_user_gate"
        assert "decision" not in proposals[-1]

        changed_placement = run_cli(
            root,
            "apply-proposal",
            "--proposal-id",
            proposal_id,
            "--placement",
            "skill_patch",
            "--applied-target",
            "missing-skill/SKILL.md",
            "--summary",
            "Should not be recorded without a concrete Skill recommendation.",
            expect=1,
        )
        assert "revise the proposal first" in changed_placement.stderr

        target = root / "AGENTS.md"
        target.write_text("# Rules\n", encoding="utf-8")
        before = target.read_text(encoding="utf-8")
        run_cli(
            root,
            "apply-proposal",
            "--proposal-id",
            proposal_id,
            "--placement",
            "project_rule",
            "--applied-target",
            str(target),
            "--summary",
            "Added the verified project rule through the host editor.",
        )
        assert target.read_text(encoding="utf-8") == before
        adopted = jinhua.read_jsonl(data / "adopted-edits.jsonl")[-1]
        assert adopted["applied_target"] == str(target)
        assert "applied_path" not in adopted
        assert cluster(root, key)["status"] == "adopted"

        reject_key = "constraint_recognition:revision_and_cooldown"
        log_signal(root, reject_key, 1, immediate=True)
        run_cli(
            root,
            "propose",
            "--cluster-key",
            reject_key,
            "--placement",
            "project_rule",
            "--target",
            "AGENTS.md",
            "--patch",
            "## Review Scope\n\nReview scope before changing shared behavior.",
            "--risk",
            "Could slow urgent local repairs.",
        )
        proposal_id = jinhua.read_jsonl(data / "proposals.jsonl")[-1]["id"]
        run_cli(root, "reject-proposal", "--proposal-id", proposal_id, "--reason", "Narrow the rule.", "--revision")
        assert jinhua.read_jsonl(data / "proposals.jsonl")[-1]["status"] == "needs_revision"
        run_cli(root, "reject-proposal", "--proposal-id", proposal_id, "--reason", "Not useful enough.")
        assert cluster(root, reject_key)["cooldown_signal_remaining"] == 5
        for remaining in range(4, 0, -1):
            log_signal(root, reject_key, 1)
            assert cluster(root, reject_key)["status"] == "cooldown"
            assert cluster(root, reject_key)["cooldown_signal_remaining"] == remaining
        log_signal(root, reject_key, 1)
        assert cluster(root, reject_key)["status"] == "ready"
        assert cluster(root, reject_key)["cooldown_signal_remaining"] == 0
        run_cli(root, "validate")


def populate_global_project(global_root: Path, project_id: str, strengths: list[int], action: str) -> Path:
    root = global_root.parent / project_id
    root.mkdir()
    key = "verification_path:shared_global_method"
    for strength in strengths:
        log_signal(root, key, strength, global_root=global_root, project_id=project_id, action=action)
    run_cli(root, "cycle", global_root=global_root, project_id=project_id)
    return root


def test_global_thresholds_identity_and_dedupe() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        global_root = base / "global"
        action = "read the README and relevant source before recommending"
        projects = [
            populate_global_project(global_root, "project-one", [2, 2], action),
            populate_global_project(global_root, "project-two", [1, 1], action),
            populate_global_project(global_root, "project-three", [1], action),
        ]
        clusters = json.loads((global_root / "global-clusters.json").read_text(encoding="utf-8"))["clusters"]
        assert len(clusters) == 1
        method = next(iter(clusters.values()))
        assert method["status"] == "ready"
        assert method["evidence_count"] == 5
        assert method["strength_sum"] == 7
        assert len(method["project_hashes"]) == 3

        signal_count = len(jinhua.read_jsonl(global_root / "global-signals.jsonl"))
        run_cli(projects[0], "cycle", global_root=global_root, project_id="project-one")
        assert len(jinhua.read_jsonl(global_root / "global-signals.jsonl")) == signal_count
        index_text = (global_root / "project-index.json").read_text(encoding="utf-8")
        assert "project-one" not in index_text
        assert json.loads(index_text)["schema_version"] == "2.0"

        left = {"operator": "verification_path", "action": action, "trigger": "case one"}
        right = {"operator": "verification_path", "action": action, "trigger": "case two"}
        assert jinhua.method_fingerprint_for_signal(left) == jinhua.method_fingerprint_for_signal(right)

        fingerprint = next(iter(clusters))
        target = base / "global-skill.md"
        target.write_text("# Existing\n", encoding="utf-8")
        before = target.read_text(encoding="utf-8")
        run_cli(
            projects[0],
            "global-propose",
            "--method-fingerprint",
            fingerprint,
            "--placement",
            "personal_global_skill",
            "--target",
            str(target),
            "--patch",
            "## Source Verification\n\nRead the README and relevant source before recommending adoption.",
            "--risk",
            "May add unnecessary work to quick name-only requests.",
            global_root=global_root,
            project_id="project-one",
        )
        global_proposals = jinhua.read_jsonl(global_root / "global-proposals.jsonl")
        global_proposal = global_proposals[-1]
        assert global_proposal["status"] == "pending_user_gate"
        assert "decision" not in global_proposal
        global_proposal["recommended_skill"] = ""
        global_proposal["recommended_skill_path"] = ""
        jinhua.write_jsonl(global_root / "global-proposals.jsonl", global_proposals)
        changed_placement = run_cli(
            projects[0],
            "global-apply",
            "--proposal-id",
            global_proposal["id"],
            "--placement",
            "skill_patch",
            "--applied-target",
            str(target),
            "--summary",
            "Should not be adopted without a concrete Skill recommendation.",
            global_root=global_root,
            project_id="project-one",
            expect=1,
        )
        assert "revise the proposal first" in changed_placement.stderr
        run_cli(
            projects[0],
            "global-apply",
            "--proposal-id",
            global_proposal["id"],
            "--placement",
            "personal_global_skill",
            "--applied-target",
            str(target),
            "--summary",
            "Recorded the host-edited and verified global rule.",
            global_root=global_root,
            project_id="project-one",
        )
        assert target.read_text(encoding="utf-8") == before
        adopted = jinhua.read_jsonl(global_root / "adopted-global-edits.jsonl")[-1]
        assert adopted["applied_target"] == str(target)
        assert "applied_path" not in adopted

        fast_global = base / "fast-global"
        populate_global_project(fast_global, "fast-one", [3], action)
        populate_global_project(fast_global, "fast-two", [3], action)
        fast = next(iter(json.loads((fast_global / "global-clusters.json").read_text(encoding="utf-8"))["clusters"].values()))
        assert fast["status"] == "ready"
        assert "fast path" in fast["ready_reason"]


def write_old_local_runtime(root: Path, malformed: bool = False) -> Namespace:
    args = args_for(root)
    data = root / ".jinhua" / "data"
    data.mkdir(parents=True)
    (data / "evolution-state.json").write_text(
        json.dumps({"schema_version": "2.0", "last_proposal_id": "p1", "total_signal_count": 1,
                    "adopted_edit_count": 1, "rejected_proposal_count": 1, "updated_at": ""}),
        encoding="utf-8",
    )
    signal = {
        "id": "s1", "timestamp": "2026-01-01T00:00:00Z", "source_type": "user_correction",
        "summary": "summary", "context": "context", "operator": "verification_path",
        "cluster_key": "verification_path:migrate", "strength": 2, "status": "compacted", "confidence": 0.8,
    }
    (data / "signals.jsonl").write_text("{broken\n" if malformed else json.dumps(signal) + "\n", encoding="utf-8")
    proposal = {
        "id": "p1", "timestamp": "2026-01-01T00:00:00Z", "cluster_key": "verification_path:migrate",
        "decision": "core_operator_promotion", "trigger": "old trigger", "evidence_signal_ids": ["s1"],
        "target": "C:/skills/example/SKILL.md", "patch": "old patch", "risk": "old risk", "status": "applied",
        "applied_path": "C:/skills/example/SKILL.md", "write_status": "written",
    }
    (data / "proposals.jsonl").write_text(json.dumps(proposal) + "\n", encoding="utf-8")
    adopted = {
        "id": "a1", "timestamp": "2026-01-01T00:00:00Z", "proposal_id": "p1",
        "target_skill": "fallback", "applied_path": "C:/skills/example/SKILL.md", "write_status": "written",
        "decision": "core_operator_promotion", "edit_summary": "old summary",
    }
    (data / "adopted-edits.jsonl").write_text(json.dumps(adopted) + "\n", encoding="utf-8")
    rejected = {
        "id": "r1", "timestamp": "2026-01-01T00:00:00Z", "proposal_id": "p1",
        "cluster_key": "verification_path:migrate", "reason": "old reason",
        "cooldown_until": "2099-01-01T00:00:00Z", "cooldown_signal_remaining": 0,
    }
    (data / "rejected-proposals.jsonl").write_text(json.dumps(rejected) + "\n", encoding="utf-8")
    cluster_state = {
        "schema_version": "2.0", "updated_at": "", "clusters": {
            "verification_path:migrate": {
                "cluster_key": "verification_path:migrate", "operator": "verification_path",
                "signal_count": 1, "strength_sum": 2, "sample_signal_ids": ["s1"],
                "last_seen": "2026-01-01T00:00:00Z", "status": "cooldown", "ready_reason": "",
                "cooldown_until": "2099-01-01T00:00:00Z", "cooldown_signal_remaining": 0,
            }
        },
    }
    (data / "cluster-state.json").write_text(json.dumps(cluster_state), encoding="utf-8")
    (data / "crystallized-operators.jsonl").write_text(json.dumps({"id": "verification_path"}) + "\n", encoding="utf-8")
    return args


def test_schema_migration_is_clean_and_idempotent() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        args = write_old_local_runtime(root)
        assert jinhua.migrate_local_runtime(args) is True
        data = root / ".jinhua" / "data"
        assert not (data / "crystallized-operators.jsonl").exists()
        signal = jinhua.read_jsonl(data / "signals.jsonl")[0]
        assert signal["status"] == "active"
        assert "confidence" not in signal
        proposal = jinhua.read_jsonl(data / "proposals.jsonl")[0]
        assert proposal["placement"] == "skill_patch"
        assert "decision" not in proposal
        adopted = jinhua.read_jsonl(data / "adopted-edits.jsonl")[0]
        assert adopted["applied_target"] == "C:/skills/example/SKILL.md"
        assert adopted["placement"] == "skill_patch"
        assert "applied_path" not in adopted
        rejected = jinhua.read_jsonl(data / "rejected-proposals.jsonl")[0]
        assert "cooldown_until" not in rejected
        assert rejected["cooldown_signal_remaining"] == 5
        state = json.loads((data / "evolution-state.json").read_text(encoding="utf-8"))
        clusters = json.loads((data / "cluster-state.json").read_text(encoding="utf-8"))
        assert state["schema_version"] == "3.0"
        assert clusters["schema_version"] == "3.0"
        assert clusters["clusters"]["verification_path:migrate"]["cooldown_signal_remaining"] == 5

        before = {path.name: path.read_bytes() for path in data.iterdir() if path.is_file()}
        assert jinhua.migrate_local_runtime(args) is False
        after = {path.name: path.read_bytes() for path in data.iterdir() if path.is_file()}
        assert before == after

        global_root = root / "old-global"
        global_root.mkdir()
        global_signal = {
            "id": "gs1", "timestamp": "2026-01-01T00:00:00Z", "project_hash": "hash1",
            "source_signal_id": "s1", "source_timestamp": "2026-01-01T00:00:00Z", "dedupe_key": "hash1:s1",
            "method_fingerprint": "fp1", "method_key": "verification_path:migrate", "operator": "verification_path",
            "local_cluster_key": "verification_path:migrate", "summary": "summary", "context": "context",
            "source_type": "user_correction", "strength": 2, "status": "compacted", "confidence": 0.8,
        }
        (global_root / "global-signals.jsonl").write_text(json.dumps(global_signal) + "\n", encoding="utf-8")
        global_proposal = {
            "id": "gp1", "timestamp": "2026-01-01T00:00:00Z", "method_fingerprint": "fp1",
            "method_key": "verification_path:migrate", "operator": "verification_path",
            "decision": "experimental_operator", "trigger": "old trigger", "evidence_global_signal_ids": ["gs1"],
            "target": "C:/skills/global/SKILL.md", "patch": "old patch", "risk": "old risk", "status": "applied",
            "applied_path": "C:/skills/global/SKILL.md", "write_status": "written",
        }
        (global_root / "global-proposals.jsonl").write_text(json.dumps(global_proposal) + "\n", encoding="utf-8")
        global_adopted = {
            "id": "ga1", "timestamp": "2026-01-01T00:00:00Z", "proposal_id": "gp1",
            "target_skill": "fallback", "applied_path": "C:/skills/global/SKILL.md", "write_status": "written",
            "decision": "experimental_operator", "edit_summary": "old global summary",
        }
        (global_root / "adopted-global-edits.jsonl").write_text(json.dumps(global_adopted) + "\n", encoding="utf-8")
        global_rejected = {
            "id": "gr1", "timestamp": "2026-01-01T00:00:00Z", "proposal_id": "gp1",
            "method_fingerprint": "fp1", "reason": "old reason", "cooldown_until": "2099-01-01T00:00:00Z",
            "cooldown_signal_remaining": 0,
        }
        (global_root / "rejected-global-proposals.jsonl").write_text(json.dumps(global_rejected) + "\n", encoding="utf-8")
        (global_root / "global-state.json").write_text(json.dumps({"schema_version": "1.0"}), encoding="utf-8")
        (global_root / "project-index.json").write_text(
            json.dumps({
                "schema_version": "1.0", "projects": {
                    "hash1": {
                        "project_hash": "hash1", "identity_source": "explicit", "first_seen": "2026-01-01T00:00:00Z",
                        "last_seen": "2026-01-01T00:00:00Z", "imported_signal_count": 1, "last_scan_signal_count": 1,
                    }
                }, "updated_at": "",
            }),
            encoding="utf-8",
        )
        (global_root / "global-clusters.json").write_text(
            json.dumps({
                "schema_version": "1.0", "clusters": {
                    "fp1": {
                        "method_fingerprint": "fp1", "method_key": "verification_path:migrate",
                        "operator": "verification_path", "evidence_count": 1, "strength_sum": 2,
                        "project_hashes": ["hash1"], "sample_global_signal_ids": ["gs1"],
                        "summary_samples": ["summary"], "method_signature_samples": [], "source_type_counts": {"user_correction": 1},
                        "user_correction_count": 1, "high_strength_count": 0, "last_seen": "2026-01-01T00:00:00Z",
                        "status": "cooldown", "ready_reason": "", "cooldown_until": "2099-01-01T00:00:00Z",
                        "cooldown_signal_remaining": 0,
                    }
                }, "updated_at": "",
            }),
            encoding="utf-8",
        )
        global_args = args_for(root, global_root)
        assert jinhua.migrate_global_runtime(global_args) is True
        assert json.loads((global_root / "global-state.json").read_text(encoding="utf-8"))["schema_version"] == "2.0"
        assert json.loads((global_root / "global-clusters.json").read_text(encoding="utf-8"))["schema_version"] == "2.0"
        assert json.loads((global_root / "project-index.json").read_text(encoding="utf-8"))["schema_version"] == "2.0"
        assert "confidence" not in jinhua.read_jsonl(global_root / "global-signals.jsonl")[0]
        assert "decision" not in jinhua.read_jsonl(global_root / "global-proposals.jsonl")[0]
        assert jinhua.read_jsonl(global_root / "adopted-global-edits.jsonl")[0]["applied_target"] == "C:/skills/global/SKILL.md"
        assert jinhua.read_jsonl(global_root / "rejected-global-proposals.jsonl")[0]["cooldown_signal_remaining"] == 5
        assert jinhua.migrate_global_runtime(global_args) is False
        run_cli(root, "validate", global_root=global_root)


def test_malformed_migration_does_not_rewrite_files() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        args = write_old_local_runtime(root, malformed=True)
        data = root / ".jinhua" / "data"
        before = {path.name: path.read_bytes() for path in data.iterdir() if path.is_file()}
        try:
            jinhua.migrate_local_runtime(args)
        except ValueError:
            pass
        else:
            raise AssertionError("Malformed migration should fail")
        after = {path.name: path.read_bytes() for path in data.iterdir() if path.is_file()}
        assert before == after


def test_removed_public_interfaces_are_absent() -> None:
    help_text = run_cli(Path.cwd(), "--help").stdout
    for command in ["wake-check", "hook-user-prompt-submit", "parse-output-state", "compact", "global-merge-suggestions"]:
        assert command not in help_text
    for option in [
        "--decision",
        "--confidence",
        "--force",
        "--target-skill-path",
        "--insert-after",
        "--cooldown-days",
        "--cooldown-signals",
    ]:
        assert option not in help_text
    apply_help = run_cli(Path.cwd(), "apply-proposal", "--help").stdout
    global_apply_help = run_cli(Path.cwd(), "global-apply", "--help").stdout
    for option in ["--patch", "--target-skill-path", "--insert-after", "--force"]:
        assert option not in apply_help
        assert option not in global_apply_help


if __name__ == "__main__":
    test_initialization_and_local_thresholds()
    test_complete_proposal_apply_revision_and_cooldown()
    test_global_thresholds_identity_and_dedupe()
    test_schema_migration_is_clean_and_idempotent()
    test_malformed_migration_does_not_rewrite_files()
    test_removed_public_interfaces_are_absent()
    print("core-loop tests passed")
