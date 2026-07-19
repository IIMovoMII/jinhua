#!/usr/bin/env python3
"""Local ledger CLI for jinhua.

The CLI is platform-neutral and uses only Python's standard library. It does
not perform LLM-level judgment. It stores signals, maintains lightweight
clusters, emits proposal skeletons, and records user-gated outcomes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


JSONL_FILES = [
    "signals.jsonl",
    "proposals.jsonl",
    "adopted-edits.jsonl",
    "rejected-proposals.jsonl",
]

JSON_FILES = ["cluster-state.json", "evolution-state.json"]

GLOBAL_JSONL_FILES = [
    "global-signals.jsonl",
    "global-proposals.jsonl",
    "adopted-global-edits.jsonl",
    "rejected-global-proposals.jsonl",
]

GLOBAL_JSON_FILES = ["global-clusters.json", "global-state.json", "project-index.json"]

CORE_OPERATOR_IDS = [
    "problem_representation",
    "domain_knowledge_access",
    "constraint_recognition",
    "candidate_competition",
    "counterfactual_check",
    "verification_path",
    "compression",
    "skill_merge_suggestion",
]

VALID_OPERATOR_IDS = CORE_OPERATOR_IDS + ["other"]

OPERATOR_ALIASES = {
    "problem-representation": "problem_representation",
    "domain-knowledge-access": "domain_knowledge_access",
    "constraint-recognition": "constraint_recognition",
    "candidate-competition": "candidate_competition",
    "counterfactual-check": "counterfactual_check",
    "verification-path": "verification_path",
    "skill-merge-suggestion": "skill_merge_suggestion",
}

SOURCE_TYPES = [
    "user_prompt",
    "user_correction",
    "success_trace",
    "failure_trace",
    "repeated_pattern",
    "skill_update_signal",
    "self_observation",
]

SIGNAL_STATUSES = {"active"}
CLUSTER_STATUSES = {"active", "ready", "proposed", "adopted", "cooldown"}
PROPOSAL_STATUSES = {"pending_user_gate", "applied", "rejected", "needs_revision"}
PROPOSAL_PLACEMENTS = {
    "project_rule",
    "skill_patch",
    "personal_global_skill",
}
GLOBAL_PROPOSAL_PLACEMENTS = {"skill_patch", "personal_global_skill"}
PLACEMENT_USER_GATE = (
    "项目规则(project_rule) / 增强已有 Skill(skill_patch) / "
    "个人全局 Skill(personal_global_skill) / 拒绝(No) / 修订(Revision)"
)
GLOBAL_USER_GATE = (
    "增强已有 Skill(skill_patch) / 个人全局 Skill(personal_global_skill) / "
    "拒绝(No) / 修订(Revision)"
)
SIGNAL_COUNT_THRESHOLD = 3
SIGNAL_STRENGTH_THRESHOLD = 5
COOLDOWN_SIGNAL_LIMIT = 5
GLOBAL_PROJECT_THRESHOLD = 3
GLOBAL_EVIDENCE_THRESHOLD = 5
GLOBAL_STRENGTH_THRESHOLD = 7
GLOBAL_FAST_PROJECT_THRESHOLD = 2
GLOBAL_FAST_STRENGTH_THRESHOLD = 6
DEFAULT_RUNTIME_DIR_NAME = ".jinhua"
HOOK_PROJECT_PATH_KEYS = (
    "cwd",
    "project_root",
    "projectRoot",
    "project_dir",
    "projectDir",
    "working_directory",
    "workingDirectory",
    "current_working_directory",
    "currentWorkingDirectory",
    "workspace_root",
    "workspaceRoot",
)
HOOK_METADATA_PARENT_PATHS = ((), ("event",), ("event", "context"), ("context",))
HOOK_TOOL_PARENT_PATHS = ((), ("event",))
HOOK_PROMPT_PARENT_PATHS = ((), ("event",), ("input",), ("payload",))
HOOK_SESSION_ID_KEYS = (
    "session_id",
    "sessionId",
    "conversation_id",
    "conversationId",
    "thread_id",
    "threadId",
)
HOOK_TURN_ID_KEYS = (
    "turn_id",
    "turnId",
    "prompt_id",
    "promptId",
    "message_id",
    "messageId",
    "request_id",
    "requestId",
)
HOOK_SHELL_TOOL_NAMES = frozenset(
    {
        "bash",
        "shell",
        "shell_command",
        "exec_command",
        "powershell",
        "pwsh",
        "cmd",
        "terminal",
    }
)
JINHUA_GUARDED_COMMANDS = (
    "log-signal",
    "global-propose",
    "global-cycle",
    "propose",
    "cycle",
    "apply-proposal",
    "global-apply",
    "reject-proposal",
    "global-reject",
)
HOOK_PROJECT_ENV_KEYS = (
    "JINHUA_PROJECT_ROOT",
    "CODEX_PROJECT_ROOT",
    "CODEX_PROJECT_DIR",
    "CLAUDE_PROJECT_DIR",
    "PROJECT_DIR",
    "CURRENT_WORKING_DIRECTORY",
    "INIT_CWD",
    "PWD",
)
STATUS_LABELS = {
    "runtime": "运行态",
    "global_runtime": "全局运行态",
    "signals": "信号",
    "clusters": "聚类",
    "ready": "就绪",
    "pending_gates": "待确认门",
    "global": "全局",
    "imported": "已导入",
    "projects": "项目",
    "global_signals": "全局信号",
    "global_clusters": "全局聚类",
    "active": "活跃",
    "proposed": "已提案",
    "cooldown": "冷却",
    "proposals": "提案",
    "global_proposals": "全局提案",
    "pending_user_gate": "等待用户确认",
    "needs_revision": "需要修订",
    "adopted_skill_edits": "已采纳 Skill 修改",
    "adopted_global_edits": "已采纳全局修改",
    "rejected_proposals": "已拒绝提案",
    "rejected_global_proposals": "已拒绝全局提案",
    "last_proposal_id": "最后提案 ID",
    "created": "已创建",
    "ready_state": "就绪",
}

DEFAULT_PERIODIC_STOP_INTERVAL = 8

CORRECTION_RULES = [
    ("direct_denial", 3, [
        r"你(?:又)?错了",
        r"这(?:个)?不对",
        r"完全不对",
        r"不是这样",
        r"这不是我要的",
        r"不是这个",
        r"不符合(?:我的)?要求",
        r"你(?:又)?搞错了",
        r"\bwrong\b",
        r"\bincorrect\b",
        r"\bnot this\b",
    ]),
    ("misunderstanding", 3, [
        r"你(?:没|沒有|没有)(?:懂|看懂|明白|理解)",
        r"你理解错了",
        r"你搞错(?:重点)?了",
        r"你(?:又)?跑偏了",
        r"这不是(?:我)?(?:的)?意思",
        r"我(?:说的)?不是这个",
        r"我说的不是",
        r"你没抓住重点",
        r"重点不是",
        r"\bnot what i meant\b",
        r"\byou misunderstood\b",
        r"\bthat's not what i asked\b",
        r"\byou missed the point\b",
    ]),
    ("missed_requirement", 3, [
        r"重新看我的要求",
        r"重新读(?:一下)?我的要求",
        r"再读(?:一遍|一下)",
        r"我(?:已经|已經|前面|刚才|剛才)说(?:过|了)",
        r"按我(?:刚才|剛才|前面)?说的来",
        r"你(?:又)?没按.*说的",
        r"你(?:又)?漏(?:看|掉|了)",
        r"本来(?:就)?应该",
        r"本来就该",
        r"不是早就说了",
        r"别自己发挥",
        r"\bread again\b",
        r"\bas i said\b",
        r"\bi already said\b",
    ]),
    ("output_format_correction", 2, [
        r"不要写代码",
        r"我要的是.*不是.*代码",
        r"我要的是方案",
        r"我要中文|别用英文|不要.*英文",
        r"(?:你|刚才|剛才|前面|我说的).*(?:不要列表|不要这么啰嗦|废话)",
        r"不要讲最小方案|直接给最佳方案",
        r"我问的不是这个",
        r"不要只(?:解释|說明|说明)",
        r"直接(?:改|做|执行|生成)",
        r"\bdon't write code\b",
        r"\bi asked for.*not code\b",
    ]),
    ("scope_boundary", 3, [
        r"不要(?:改|动|動).*(?:skill|内核|內核|核心流程|现有逻辑|現有邏輯)",
        r"不是让你改.*(?:skill|内核|內核|核心流程)",
        r"只改.*(?:触发|觸發|唤醒|喚醒|第一道|hook)",
        r"你改错地方了",
        r"不要重构|不要重構",
        r"你把范围扩大了",
        r"别(?:扩大|擴大)范围",
        r"\bthat's not the scope\b",
        r"\bdon't change.*core\b",
    ]),
    ("tool_skill_procedure_miss", 3, [
        r"为什么.*(没|沒有|没有|未).*(触发|调用|唤醒|启动|啟動|执行|執行|判断|檢查|检查)",
        r"(应该|應該|本该|本應|需要).*(触发|调用|唤醒|启动|啟動|执行|執行|判断).*(skill|技能|工具|流程|jinhua|hook)",
        r"(jinhua|skill|hook|工具|流程).*(没|沒有|没有|未).*(触发|调用|唤醒|启动|啟動|执行|執行|判断)",
        r"agent为什么没(?:有)?(?:自动)?判断",
        r"本来应该触发",
        r"应该(?:自动)?判断",
        r"应该(?:直接|自动)?.*(?:生成提案|创建提案|propose)",
        r"\bshould have\b.*\b(triggered|called|run|loaded|selected|checked)\b",
        r"\bwhy.*(?:didn't|not).*\b(trigger|call|run|load|select|check)\b",
    ]),
    ("future_rule_request", 3, [
        r"(以后|下次|今后|往后).*(应该|應該|必须|一定|先|记住|沉淀|写进)",
        r"(记住|記住|沉淀|沉澱|写进|寫進|保存).*(规则|規則|skill|经验|經驗|流程|方法)",
        r"把.*(?:沉淀|沉澱|写进|寫進|保存).*(skill|规则|規則|经验|經驗)",
        r"\b(from now on|next time|going forward)\b.*\b(should|must|always|never)\b",
        r"\b(remember|crystallize|preserve|save)\b.*\b(skill|rule|method|workflow)\b",
    ]),
    ("frustration", 3, [
        r"操你妈|傻逼|离谱|胡说|瞎说|扯淡|别扯|乱讲",
        r"你到底有没有看",
        r"怎么又这样",
        r"又来了",
    ]),
]

MEDIUM_CORRECTION_PATTERNS = [
    r"不是",
    r"不对|不對",
    r"错了|錯了",
    r"重新说",
    r"看清楚",
    r"我说的是",
    r"别这样",
    r"不要",
    r"只要",
    r"\bno\b",
    r"\bnot this\b",
    r"\bdon't do that\b",
    r"\bi said\b",
    r"\bas i said\b",
]

CORRECTION_CONTEXT_PATTERNS = [
    r"你",
    r"刚才|剛才|前面|上一轮|上一輪",
    r"我说的|我已(?:经|經)说过",
    r"不是这个",
    r"改错|跑偏",
    r"workflow|verification|reasoning|scope|skill|tool",
]

WEAK_CLARIFICATION_PATTERNS = [
    r"再详细一点",
    r"换个说法",
    r"继续",
    r"举例",
    r"能不能更短",
    r"能不能更正式",
    r"帮我润色",
    r"\bmore detail\b",
    r"\bcontinue\b",
    r"\bgive examples?\b",
    r"\bshorter\b",
]

GENERIC_PROJECT_RULE_FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    ".github/copilot-instructions.md",
    "copilot-instructions.md",
    "README.md",
    "docs/AI.md",
    "docs/AGENTS.md",
]

AGENT_PROFILE_RULE_FILES = {
    "codex": ["AGENTS.md"],
    "claude": ["CLAUDE.md"],
    "copilot": [".github/copilot-instructions.md", "copilot-instructions.md"],
    "trae": ["AGENTS.md", ".trae/rules.md", "README.md"],
    "hermes": ["AGENTS.md", "HERMES.md", "README.md"],
    "openclaw": ["AGENTS.md", "OPENCLAW.md", "README.md"],
    "workbuddy": ["AGENTS.md", "WORKBUDDY.md", "README.md"],
    "generic": GENERIC_PROJECT_RULE_FILES,
    "custom": GENERIC_PROJECT_RULE_FILES,
    "unknown": GENERIC_PROJECT_RULE_FILES,
}

AGENT_PROFILE_ALIASES = {
    "claude-code": "claude",
    "claudecode": "claude",
    "github-copilot": "copilot",
    "githubcopilot": "copilot",
}

SIGNAL_CARD_FIELDS = [
    "trigger",
    "action",
    "transfer_conditions",
    "negative_cases",
    "verification_path",
]

METHOD_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "before", "by", "can", "do", "for",
    "from", "has", "have", "if", "in", "into", "is", "it", "of", "on", "or", "that",
    "the", "then", "this", "to", "use", "when", "with", "within", "without", "user",
    "users", "model", "skill", "skills", "project", "projects", "task", "tasks",
    "action", "trigger", "transfer_conditions", "negative_cases", "verification_path",
    "method_signature", "summary", "context", "source_type",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def make_id(prefix: str) -> str:
    return f"{prefix}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def codex_home() -> Path:
    explicit = os.environ.get("CODEX_HOME", "").strip()
    if explicit:
        return Path(explicit).expanduser().resolve()
    return Path.home() / ".codex"


def project_root(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "project_root", ".")).resolve()


def path_is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def normalize_agent_profile(value: str) -> str:
    profile = re.sub(r"[^a-z0-9_-]+", "-", str(value or "").strip().lower()).strip("-_")
    if not profile:
        return "generic"
    return AGENT_PROFILE_ALIASES.get(profile, profile)


def agent_profile(args: argparse.Namespace | None) -> str:
    explicit = getattr(args, "agent_profile", "") if args is not None else ""
    profile = explicit or os.environ.get("JINHUA_AGENT_PROFILE", "")
    return normalize_agent_profile(profile)


def project_identity_material(args: argparse.Namespace) -> tuple[str, str]:
    root = project_root(args)
    explicit = getattr(args, "project_id", "").strip()
    if explicit:
        return f"explicit:{explicit}", "explicit"
    env_project_id = os.environ.get("JINHUA_PROJECT_ID", "").strip()
    if env_project_id:
        return f"env:{env_project_id}", "env"
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        remote = result.stdout.strip()
        if result.returncode == 0 and remote:
            return f"git:{remote}", "git_remote"
    except (OSError, subprocess.SubprocessError):
        pass
    return f"path:{root}", "path"


def project_signature(args: argparse.Namespace) -> str:
    material, _ = project_identity_material(args)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def method_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def runtime_root(args: argparse.Namespace) -> Path:
    explicit = getattr(args, "runtime_dir", "")
    if explicit:
        return Path(explicit).resolve()
    return project_root(args) / DEFAULT_RUNTIME_DIR_NAME


def data_dir(args: argparse.Namespace) -> Path:
    return runtime_root(args) / "data"


def runtime_meta_dir(args: argparse.Namespace) -> Path:
    return runtime_root(args) / "runtime"


def invocation_guard_path(args: argparse.Namespace) -> Path:
    return runtime_meta_dir(args) / "invocation-guard.json"


def global_runtime_root(args: argparse.Namespace | None = None) -> Path:
    explicit = getattr(args, "global_runtime_dir", "") if args is not None else ""
    if explicit:
        return Path(explicit).resolve()
    return skill_root() / "global-data"


def global_data_dir(args: argparse.Namespace | None = None) -> Path:
    return global_runtime_root(args)


def state_path(args: argparse.Namespace) -> Path:
    return data_dir(args) / "evolution-state.json"


def cluster_path(args: argparse.Namespace) -> Path:
    return data_dir(args) / "cluster-state.json"


def global_state_path(args: argparse.Namespace | None = None) -> Path:
    return global_data_dir(args) / "global-state.json"


def global_cluster_path(args: argparse.Namespace | None = None) -> Path:
    return global_data_dir(args) / "global-clusters.json"


def project_index_path(args: argparse.Namespace | None = None) -> Path:
    return global_data_dir(args) / "project-index.json"


def default_state() -> dict:
    return {
        "schema_version": "3.0",
        "last_proposal_id": "",
        "total_signal_count": 0,
        "adopted_edit_count": 0,
        "rejected_proposal_count": 0,
        "updated_at": "",
    }


def default_cluster_state() -> dict:
    return {"schema_version": "3.0", "clusters": {}, "updated_at": ""}


def default_global_state() -> dict:
    return {
        "schema_version": "2.0",
        "last_scan_at": "",
        "last_scan_project_count": 0,
        "last_scan_signal_count": 0,
        "last_ready_cluster_count": 0,
        "last_proposal_id": "",
        "updated_at": "",
    }


def default_global_cluster_state() -> dict:
    return {"schema_version": "2.0", "clusters": {}, "updated_at": ""}


def default_project_index() -> dict:
    return {"schema_version": "2.0", "projects": {}, "updated_at": ""}


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            text = line.strip()
            if not text:
                continue
            try:
                records.append(json.loads(text))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
    return records


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(text, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def write_jsonl(path: Path, records: list[dict]) -> None:
    if records:
        text = "\n".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in records) + "\n"
    else:
        text = ""
    atomic_write_text(path, text)


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def read_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return dict(default)
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    atomic_write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def regex_hits(patterns: list[str], text: str) -> list[str]:
    return [pattern for pattern in patterns if re.search(pattern, text, flags=re.I)]


def correction_evidence(text: str) -> list[dict]:
    evidence = []
    for category, weight, patterns in CORRECTION_RULES:
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.I)
            if match:
                evidence.append({
                    "category": category,
                    "pattern": pattern,
                    "match": match.group(0),
                    "weight": weight,
                    "start": match.start(),
                    "end": match.end(),
                })
    return evidence


def read_state(args: argparse.Namespace) -> dict:
    state = default_state()
    state.update(read_json(state_path(args), default_state()))
    return state


def write_state(args: argparse.Namespace, state: dict) -> None:
    clean_state = default_state()
    for key in clean_state:
        if key in state:
            clean_state[key] = state[key]
    clean_state["schema_version"] = "3.0"
    clean_state["updated_at"] = utc_now()
    write_json(state_path(args), clean_state)


def read_cluster_state(args: argparse.Namespace) -> dict:
    state = default_cluster_state()
    state.update(read_json(cluster_path(args), default_cluster_state()))
    state.setdefault("clusters", {})
    return state


def write_cluster_state(args: argparse.Namespace, state: dict) -> None:
    state["schema_version"] = "3.0"
    state["updated_at"] = utc_now()
    write_json(cluster_path(args), state)


def read_global_state(args: argparse.Namespace | None = None) -> dict:
    state = default_global_state()
    state.update(read_json(global_state_path(args), default_global_state()))
    return state


def write_global_state(state: dict, args: argparse.Namespace | None = None) -> None:
    state["schema_version"] = "2.0"
    state["updated_at"] = utc_now()
    write_json(global_state_path(args), state)


def read_global_clusters(args: argparse.Namespace | None = None) -> dict:
    state = default_global_cluster_state()
    state.update(read_json(global_cluster_path(args), default_global_cluster_state()))
    state.setdefault("clusters", {})
    return state


def write_global_clusters(state: dict, args: argparse.Namespace | None = None) -> None:
    state["schema_version"] = "2.0"
    state["updated_at"] = utc_now()
    write_json(global_cluster_path(args), state)


def read_project_index(args: argparse.Namespace | None = None) -> dict:
    state = default_project_index()
    state.update(read_json(project_index_path(args), default_project_index()))
    state.setdefault("projects", {})
    return state


def write_project_index(state: dict, args: argparse.Namespace | None = None) -> None:
    state["schema_version"] = "2.0"
    state["updated_at"] = utc_now()
    write_json(project_index_path(args), state)


def runtime_exists(args: argparse.Namespace) -> bool:
    return data_dir(args).exists() and state_path(args).exists()


def migrated_proposal_placement(record: dict, global_scope: bool = False) -> str:
    placement = str(record.get("placement") or "").strip()
    allowed = GLOBAL_PROPOSAL_PLACEMENTS if global_scope else PROPOSAL_PLACEMENTS
    if placement in allowed:
        return placement
    target_text = " ".join(
        str(record.get(field) or "")
        for field in ["target", "recommended_skill", "recommended_skill_path"]
    ).lower()
    if "skill.md" in target_text or record.get("recommended_skill_path"):
        return "skill_patch"
    return "personal_global_skill" if global_scope else "project_rule"


def migrated_adopted_record(record: dict, proposals_by_id: dict[str, dict], global_scope: bool = False) -> dict:
    migrated = dict(record)
    proposal = proposals_by_id.get(str(record.get("proposal_id", "")), {})
    applied_target = (
        record.get("applied_target")
        or record.get("applied_path")
        or record.get("target_skill")
        or proposal.get("target")
        or ""
    )
    migrated["applied_target"] = applied_target
    migrated["placement"] = migrated_proposal_placement(
        {**proposal, **migrated, "target": applied_target or proposal.get("target", "")},
        global_scope=global_scope,
    )
    migrated["edit_summary"] = str(record.get("edit_summary") or proposal.get("patch") or "Migrated adopted edit")[:220]
    for field in ["target_skill", "applied_path", "write_status", "decision"]:
        migrated.pop(field, None)
    return migrated


def migrate_local_runtime(args: argparse.Namespace) -> bool:
    if not runtime_exists(args):
        return False
    data = data_dir(args)
    raw_state = read_json(state_path(args), default_state())
    crystallized_path = data / "crystallized-operators.jsonl"
    if raw_state.get("schema_version") == "3.0" and not crystallized_path.exists():
        return False

    signals = read_jsonl(data / "signals.jsonl")
    proposals = read_jsonl(data / "proposals.jsonl")
    adopted = read_jsonl(data / "adopted-edits.jsonl")
    rejected = read_jsonl(data / "rejected-proposals.jsonl")
    if crystallized_path.exists():
        read_jsonl(crystallized_path)
    cluster_state = read_json(cluster_path(args), default_cluster_state())

    migrated_signals = []
    for record in signals:
        item = dict(record)
        item.pop("confidence", None)
        if item.get("status") in {"compacted", "ignored"}:
            item["status"] = "active"
        migrated_signals.append(item)

    migrated_proposals = []
    for record in proposals:
        item = dict(record)
        for field in ["decision", "applied_path", "write_status"]:
            item.pop(field, None)
        item["placement"] = migrated_proposal_placement(item)
        migrated_proposals.append(item)

    proposals_by_id = {str(item.get("id", "")): item for item in migrated_proposals}
    migrated_adopted = [migrated_adopted_record(item, proposals_by_id) for item in adopted]
    migrated_rejected = []
    for record in rejected:
        item = dict(record)
        item.pop("cooldown_until", None)
        if int(item.get("cooldown_signal_remaining", 0) or 0) <= 0:
            item["cooldown_signal_remaining"] = COOLDOWN_SIGNAL_LIMIT
        migrated_rejected.append(item)

    clusters = cluster_state.setdefault("clusters", {})
    for cluster in clusters.values():
        cluster.pop("cooldown_until", None)
        if cluster.get("status") == "cooldown" and int(cluster.get("cooldown_signal_remaining", 0) or 0) <= 0:
            cluster["cooldown_signal_remaining"] = COOLDOWN_SIGNAL_LIMIT
    cluster_state["schema_version"] = "3.0"
    cluster_state["updated_at"] = utc_now()

    clean_state = default_state()
    for key in clean_state:
        if key in raw_state:
            clean_state[key] = raw_state[key]
    clean_state["schema_version"] = "3.0"
    clean_state["updated_at"] = utc_now()

    write_jsonl(data / "signals.jsonl", migrated_signals)
    write_jsonl(data / "proposals.jsonl", migrated_proposals)
    write_jsonl(data / "adopted-edits.jsonl", migrated_adopted)
    write_jsonl(data / "rejected-proposals.jsonl", migrated_rejected)
    write_json(cluster_path(args), cluster_state)
    write_json(state_path(args), clean_state)
    if crystallized_path.exists():
        crystallized_path.unlink()
    return True


def migrate_global_runtime(args: argparse.Namespace | None = None) -> bool:
    if not global_runtime_exists(args):
        return False
    data = global_data_dir(args)
    raw_state = read_json(global_state_path(args), default_global_state())
    if raw_state.get("schema_version") == "2.0":
        return False

    signals = read_jsonl(global_signal_path(args))
    proposals = read_jsonl(global_proposal_path(args))
    adopted = read_jsonl(adopted_global_path(args))
    rejected = read_jsonl(rejected_global_path(args))
    cluster_state = read_json(global_cluster_path(args), default_global_cluster_state())
    project_index = read_json(project_index_path(args), default_project_index())

    migrated_signals = []
    for record in signals:
        item = dict(record)
        item.pop("confidence", None)
        if item.get("status") in {"compacted", "ignored"}:
            item["status"] = "active"
        migrated_signals.append(item)

    migrated_proposals = []
    for record in proposals:
        item = dict(record)
        for field in ["decision", "applied_path", "write_status"]:
            item.pop(field, None)
        item["placement"] = migrated_proposal_placement(item, global_scope=True)
        migrated_proposals.append(item)

    proposals_by_id = {str(item.get("id", "")): item for item in migrated_proposals}
    migrated_adopted = [migrated_adopted_record(item, proposals_by_id, global_scope=True) for item in adopted]
    migrated_rejected = []
    for record in rejected:
        item = dict(record)
        item.pop("cooldown_until", None)
        if int(item.get("cooldown_signal_remaining", 0) or 0) <= 0:
            item["cooldown_signal_remaining"] = COOLDOWN_SIGNAL_LIMIT
        migrated_rejected.append(item)

    clusters = cluster_state.setdefault("clusters", {})
    for cluster in clusters.values():
        cluster.pop("cooldown_until", None)
        if cluster.get("status") == "cooldown" and int(cluster.get("cooldown_signal_remaining", 0) or 0) <= 0:
            cluster["cooldown_signal_remaining"] = COOLDOWN_SIGNAL_LIMIT
    cluster_state["schema_version"] = "2.0"
    cluster_state["updated_at"] = utc_now()
    project_index["schema_version"] = "2.0"
    project_index["updated_at"] = utc_now()

    clean_state = default_global_state()
    for key in clean_state:
        if key in raw_state:
            clean_state[key] = raw_state[key]
    clean_state["schema_version"] = "2.0"
    clean_state["updated_at"] = utc_now()

    write_jsonl(global_signal_path(args), migrated_signals)
    write_jsonl(global_proposal_path(args), migrated_proposals)
    write_jsonl(adopted_global_path(args), migrated_adopted)
    write_jsonl(rejected_global_path(args), migrated_rejected)
    write_json(global_cluster_path(args), cluster_state)
    write_json(project_index_path(args), project_index)
    write_json(global_state_path(args), clean_state)
    return True


def ensure_runtime(args: argparse.Namespace, auto_init: bool = False) -> None:
    if not runtime_exists(args):
        if auto_init:
            initialize_runtime(args, quiet=True)
            return
        raise SystemExit("Runtime directory not initialized. Run: jinhua.py init")
    migrate_local_runtime(args)


def global_runtime_exists(args: argparse.Namespace | None = None) -> bool:
    return global_data_dir(args).exists() and global_state_path(args).exists()


def ensure_global_runtime(args: argparse.Namespace | None = None) -> None:
    data = global_data_dir(args)
    data.mkdir(parents=True, exist_ok=True)
    for filename in GLOBAL_JSONL_FILES:
        path = data / filename
        if not path.exists():
            path.write_text("", encoding="utf-8")
    for filename in GLOBAL_JSON_FILES:
        path = data / filename
        if path.exists():
            continue
        if filename == "global-clusters.json":
            write_json(path, default_global_cluster_state())
        elif filename == "project-index.json":
            write_json(path, default_project_index())
        else:
            write_json(path, default_global_state())
    migrate_global_runtime(args)


def is_skill_source_project(args: argparse.Namespace) -> bool:
    root = project_root(args)
    return root.name.lower() == "jinhua" and (root / "SKILL.md").exists()


def normalize_operator(value: str) -> str:
    normalized = OPERATOR_ALIASES.get(value, value)
    if normalized not in VALID_OPERATOR_IDS:
        valid_list = ", ".join(VALID_OPERATOR_IDS)
        raise SystemExit(f"Invalid --operator: {value!r}\nAllowed values: {valid_list}")
    return normalized


def validate_cluster_key(value: str, operator: str) -> None:
    prefix = f"{operator}:"
    if not value.startswith(prefix) or len(value) <= len(prefix):
        raise SystemExit(f"--cluster-key must use format '{operator}:short_method_slug'")
    slug = value.split(":", 1)[1]
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_-")
    if any(ch not in allowed for ch in slug):
        raise SystemExit("--cluster-key slug may contain only lowercase letters, digits, underscores, and hyphens")


def clamp_strength(value: int) -> int:
    if value < 1 or value > 3:
        raise SystemExit("--strength must be 1, 2, or 3")
    return value


def cooldown_is_active(cluster: dict) -> bool:
    remaining = int(cluster.get("cooldown_signal_remaining", 0) or 0)
    return remaining > 0


def threshold_reason(cluster: dict, immediate: bool = False) -> str:
    if immediate:
        return "immediate trigger requested by model/user"
    count = int(cluster.get("signal_count", 0))
    strength = int(cluster.get("strength_sum", 0))
    if count >= SIGNAL_COUNT_THRESHOLD and strength >= SIGNAL_STRENGTH_THRESHOLD:
        return f"signal_count >= {SIGNAL_COUNT_THRESHOLD} and strength_sum >= {SIGNAL_STRENGTH_THRESHOLD}"
    if count >= SIGNAL_COUNT_THRESHOLD:
        return f"signal_count >= {SIGNAL_COUNT_THRESHOLD}"
    if strength >= SIGNAL_STRENGTH_THRESHOLD:
        return f"strength_sum >= {SIGNAL_STRENGTH_THRESHOLD}"
    return ""


def canonical_operator(value: str) -> str:
    operator = OPERATOR_ALIASES.get(value, value)
    if operator not in VALID_OPERATOR_IDS:
        return "other"
    return operator


def method_words(value: str) -> list[str]:
    text = str(value or "").lower()
    text = re.sub(r"https?://\S+", " url ", text)
    text = re.sub(r"[a-z]:[\\/][^\s]+", " path ", text)
    text = re.sub(r"\b\d+\b", " num ", text)
    words = re.findall(r"[a-z][a-z0-9_]{1,}", text)
    return [word for word in words if word not in METHOD_STOPWORDS]


def method_slug_from_parts(parts: list[str], fallback: str = "method") -> str:
    words: list[str] = []
    seen: set[str] = set()
    for part in parts:
        for word in method_words(part):
            if word in seen:
                continue
            seen.add(word)
            words.append(word)
            if len(words) >= 12:
                break
        if len(words) >= 12:
            break
    slug = "_".join(words).strip("_")
    return slug or fallback


def signal_card_parts(signal: dict) -> list[str]:
    return [
        str(signal.get("action") or ""),
        str(signal.get("trigger") or ""),
        str(signal.get("transfer_conditions") or ""),
    ]


def method_signature(signal: dict) -> str:
    parts = []
    for key in ["action", "trigger", "transfer_conditions"]:
        value = compact_text(signal.get(key, ""), limit=120)
        if value:
            parts.append(f"{key}={value}")
    return " | ".join(parts)


def proposal_query_parts(cluster: dict, records: list[dict]) -> list[str]:
    parts = [
        str(cluster.get("cluster_key") or ""),
        str(cluster.get("method_key") or ""),
        str(cluster.get("operator") or ""),
        str(cluster.get("ready_reason") or ""),
    ]
    parts.extend(str(item) for item in cluster.get("summary_samples", []))
    parts.extend(str(item) for item in cluster.get("method_signature_samples", []))
    for record in records:
        for field in [
            "summary",
            "context",
            "trigger",
            "action",
            "transfer_conditions",
            "negative_cases",
            "verification_path",
            "risk",
        ]:
            parts.append(str(record.get(field) or ""))
    return parts


def proposal_positive_parts(cluster: dict, records: list[dict]) -> list[str]:
    parts = [
        str(cluster.get("cluster_key") or ""),
        str(cluster.get("method_key") or ""),
        str(cluster.get("operator") or ""),
        str(cluster.get("ready_reason") or ""),
    ]
    parts.extend(str(item) for item in cluster.get("summary_samples", []))
    parts.extend(str(item) for item in cluster.get("method_signature_samples", []))
    for record in records:
        for field in [
            "summary",
            "context",
            "trigger",
            "action",
            "transfer_conditions",
            "verification_path",
        ]:
            parts.append(str(record.get(field) or ""))
    return parts


def parse_skill_frontmatter(text: str, fallback_name: str) -> tuple[str, str]:
    name = fallback_name
    description = ""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for raw_line in text[3:end].splitlines():
                line = raw_line.strip()
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                value = value.strip().strip("\"'")
                if key.strip() == "name" and value:
                    name = value
                elif key.strip() == "description" and value:
                    description = value
    return name, description


def read_skill_candidate(skill_md: Path, source: str) -> dict | None:
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    name, description = parse_skill_frontmatter(text[:8000], skill_md.parent.name)
    body_head = re.sub(r"---.*?---", " ", text[:6000], count=1, flags=re.S)
    search_text = " ".join([name, skill_md.parent.name, description, body_head])
    return {
        "name": name,
        "path": str(skill_md.resolve()),
        "source": source,
        "description": compact_text(description, limit=240),
        "search_text": search_text,
    }


def discover_local_skills(args: argparse.Namespace | None = None) -> list[dict]:
    candidates: list[dict] = []
    seen: set[str] = set()

    paths: list[tuple[Path, str]] = []
    if args is not None:
        project_skill = project_root(args) / "SKILL.md"
        if project_skill.exists():
            paths.append((project_skill, "current_project"))

    installed_dir = codex_home() / "skills"
    if installed_dir.exists():
        try:
            for child in sorted(installed_dir.iterdir(), key=lambda p: p.name.lower()):
                if not child.is_dir() or child.name.startswith("."):
                    continue
                skill_md = child / "SKILL.md"
                if skill_md.exists():
                    paths.append((skill_md, "codex_home"))
        except OSError:
            pass

    current_skill = skill_root() / "SKILL.md"
    if current_skill.exists():
        paths.append((current_skill, "jinhua_runtime"))

    for skill_md, source in paths:
        resolved = str(skill_md.resolve()).lower()
        if resolved in seen:
            continue
        seen.add(resolved)
        candidate = read_skill_candidate(skill_md, source)
        if candidate:
            candidates.append(candidate)
    return candidates


def score_skill_candidate(candidate: dict, query_text: str, query_words: set[str]) -> tuple[int, list[str]]:
    candidate_text = str(candidate.get("search_text") or "").lower()
    candidate_words = set(method_words(candidate_text))
    matches = sorted(query_words & candidate_words)
    score = len(matches)
    name = str(candidate.get("name") or "").lower()
    folder = Path(str(candidate.get("path") or "")).parent.name.lower()
    for token in [name, folder, name.replace("-", " "), folder.replace("-", " ")]:
        if token and token in query_text:
            score += 8
    for word in matches:
        if word in name or word in folder:
            score += 2
    description = str(candidate.get("description") or "").lower()
    for word in matches:
        if word in description:
            score += 1
    if candidate.get("source") == "current_project":
        for phrase in ["this skill", "current skill", "self improvement", "skill evolution", "jinhua"]:
            if phrase in query_text:
                score += 3
                break
    return score, matches[:8]


def recommend_local_skill(args: argparse.Namespace | None, cluster: dict, records: list[dict]) -> dict:
    if args is None:
        return {}
    query_text = " ".join(proposal_query_parts(cluster, records)).lower()
    query_words = set(method_words(query_text))
    if not query_words:
        return {}
    scored = []
    for candidate in discover_local_skills(args):
        score, matches = score_skill_candidate(candidate, query_text, query_words)
        if score <= 0:
            continue
        scored.append({
            "name": candidate["name"],
            "path": candidate["path"],
            "source": candidate["source"],
            "score": score,
            "matched_terms": matches,
        })
    scored.sort(key=lambda item: (item["score"], item["source"] == "current_project"), reverse=True)
    best = scored[0] if scored else {}
    if not best or int(best.get("score", 0)) < 3:
        return {}
    best["alternatives"] = scored[1:4]
    terms = ", ".join(best.get("matched_terms", [])[:5]) or "metadata overlap"
    best["reason"] = f"best local Skill match by name/description/rule overlap: {terms}"
    return best


def unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = item.replace("\\", "/").strip("/")
        key = normalized.lower()
        if not normalized or key in seen:
            continue
        seen.add(key)
        result.append(normalized)
    return result


def project_rule_candidates_for_profile(profile: str) -> list[str]:
    candidates = AGENT_PROFILE_RULE_FILES.get(profile, []) + GENERIC_PROJECT_RULE_FILES
    return unique_preserve_order(candidates)


def recommend_project_rule_file(args: argparse.Namespace | None) -> dict:
    if args is None:
        return {}
    root = project_root(args)
    profile = agent_profile(args)
    candidates = project_rule_candidates_for_profile(profile)
    existing = [item for item in candidates if (root / item).is_file()]
    recommended = existing[0] if existing else (candidates[0] if candidates else "AGENTS.md")
    reason = "existing project rule file" if existing else "first candidate for this agent profile; do not create without user confirmation"
    if profile not in AGENT_PROFILE_RULE_FILES:
        reason = f"unknown agent profile; {reason}"
    return {
        "agent_profile": profile,
        "recommended_project_rule_file": recommended,
        "recommended_project_rule_path": str((root / recommended).resolve()),
        "recommended_project_rule_reason": reason,
        "project_rule_candidates": candidates,
        "project_rule_existing_files": existing,
    }


def placement_text(cluster: dict, records: list[dict]) -> str:
    return " ".join(proposal_positive_parts(cluster, records)).lower()


def looks_like_skill_patch(text: str, recommendation: dict) -> bool:
    phrases = [
        "existing skill",
        "local skill",
        "target skill",
        "skill rule",
        "skill.md",
        "references/",
        "write into a skill",
        "enhance skill",
        "update skill",
        "patch skill",
        "skill update",
        "skill evolution",
    ]
    if any(phrase in text for phrase in phrases):
        return True
    return bool(recommendation and int(recommendation.get("score", 0)) >= 6 and "skill" in text)


def looks_like_personal_global_skill(text: str) -> bool:
    phrases = [
        "personal global skill",
        "global skill",
        "all projects",
        "across all projects",
        "every project",
        "new skill",
        "standalone skill",
        "independent workflow",
    ]
    return any(phrase in text for phrase in phrases)


def placement_target_hint(placement: str, recommendation: dict, project_rule: dict | None = None) -> str:
    if placement == "skill_patch":
        if recommendation:
            return f"{recommendation.get('name', '')}/SKILL.md ({recommendation.get('path', '')})"
        return "[specific existing local Skill / SKILL.md or references/*.md]"
    if placement == "personal_global_skill":
        return "[~/.codex/skills/<new-skill-name>/SKILL.md]"
    if project_rule and project_rule.get("recommended_project_rule_file"):
        return project_rule.get("recommended_project_rule_file", "")
    return "[project rule location, project docs, or recorded local rule]"


def normalize_placement(value: str, default: str = "") -> str:
    placement = str(value or "").strip()
    if not placement:
        return default
    if placement not in PROPOSAL_PLACEMENTS:
        raise SystemExit(
            f"Invalid placement: {placement!r}. Expected one of: {', '.join(sorted(PROPOSAL_PLACEMENTS))}"
        )
    return placement


def require_concrete_text(value: str, option_name: str) -> str:
    text = str(value or "").strip()
    if not text or text.startswith("["):
        raise SystemExit(f"{option_name} must contain concrete content, not a placeholder.")
    return text


def require_markdown_patch(value: str) -> str:
    patch = require_concrete_text(value, "--patch")
    if not re.search(r"(?m)^#{1,6}\s+\S", patch):
        raise SystemExit("--patch must be a complete Markdown block with a heading.")
    return patch


def infer_local_placement(args: argparse.Namespace | None, cluster: dict, records: list[dict]) -> dict:
    recommendation = recommend_local_skill(args, cluster, records)
    text = placement_text(cluster, records)
    project_rule = recommend_project_rule_file(args)
    if looks_like_personal_global_skill(text):
        placement = "personal_global_skill"
        reason = "the signal explicitly asks for all-project or standalone Skill use"
    elif looks_like_skill_patch(text, recommendation):
        placement = "skill_patch"
        if recommendation:
            reason = f"an existing local Skill is the closest owner: {recommendation.get('name', '')}"
        else:
            reason = "the signal is about changing an existing Skill rule"
    else:
        placement = "project_rule"
        reason = "same-project repetition shows current project need, without enough cross-project evidence"
    owner = recommendation if placement == "skill_patch" else {}
    project_rule_fields = project_rule if placement == "project_rule" else {}
    return {
        "placement_hint": placement,
        "placement_reason": reason,
        "recommended_skill": owner.get("name", ""),
        "recommended_skill_path": owner.get("path", ""),
        "recommended_skill_reason": owner.get("reason", ""),
        "agent_profile": project_rule_fields.get("agent_profile", ""),
        "recommended_project_rule_file": project_rule_fields.get("recommended_project_rule_file", ""),
        "recommended_project_rule_path": project_rule_fields.get("recommended_project_rule_path", ""),
        "recommended_project_rule_reason": project_rule_fields.get("recommended_project_rule_reason", ""),
        "project_rule_candidates": project_rule_fields.get("project_rule_candidates", []),
        "project_rule_existing_files": project_rule_fields.get("project_rule_existing_files", []),
        "skill_candidates": [
            {
                "name": item.get("name", ""),
                "path": item.get("path", ""),
                "score": item.get("score", 0),
            }
            for item in ([owner] + owner.get("alternatives", []) if owner else [])
        ],
        "target_hint": placement_target_hint(placement, owner, project_rule_fields),
    }


def infer_global_placement(args: argparse.Namespace | None, cluster: dict, records: list[dict]) -> dict:
    recommendation = recommend_local_skill(args, cluster, records)
    text = placement_text(cluster, records)
    if recommendation and int(recommendation.get("score", 0)) >= 3:
        placement = "skill_patch"
        reason = f"cross-project evidence fits an existing local Skill: {recommendation.get('name', '')}"
    elif looks_like_skill_patch(text, recommendation):
        placement = "skill_patch"
        reason = "cross-project evidence is framed as an existing Skill enhancement"
    else:
        placement = "personal_global_skill"
        reason = "cross-project evidence is transferable and no existing local Skill owns it clearly"
    owner = recommendation if placement == "skill_patch" else {}
    return {
        "placement_hint": placement,
        "placement_reason": reason,
        "recommended_skill": owner.get("name", ""),
        "recommended_skill_path": owner.get("path", ""),
        "recommended_skill_reason": owner.get("reason", ""),
        "skill_candidates": [
            {
                "name": item.get("name", ""),
                "path": item.get("path", ""),
                "score": item.get("score", 0),
            }
            for item in ([owner] + owner.get("alternatives", []) if owner else [])
        ],
        "target_hint": placement_target_hint(placement, owner),
    }


def normalize_method_key(signal: dict) -> str:
    operator = signal.get("operator", "other")
    operator = canonical_operator(operator)

    action_slug = method_slug_from_parts([str(signal.get("action") or "")], fallback="")
    if action_slug:
        return f"{operator}:{action_slug}"

    raw_key = str(signal.get("cluster_key") or "").strip().lower()
    if ":" in raw_key:
        raw_operator, raw_slug = raw_key.split(":", 1)
        operator = canonical_operator(raw_operator)
    else:
        raw_slug = raw_key

    if not raw_slug:
        card_slug = method_slug_from_parts(signal_card_parts(signal), fallback="")
        raw_slug = card_slug or str(signal.get("summary") or "method").lower()
    slug = method_slug_from_parts([raw_slug], fallback="")
    if not slug:
        slug = re.sub(r"[^a-z0-9]+", "_", raw_slug).strip("_")
        slug = re.sub(r"_+", "_", slug)
    if not slug:
        slug = "method"
    return f"{operator}:{slug}"


def method_fingerprint_for_signal(signal: dict) -> str:
    return method_hash(normalize_method_key(signal))


def compact_text(value: str, limit: int = 220) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def first_nonempty(records: list[dict], field: str) -> str:
    for record in reversed(records):
        value = compact_text(record.get(field, ""), limit=180)
        if value:
            return value
    return ""


def local_proposal_skeleton(cluster: dict, signals: list[dict], args: argparse.Namespace | None = None) -> dict:
    evidence = [compact_text(signal.get("summary", ""), limit=140) for signal in signals[-3:]]
    evidence = [item for item in evidence if item]
    trigger = first_nonempty(signals, "trigger") or first_nonempty(signals, "context") or cluster.get("ready_reason", "")
    action = first_nonempty(signals, "action") or first_nonempty(signals, "summary")
    transfer = first_nonempty(signals, "transfer_conditions")
    risk = first_nonempty(signals, "negative_cases") or first_nonempty(signals, "risk") or "[main risk or side effect]"
    if trigger and action:
        patch_hint = f"When {trigger}, {action}."
    else:
        patch_hint = "[1-3 sentence transferable rule]"
    if transfer:
        patch_hint = f"{patch_hint} Use when {transfer}."
    placement = infer_local_placement(args, cluster, signals)
    return {
        "target_hint": placement["target_hint"],
        "placement_hint": placement["placement_hint"],
        "placement_reason": placement["placement_reason"],
        "recommended_skill": placement["recommended_skill"],
        "recommended_skill_path": placement["recommended_skill_path"],
        "recommended_skill_reason": placement["recommended_skill_reason"],
        "agent_profile": placement["agent_profile"],
        "recommended_project_rule_file": placement["recommended_project_rule_file"],
        "recommended_project_rule_path": placement["recommended_project_rule_path"],
        "recommended_project_rule_reason": placement["recommended_project_rule_reason"],
        "project_rule_candidates": placement["project_rule_candidates"],
        "project_rule_existing_files": placement["project_rule_existing_files"],
        "skill_candidates": placement["skill_candidates"],
        "patch_hint": compact_text(patch_hint, limit=260),
        "risk_hint": compact_text(risk, limit=180),
        "evidence": evidence,
    }


def global_proposal_skeleton(cluster: dict, records: list[dict], args: argparse.Namespace | None = None) -> dict:
    evidence = list(cluster.get("summary_samples", []))[:3]
    trigger = first_nonempty(records, "trigger") or cluster.get("ready_reason", "")
    action = first_nonempty(records, "action") or (evidence[-1] if evidence else "")
    transfer = first_nonempty(records, "transfer_conditions")
    risk = first_nonempty(records, "negative_cases") or first_nonempty(records, "risk") or "[main risk or side effect]"
    if trigger and action:
        patch_hint = f"When {trigger}, {action}."
    else:
        patch_hint = "[1-3 sentence cross-project transferable rule]"
    if transfer:
        patch_hint = f"{patch_hint} Use when {transfer}."
    placement = infer_global_placement(args, cluster, records)
    return {
        "target_hint": placement["target_hint"],
        "placement_hint": placement["placement_hint"],
        "placement_reason": placement["placement_reason"],
        "recommended_skill": placement["recommended_skill"],
        "recommended_skill_path": placement["recommended_skill_path"],
        "recommended_skill_reason": placement["recommended_skill_reason"],
        "skill_candidates": placement["skill_candidates"],
        "patch_hint": compact_text(patch_hint, limit=260),
        "risk_hint": compact_text(risk, limit=180),
        "evidence": evidence,
    }


def global_threshold_reason(cluster: dict) -> str:
    project_count = len(set(cluster.get("project_hashes", [])))
    evidence_count = int(cluster.get("evidence_count", 0))
    strength = int(cluster.get("strength_sum", 0))
    correction_count = int(cluster.get("user_correction_count", 0))
    high_strength_count = int(cluster.get("high_strength_count", 0))

    if (
        project_count >= GLOBAL_PROJECT_THRESHOLD
        and evidence_count >= GLOBAL_EVIDENCE_THRESHOLD
        and strength >= GLOBAL_STRENGTH_THRESHOLD
    ):
        return (
            f"unique_project_count >= {GLOBAL_PROJECT_THRESHOLD}, "
            f"evidence_count >= {GLOBAL_EVIDENCE_THRESHOLD}, "
            f"strength_sum >= {GLOBAL_STRENGTH_THRESHOLD}"
        )
    if (
        project_count >= GLOBAL_FAST_PROJECT_THRESHOLD
        and strength >= GLOBAL_FAST_STRENGTH_THRESHOLD
        and (high_strength_count >= 2 or correction_count >= 2)
    ):
        return (
            f"fast path: unique_project_count >= {GLOBAL_FAST_PROJECT_THRESHOLD}, "
            f"strength_sum >= {GLOBAL_FAST_STRENGTH_THRESHOLD}, repeated high-strength/user-correction evidence"
        )
    return ""


def update_cluster_for_signal(args: argparse.Namespace, signal: dict) -> dict:
    state = read_cluster_state(args)
    clusters = state.setdefault("clusters", {})
    key = signal["cluster_key"]
    cluster = clusters.get(key, {
        "cluster_key": key,
        "operator": signal["operator"],
        "signal_count": 0,
        "strength_sum": 0,
        "sample_signal_ids": [],
        "last_seen": "",
        "status": "active",
        "ready_reason": "",
        "cooldown_signal_remaining": 0,
    })

    if cluster.get("status") == "cooldown" and int(cluster.get("cooldown_signal_remaining", 0) or 0) > 0:
        cluster["cooldown_signal_remaining"] = max(0, int(cluster.get("cooldown_signal_remaining", 0)) - 1)

    cluster["signal_count"] = int(cluster.get("signal_count", 0)) + 1
    cluster["strength_sum"] = int(cluster.get("strength_sum", 0)) + int(signal["strength"])
    cluster["last_seen"] = signal["timestamp"]
    samples = list(cluster.get("sample_signal_ids", []))
    if signal["id"] not in samples:
        samples.append(signal["id"])
    cluster["sample_signal_ids"] = samples[-5:]

    immediate = bool(signal.get("immediate"))
    reason = threshold_reason(cluster, immediate=immediate)
    if reason and not cooldown_is_active(cluster):
        cluster["status"] = "ready"
        cluster["ready_reason"] = reason
    elif cluster.get("status") != "cooldown":
        cluster["status"] = "active"

    clusters[key] = cluster
    write_cluster_state(args, state)
    return cluster


def global_signal_path(args: argparse.Namespace | None = None) -> Path:
    return global_data_dir(args) / "global-signals.jsonl"


def global_proposal_path(args: argparse.Namespace | None = None) -> Path:
    return global_data_dir(args) / "global-proposals.jsonl"


def adopted_global_path(args: argparse.Namespace | None = None) -> Path:
    return global_data_dir(args) / "adopted-global-edits.jsonl"


def rejected_global_path(args: argparse.Namespace | None = None) -> Path:
    return global_data_dir(args) / "rejected-global-proposals.jsonl"


def update_project_index_for_scan(args: argparse.Namespace, imported: int, scanned: int) -> None:
    project_hash = project_signature(args)
    _, identity_source = project_identity_material(args)
    index = read_project_index(args)
    projects = index.setdefault("projects", {})
    project = projects.get(project_hash, {
        "project_hash": project_hash,
        "identity_source": identity_source,
        "first_seen": utc_now(),
        "last_seen": "",
        "imported_signal_count": 0,
        "last_scan_signal_count": 0,
    })
    project["identity_source"] = identity_source
    project["last_seen"] = utc_now()
    project["imported_signal_count"] = int(project.get("imported_signal_count", 0)) + imported
    project["last_scan_signal_count"] = scanned
    projects[project_hash] = project
    write_project_index(index, args)


def global_record_from_signal(args: argparse.Namespace, signal: dict) -> dict:
    project_hash = project_signature(args)
    source_signal_id = str(signal.get("id", ""))
    fingerprint = method_fingerprint_for_signal(signal)
    record_id = make_id("gsig")
    record = {
        "id": record_id,
        "timestamp": utc_now(),
        "project_hash": project_hash,
        "source_signal_id": source_signal_id,
        "source_timestamp": signal.get("timestamp", ""),
        "dedupe_key": f"{project_hash}:{source_signal_id}",
        "method_fingerprint": fingerprint,
        "method_key": normalize_method_key(signal),
        "method_signature": method_signature(signal),
        "operator": signal.get("operator", "other"),
        "local_cluster_key": signal.get("cluster_key", ""),
        "summary": compact_text(signal.get("summary", "")),
        "context": compact_text(signal.get("context", ""), limit=160),
        "source_type": signal.get("source_type", ""),
        "strength": int(signal.get("strength", 1) or 1),
        "risk": compact_text(signal.get("risk", ""), limit=160),
        "status": "active",
    }
    for field in SIGNAL_CARD_FIELDS:
        value = compact_text(signal.get(field, ""), limit=160)
        if value:
            record[field] = value
    return record


def merge_global_record_into_clusters(clusters: dict, record: dict) -> None:
    fingerprint = record["method_fingerprint"]
    cluster = clusters.get(fingerprint, {
        "method_fingerprint": fingerprint,
        "method_key": record.get("method_key", ""),
        "operator": record.get("operator", "other"),
        "evidence_count": 0,
        "strength_sum": 0,
        "project_hashes": [],
        "sample_global_signal_ids": [],
        "summary_samples": [],
        "method_signature_samples": [],
        "source_type_counts": {},
        "user_correction_count": 0,
        "high_strength_count": 0,
        "last_seen": "",
        "status": "active",
        "ready_reason": "",
        "cooldown_signal_remaining": 0,
    })

    if cluster.get("status") == "cooldown" and int(cluster.get("cooldown_signal_remaining", 0) or 0) > 0:
        cluster["cooldown_signal_remaining"] = max(0, int(cluster.get("cooldown_signal_remaining", 0)) - 1)

    cluster["method_key"] = cluster.get("method_key") or record.get("method_key", "")
    cluster["operator"] = cluster.get("operator") or record.get("operator", "other")
    cluster["evidence_count"] = int(cluster.get("evidence_count", 0)) + 1
    cluster["strength_sum"] = int(cluster.get("strength_sum", 0)) + int(record.get("strength", 1) or 1)
    cluster["last_seen"] = record.get("source_timestamp") or record.get("timestamp", "")

    project_hashes = list(cluster.get("project_hashes", []))
    if record.get("project_hash") not in project_hashes:
        project_hashes.append(record.get("project_hash"))
    cluster["project_hashes"] = sorted(project_hashes)

    sample_ids = list(cluster.get("sample_global_signal_ids", []))
    if record.get("id") not in sample_ids:
        sample_ids.append(record.get("id"))
    cluster["sample_global_signal_ids"] = sample_ids[-5:]

    samples = list(cluster.get("summary_samples", []))
    summary = record.get("summary", "")
    if summary and summary not in samples:
        samples.append(summary)
    cluster["summary_samples"] = samples[-3:]

    signature_samples = list(cluster.get("method_signature_samples", []))
    signature = record.get("method_signature", "")
    if signature and signature not in signature_samples:
        signature_samples.append(signature)
    cluster["method_signature_samples"] = signature_samples[-3:]

    source_counts = dict(cluster.get("source_type_counts", {}))
    source_type = record.get("source_type", "unknown")
    source_counts[source_type] = int(source_counts.get(source_type, 0)) + 1
    cluster["source_type_counts"] = source_counts
    if source_type == "user_correction":
        cluster["user_correction_count"] = int(cluster.get("user_correction_count", 0)) + 1
    if int(record.get("strength", 1) or 1) >= 3:
        cluster["high_strength_count"] = int(cluster.get("high_strength_count", 0)) + 1

    reason = global_threshold_reason(cluster)
    if cluster.get("status") in {"proposed", "adopted"}:
        pass
    elif reason and not cooldown_is_active(cluster):
        cluster["status"] = "ready"
        cluster["ready_reason"] = reason
    elif cluster.get("status") != "cooldown":
        cluster["status"] = "active"
        cluster["ready_reason"] = ""

    clusters[fingerprint] = cluster


def import_local_signals_to_global(args: argparse.Namespace) -> dict:
    ensure_global_runtime(args)
    project_hash = project_signature(args)
    local_signals = []
    if runtime_exists(args):
        local_signals = [
            signal for signal in read_jsonl(data_dir(args) / "signals.jsonl")
            if signal.get("status") == "active"
        ]

    global_signals = read_jsonl(global_signal_path(args))
    seen = {record.get("dedupe_key") for record in global_signals}
    cluster_state = read_global_clusters(args)
    clusters = cluster_state.setdefault("clusters", {})

    imported_records: list[dict] = []
    for signal in local_signals:
        source_signal_id = str(signal.get("id", ""))
        if not source_signal_id:
            continue
        dedupe_key = f"{project_hash}:{source_signal_id}"
        if dedupe_key in seen:
            continue
        record = global_record_from_signal(args, signal)
        append_jsonl(global_signal_path(args), record)
        imported_records.append(record)
        seen.add(dedupe_key)
        merge_global_record_into_clusters(clusters, record)

    if imported_records:
        write_global_clusters(cluster_state, args)
    update_project_index_for_scan(args, imported=len(imported_records), scanned=len(local_signals))

    state = read_global_state(args)
    state["last_scan_at"] = utc_now()
    state["last_scan_project_count"] = len(read_project_index(args).get("projects", {}))
    state["last_scan_signal_count"] = len(global_signals) + len(imported_records)
    state["last_ready_cluster_count"] = sum(1 for c in clusters.values() if c.get("status") == "ready")
    write_global_state(state, args)

    return {
        "imported": len(imported_records),
        "scanned_local_signals": len(local_signals),
        "project_hash": project_hash,
    }


def load_global_proposals(args: argparse.Namespace) -> list[dict]:
    ensure_global_runtime(args)
    return read_jsonl(global_proposal_path(args))


def save_global_proposals(args: argparse.Namespace, proposals: list[dict]) -> None:
    ensure_global_runtime(args)
    write_jsonl(global_proposal_path(args), proposals)


def get_global_proposal(args: argparse.Namespace, proposal_id: str) -> tuple[list[dict], dict]:
    proposals = load_global_proposals(args)
    for proposal in proposals:
        if proposal.get("id") == proposal_id:
            return proposals, proposal
    raise SystemExit(f"Global proposal not found: {proposal_id!r}")


def collect_global_summary(args: argparse.Namespace, import_result: dict | None = None) -> dict:
    ensure_global_runtime(args)
    global_signals = read_jsonl(global_signal_path(args))
    proposals = read_jsonl(global_proposal_path(args))
    adopted = read_jsonl(adopted_global_path(args))
    rejected = read_jsonl(rejected_global_path(args))
    clusters = read_global_clusters(args).get("clusters", {})
    projects = read_project_index(args).get("projects", {})
    cluster_counts = Counter(c.get("status", "unknown") for c in clusters.values())
    proposal_counts = Counter(p.get("status", "unknown") for p in proposals)
    records_by_id = {record.get("id", ""): record for record in global_signals}

    ready_clusters = []
    for fingerprint, cluster in sorted(clusters.items()):
        if cluster.get("status") == "ready":
            sample_records = [
                records_by_id[sid]
                for sid in cluster.get("sample_global_signal_ids", [])
                if sid in records_by_id
            ]
            ready_clusters.append({
                "method_fingerprint": fingerprint,
                "method_key": cluster.get("method_key", ""),
                "operator": cluster.get("operator", ""),
                "evidence_count": int(cluster.get("evidence_count", 0)),
                "project_count": len(set(cluster.get("project_hashes", []))),
                "strength_sum": int(cluster.get("strength_sum", 0)),
                "ready_reason": cluster.get("ready_reason", ""),
                "samples": list(cluster.get("summary_samples", []))[:3],
                "skeleton": global_proposal_skeleton(cluster, sample_records, args),
            })

    pending_proposals = []
    for proposal in proposals:
        if proposal.get("status") in {"pending_user_gate", "needs_revision"}:
            pending_proposals.append({
                "proposal_id": proposal.get("id", ""),
                "method_fingerprint": proposal.get("method_fingerprint", ""),
                "placement": proposal.get("placement", ""),
                "recommended_skill": proposal.get("recommended_skill", ""),
                "status": proposal.get("status", ""),
                "target": proposal.get("target", ""),
            })

    import_result = import_result or {"imported": 0, "scanned_local_signals": 0, "project_hash": ""}
    return {
        "global_runtime": str(global_runtime_root(args)),
        "imported": int(import_result.get("imported", 0)),
        "scanned_local_signals": int(import_result.get("scanned_local_signals", 0)),
        "current_project_hash": import_result.get("project_hash", ""),
        "global_signals": len(global_signals),
        "projects": len(projects),
        "clusters": len(clusters),
        "cluster_counts": dict(cluster_counts),
        "global_proposals": len(proposals),
        "proposal_counts": dict(proposal_counts),
        "adopted_global_edits": len(adopted),
        "rejected_global_proposals": len(rejected),
        "ready_clusters": ready_clusters,
        "pending_proposals": pending_proposals,
    }


def command_global_cycle(args: argparse.Namespace) -> None:
    import_result = import_local_signals_to_global(args)
    summary = collect_global_summary(args, import_result)

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        if getattr(args, "fail_on_pending_gate", False) and summary["pending_proposals"]:
            raise SystemExit(2)
        return

    print(f"{STATUS_LABELS['global_runtime']}: {summary['global_runtime']}")
    print(
        "{imported_label}: {imported} | {projects_label}: {projects} | {signals_label}: {signals} | "
        "{clusters_label}: {clusters} | {ready_label}: {ready} | {pending_label}: {pending}".format(
            imported_label=STATUS_LABELS["imported"],
            imported=summary["imported"],
            projects_label=STATUS_LABELS["projects"],
            projects=summary["projects"],
            signals_label=STATUS_LABELS["global_signals"],
            signals=summary["global_signals"],
            clusters_label=STATUS_LABELS["clusters"],
            clusters=summary["clusters"],
            ready_label=STATUS_LABELS["ready"],
            ready=summary["cluster_counts"].get("ready", 0),
            pending_label=STATUS_LABELS["pending_gates"],
            pending=summary["proposal_counts"].get("pending_user_gate", 0),
        )
    )

    if summary["pending_proposals"]:
        print("\nPending global user gates:")
        for proposal in summary["pending_proposals"]:
            print(
                f"- {proposal['proposal_id']}  status={proposal['status']}  "
                f"placement={proposal.get('placement', '')}  "
                f"method={proposal['method_fingerprint']}"
            )
            if proposal.get("recommended_skill"):
                print(f"  recommended_skill: {proposal.get('recommended_skill')}")

    if summary["ready_clusters"]:
        print("\nReady global clusters:")
        for cluster in summary["ready_clusters"]:
            print(
                f"- {cluster['method_fingerprint']}  projects={cluster['project_count']}  "
                f"evidence={cluster['evidence_count']}  strength={cluster['strength_sum']}  "
                f"method={cluster['method_key']}"
            )
            skeleton = cluster.get("skeleton", {})
            if skeleton:
                print(f"  placement_hint: {skeleton.get('placement_hint', '')}")
                print(f"  placement_reason: {skeleton.get('placement_reason', '')}")
                if skeleton.get("recommended_skill"):
                    print(f"  recommended_skill: {skeleton.get('recommended_skill', '')}")
                    print(f"  recommended_skill_path: {skeleton.get('recommended_skill_path', '')}")
                print(f"  target_hint: {skeleton.get('target_hint', '')}")

    if getattr(args, "fail_on_pending_gate", False) and summary["pending_proposals"]:
        raise SystemExit(2)


def command_global_status(args: argparse.Namespace) -> None:
    summary = collect_global_summary(args)
    print(f"{STATUS_LABELS['global_runtime']}: {summary['global_runtime']}")
    print(f"{STATUS_LABELS['projects']}: {summary['projects']}")
    print(f"{STATUS_LABELS['global_signals']}: {summary['global_signals']}")
    print(f"{STATUS_LABELS['global_clusters']}: {summary['clusters']}")
    print(f"  {STATUS_LABELS['active']}:   {summary['cluster_counts'].get('active', 0)}")
    print(f"  {STATUS_LABELS['ready']}:    {summary['cluster_counts'].get('ready', 0)}")
    print(f"  {STATUS_LABELS['proposed']}: {summary['cluster_counts'].get('proposed', 0)}")
    print(f"  {STATUS_LABELS['cooldown']}: {summary['cluster_counts'].get('cooldown', 0)}")
    print(f"{STATUS_LABELS['global_proposals']}: {summary['global_proposals']}")
    print(f"  {STATUS_LABELS['pending_user_gate']}: {summary['proposal_counts'].get('pending_user_gate', 0)}")
    print(f"  {STATUS_LABELS['needs_revision']}:    {summary['proposal_counts'].get('needs_revision', 0)}")
    print(f"{STATUS_LABELS['adopted_global_edits']}: {summary['adopted_global_edits']}")
    print(f"{STATUS_LABELS['rejected_global_proposals']}: {summary['rejected_global_proposals']}")


def classify_user_correction(text: str) -> dict:
    normalized = " ".join(str(text or "").strip().split()).lower()
    if not normalized:
        return {
            "input_state": "none",
            "score": 0,
            "categories": [],
            "evidence": [],
            "strong_matches": [],
            "medium_matches": [],
            "context_matches": [],
            "weak_matches": [],
            "trigger_intent": "",
            "internal_context": "",
        }

    evidence = correction_evidence(normalized)
    categories = sorted({item["category"] for item in evidence})
    strong = [item["pattern"] for item in evidence if item["weight"] >= 3]
    format_only = categories == ["output_format_correction"]
    medium = regex_hits(MEDIUM_CORRECTION_PATTERNS, normalized)
    context = regex_hits(CORRECTION_CONTEXT_PATTERNS, normalized)
    weak = regex_hits(WEAK_CLARIFICATION_PATTERNS, normalized)

    score = sum(item["weight"] for item in evidence) + len(medium) + min(len(context), 2)
    if weak and not strong and not medium:
        state = "none"
    elif strong and not (format_only and not context and len(evidence) == 1):
        state = "strong_user_correction"
    elif (medium and context) or score >= 5:
        state = "strong_user_correction"
    elif medium:
        state = "possible_user_correction"
    else:
        state = "none"

    return {
        "input_state": state,
        "score": score,
        "categories": categories[:8],
        "evidence": evidence[:8],
        "strong_matches": strong[:5],
        "medium_matches": medium[:5],
        "context_matches": context[:5],
        "weak_matches": weak[:5],
        "trigger_intent": "user_correction" if state != "none" else "",
        "internal_context": input_internal_context(state),
    }


def input_internal_context(input_state: str) -> str:
    if input_state == "strong_user_correction":
        return (
            "User may be correcting the previous answer. Prioritize fixing the mismatch, "
            "do not explain internal state, and only consider jinhua if the correction exposes "
            "a reusable trigger plus action under the existing rules."
        )
    if input_state == "possible_user_correction":
        return (
            "User may be clarifying or narrowing the previous request. Align to the current "
            "boundary and avoid expanding scope."
        )
    return ""


def join_contexts(*parts: str) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())


def extract_hook_prompt(payload: object) -> str:
    if not isinstance(payload, dict):
        return ""
    return authoritative_string(
        payload,
        ("prompt", "userPrompt", "message"),
        HOOK_PROMPT_PARENT_PATHS,
    )


def read_hook_payload(text: str) -> dict:
    stripped = text.strip().lstrip("\ufeff")
    if not stripped:
        return {}
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return {"prompt": text}
    return parsed if isinstance(parsed, dict) else {}


def read_hook_stdin() -> str:
    stream = getattr(sys.stdin, "buffer", None)
    if stream is None:
        return sys.stdin.read()
    raw = stream.read()
    if not raw:
        return ""
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")) or raw.count(b"\x00") > len(raw) // 10:
        try:
            return raw.decode("utf-16")
        except UnicodeDecodeError:
            pass
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        encoding = getattr(sys.stdin, "encoding", None) or "mbcs"
        return raw.decode(encoding, errors="replace")


def normalize_hook_path(value: object) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = os.path.expandvars(os.path.expanduser(value.strip().strip('"')))
    if not text:
        return None
    candidate = Path(text)
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    try:
        candidate = candidate.resolve()
    except OSError:
        return None
    if candidate.exists() and candidate.is_file():
        candidate = candidate.parent
    return candidate


def hook_project_root_info(payload: dict, args: argparse.Namespace | None) -> tuple[Path | None, str]:
    configured = getattr(args, "project_root", ".") if args is not None else "."
    if str(configured or "").strip() not in {"", "."}:
        root = normalize_hook_path(str(configured))
        if root is not None:
            return root, "explicit"

    payload_value = authoritative_string(payload, HOOK_PROJECT_PATH_KEYS, HOOK_METADATA_PARENT_PATHS)
    root = normalize_hook_path(payload_value)
    if root is not None:
        return root, "payload"

    for key in HOOK_PROJECT_ENV_KEYS:
        root = normalize_hook_path(os.environ.get(key, ""))
        if root is not None:
            return root, f"env:{key}"

    root = normalize_hook_path(str(Path.cwd()))
    plugin_roots = [skill_root()]
    plugin_root_env = normalize_hook_path(os.environ.get("CLAUDE_PLUGIN_ROOT", ""))
    if plugin_root_env is not None:
        plugin_roots.append(plugin_root_env)
    if root is not None and any(root == candidate or path_is_relative_to(root, candidate) for candidate in plugin_roots):
        return root, "unsafe_process_cwd"
    return root, "process_cwd"


def hook_project_root(payload: dict, args: argparse.Namespace | None) -> Path:
    root, _ = hook_project_root_info(payload, args)
    return root or Path.cwd().resolve()


def apply_payload_project_root(args: argparse.Namespace, payload: dict) -> bool:
    configured = str(getattr(args, "project_root", ".") or "").strip()
    if configured not in {"", "."}:
        args._jinhua_hook_runtime_disabled = False
        return True

    root, source = hook_project_root_info(payload, args)
    if root is None or source == "unsafe_process_cwd":
        args._jinhua_hook_runtime_disabled = True
        return False
    args.project_root = str(root)
    args._jinhua_hook_runtime_disabled = False
    return True


def command_classify_input(args: argparse.Namespace) -> None:
    text = args.text if args.text else sys.stdin.read()
    result = classify_user_correction(text)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"input_state: {result['input_state']}")
        if result["trigger_intent"]:
            print(f"trigger_intent: {result['trigger_intent']}")
        if result["internal_context"]:
            print(f"internal_context: {result['internal_context']}")


def ready_attention_counts(args: argparse.Namespace) -> dict:
    local_ready = local_pending = global_ready = global_pending = 0
    if runtime_exists(args):
        clusters = read_cluster_state(args).get("clusters", {})
        proposals = read_jsonl(data_dir(args) / "proposals.jsonl")
        local_ready = sum(1 for cluster in clusters.values() if cluster.get("status") == "ready")
        local_pending = sum(1 for proposal in proposals if proposal.get("status") in {"pending_user_gate", "needs_revision"})
    if global_runtime_exists(args):
        clusters = read_global_clusters(args).get("clusters", {})
        proposals = read_jsonl(global_proposal_path(args))
        global_ready = sum(1 for cluster in clusters.values() if cluster.get("status") == "ready")
        global_pending = sum(1 for proposal in proposals if proposal.get("status") in {"pending_user_gate", "needs_revision"})
    return {
        "local_ready": local_ready,
        "local_pending": local_pending,
        "global_ready": global_ready,
        "global_pending": global_pending,
    }


def ready_attention_context(args: argparse.Namespace, session_id: str, turn_state: dict) -> dict:
    counts = ready_attention_counts(args)
    pending = counts["local_pending"] + counts["global_pending"]
    ready = counts["local_ready"] + counts["global_ready"]
    result = {
        **counts,
        "session_id": session_id,
        "turn_count": int(turn_state.get("turn_count", 0) or 0),
        "additional_context": "",
    }
    if pending:
        result["additional_context"] = (
            f"jinhua has pending user gates (local {counts['local_pending']}, global {counts['global_pending']}). "
            "Run cycle and surface one gate before new jinhua work."
        )
    elif ready:
        result["additional_context"] = (
            f"jinhua has ready clusters (local {counts['local_ready']}, global {counts['global_ready']}). "
            "Run cycle, then create one proposal or state a concrete skip reason; keep the user gate."
        )
    return result


def periodic_review_context(turn_state: dict) -> str:
    if not turn_state.get("periodic_review_due"):
        return ""
    return (
        "Periodic jinhua review: scan this turn and prior conversation. "
        "If a concrete reusable error or method has trigger + action, use jinhua rules; otherwise stay silent."
    )


def codex_user_prompt_submit_output(payload: dict, args: argparse.Namespace | None = None) -> dict:
    prompt = extract_hook_prompt(payload)
    result = classify_user_correction(prompt)
    turn_state = {}
    ready_attention = {}
    if (
        args is not None
        and not getattr(args, "_jinhua_hook_runtime_disabled", False)
        and hook_identity_available(payload)
    ):
        session_id = hook_session_id(payload)
        turn_id = hook_turn_id(payload)
        turn_state = record_prompt_turn(args, session_id, turn_id)
        ready_attention = ready_attention_context(args, session_id, turn_state)
    output: dict = {"continue": True}
    context = join_contexts(
        result["internal_context"],
        ready_attention.get("additional_context", ""),
        periodic_review_context(turn_state),
    )
    if not context:
        return output
    output["hookSpecificOutput"] = {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": context,
    }
    return output


def command_codex_user_prompt_submit(args: argparse.Namespace) -> None:
    if args.text:
        payload = {"hook_event_name": "UserPromptSubmit", "prompt": args.text}
    else:
        payload = read_hook_payload(read_hook_stdin())
    apply_payload_project_root(args, payload)
    output = codex_user_prompt_submit_output(payload, args)
    print(json.dumps(output, ensure_ascii=False, indent=2 if args.pretty else None))


def payload_container(payload: object, path: tuple[str, ...]) -> dict | None:
    current = payload
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current if isinstance(current, dict) else None


def authoritative_value(
    payload: object,
    keys: tuple[str, ...],
    parent_paths: tuple[tuple[str, ...], ...],
) -> object | None:
    for path in parent_paths:
        container = payload_container(payload, path)
        if container is None:
            continue
        for key in keys:
            if key in container:
                return container[key]
    return None


def authoritative_string(
    payload: object,
    keys: tuple[str, ...],
    parent_paths: tuple[tuple[str, ...], ...],
) -> str:
    value = authoritative_value(payload, keys, parent_paths)
    return value.strip() if isinstance(value, str) and value.strip() else ""


def hook_session_id(payload: dict) -> str:
    found = authoritative_string(payload, HOOK_SESSION_ID_KEYS, HOOK_METADATA_PARENT_PATHS)
    if found:
        return method_hash(found)
    transcript = authoritative_string(
        payload,
        ("transcript_path", "transcriptPath"),
        HOOK_METADATA_PARENT_PATHS,
    )
    if transcript:
        return method_hash(transcript)
    cwd = authoritative_string(payload, HOOK_PROJECT_PATH_KEYS, HOOK_METADATA_PARENT_PATHS)
    return method_hash(str(cwd or "default-session"))


def hook_turn_id(payload: dict) -> str:
    found = authoritative_string(payload, HOOK_TURN_ID_KEYS, HOOK_METADATA_PARENT_PATHS)
    if found:
        return method_hash(found)
    prompt = extract_hook_prompt(payload)
    if prompt:
        return method_hash(prompt)
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M")


def hook_identity_available(payload: dict) -> bool:
    session_evidence = authoritative_string(
        payload,
        HOOK_SESSION_ID_KEYS + ("transcript_path", "transcriptPath") + HOOK_PROJECT_PATH_KEYS,
        HOOK_METADATA_PARENT_PATHS,
    )
    turn_evidence = authoritative_string(payload, HOOK_TURN_ID_KEYS, HOOK_METADATA_PARENT_PATHS)
    return bool(session_evidence and (turn_evidence or extract_hook_prompt(payload)))


def periodic_review_interval() -> int:
    return DEFAULT_PERIODIC_STOP_INTERVAL


def hook_tool_command(payload: dict) -> str:
    tool_name = authoritative_string(payload, ("tool_name", "toolName"), HOOK_TOOL_PARENT_PATHS).lower()
    if tool_name and tool_name not in HOOK_SHELL_TOOL_NAMES:
        return ""

    tool_input = authoritative_value(payload, ("tool_input", "toolInput"), HOOK_TOOL_PARENT_PATHS)
    if isinstance(tool_input, str) and tool_input.strip():
        return tool_input.strip()
    if isinstance(tool_input, dict):
        command = authoritative_string(tool_input, ("command", "cmd"), ((),))
        if command:
            return command
        args = tool_input.get("args")
        if isinstance(args, dict):
            command = authoritative_string(args, ("command", "cmd"), ((),))
            if command:
                return command

    if tool_name in HOOK_SHELL_TOOL_NAMES:
        command = authoritative_string(payload, ("command", "cmd"), HOOK_TOOL_PARENT_PATHS)
        if command:
            return command
        args = authoritative_value(payload, ("args", "arguments"), HOOK_TOOL_PARENT_PATHS)
        if isinstance(args, dict):
            return authoritative_string(args, ("command", "cmd"), ((),))
    return ""


def shell_command_tokens(command: str) -> list[str]:
    tokens = re.findall(r'''"(?:\\.|[^"])*"|'(?:\\.|[^'])*'|[^\s]+''', command)
    result = []
    for token in tokens:
        if len(token) >= 2 and token[0] == token[-1] and token[0] in {'"', "'"}:
            token = token[1:-1]
        result.append(token)
    return result


def clean_command_token(token: str) -> str:
    return token.strip().strip(";&|()")


def command_basename(token: str) -> str:
    return clean_command_token(token).replace("\\", "/").rsplit("/", 1)[-1].lower()


def is_jinhua_script_token(token: str) -> bool:
    return command_basename(token) == "jinhua.py"


def jinhua_entry_from_command(command: str) -> str:
    tokens = shell_command_tokens(command)
    if not tokens:
        return ""

    index = 0
    while index < len(tokens) and clean_command_token(tokens[index]) in {"", "&"}:
        index += 1
    while index < len(tokens) and "=" in tokens[index] and not tokens[index].startswith(("/", ".", "\\")):
        index += 1
    if index >= len(tokens):
        return ""

    executable = command_basename(tokens[index])
    if executable in {"cmd", "cmd.exe"}:
        for marker in ("/c", "/k"):
            if marker in [clean_command_token(token).lower() for token in tokens[index + 1:]]:
                marker_index = next(
                    offset for offset in range(index + 1, len(tokens))
                    if clean_command_token(tokens[offset]).lower() == marker
                )
                return jinhua_entry_from_command(" ".join(tokens[marker_index + 1:]))
        return ""
    if executable in {"powershell", "powershell.exe", "pwsh", "pwsh.exe", "bash", "sh"}:
        wrapper_markers = {"-command", "-c", "-lc"}
        for marker_index in range(index + 1, len(tokens)):
            if clean_command_token(tokens[marker_index]).lower() in wrapper_markers:
                return jinhua_entry_from_command(" ".join(tokens[marker_index + 1:]))
        return ""

    script_index = -1
    if executable in {"python", "python.exe", "python3", "python3.exe", "py", "py.exe"}:
        candidate_index = index + 1
        while candidate_index < len(tokens) and clean_command_token(tokens[candidate_index]).startswith("-"):
            candidate_index += 1
        if candidate_index < len(tokens) and is_jinhua_script_token(tokens[candidate_index]):
            script_index = candidate_index
    elif is_jinhua_script_token(tokens[index]):
        script_index = index
    if script_index < 0:
        return ""

    options_with_values = {
        "--project-root",
        "--runtime-dir",
        "--global-runtime-dir",
        "--project-id",
        "--agent-profile",
    }
    option_flags = {"--pretty"}
    index = script_index + 1
    while index < len(tokens):
        token = clean_command_token(tokens[index])
        lowered = token.lower()
        if lowered in options_with_values:
            index += 2
            continue
        if any(lowered.startswith(f"{option}=") for option in options_with_values):
            index += 1
            continue
        if lowered in option_flags:
            index += 1
            continue
        return lowered if lowered in JINHUA_GUARDED_COMMANDS else ""
    return ""


def jinhua_entry_from_payload(payload: dict) -> str:
    return jinhua_entry_from_command(hook_tool_command(payload))


def default_guard_state() -> dict:
    return {"schema": 2, "events": [], "sessions": {}}


def read_guard_state(args: argparse.Namespace) -> dict:
    state = read_json(invocation_guard_path(args), default_guard_state())
    state["schema"] = 2
    if not isinstance(state.get("events"), list):
        state["events"] = []
    state.pop("stop_tickets", None)
    if not isinstance(state.get("sessions"), dict):
        state["sessions"] = {}
    for session in state["sessions"].values():
        if isinstance(session, dict):
            session.pop("periodic_stop_due", None)
    return state


def write_guard_state(args: argparse.Namespace, state: dict) -> None:
    runtime_meta_dir(args).mkdir(parents=True, exist_ok=True)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    events = []
    for event in state.get("events", []):
        timestamp = parse_utc(event.get("timestamp", ""))
        if timestamp is None or timestamp >= cutoff:
            events.append(event)
    state["events"] = events[-100:]
    sessions = state.get("sessions", {})
    if isinstance(sessions, dict):
        state["sessions"] = dict(list(sessions.items())[-100:])
    write_json(invocation_guard_path(args), state)


def record_prompt_turn(args: argparse.Namespace, session_id: str, turn_id: str) -> dict:
    state = read_guard_state(args)
    sessions = state.setdefault("sessions", {})
    session = sessions.setdefault(session_id, {"turn_count": 0, "seen_turns": []})
    seen_turns = session.setdefault("seen_turns", [])
    new_turn = turn_id not in seen_turns
    if new_turn:
        seen_turns.append(turn_id)
        session["turn_count"] = int(session.get("turn_count", 0)) + 1
    interval = periodic_review_interval()
    due = bool(new_turn and interval and session["turn_count"] > 0 and session["turn_count"] % interval == 0)
    session["seen_turns"] = seen_turns[-50:]
    write_guard_state(args, state)
    return {"turn_count": session["turn_count"], "interval": interval, "periodic_review_due": due}


def guard_reason_digest(reason: str) -> str:
    return method_hash(" ".join(str(reason or "").split()).lower()) if reason else ""


def invocation_guard(args: argparse.Namespace, session_id: str, turn_id: str, source: str, reason: str, entry: str = "", mark: bool = False) -> dict:
    state = read_guard_state(args)
    reason_digest = guard_reason_digest(reason)
    same_turn = [
        event for event in state.get("events", [])
        if event.get("session_id") == session_id and event.get("turn_id") == turn_id
    ]
    same_reason = [event for event in same_turn if event.get("reason_digest") == reason_digest or not reason_digest]
    if source == "stop" and same_turn:
        decision = "already_handled"
    elif len(same_turn) >= 3:
        decision = "block_loop"
    elif same_reason:
        decision = "already_handled" if source == "stop" else "skip_duplicate"
    else:
        decision = "allow"

    if mark and decision == "allow":
        state.setdefault("events", []).append({
            "timestamp": utc_now(),
            "session_id": session_id,
            "turn_id": turn_id,
            "source": source,
            "reason_digest": reason_digest,
            "entry": entry,
        })
        write_guard_state(args, state)

    return {
        "decision": decision,
        "session_id": session_id,
        "turn_id": turn_id,
        "entry": entry,
        "reason_digest": reason_digest,
    }


def command_guard(args: argparse.Namespace) -> None:
    result = invocation_guard(
        args,
        args.session_id or "manual",
        args.turn_id or datetime.now(timezone.utc).strftime("%Y%m%d%H%M"),
        args.source,
        args.reason,
        args.entry,
        args.mark,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))


def codex_post_tool_use_output(payload: dict, args: argparse.Namespace) -> dict:
    entry = jinhua_entry_from_payload(payload)
    output: dict = {"continue": True}
    if (
        not entry
        or getattr(args, "_jinhua_hook_runtime_disabled", False)
        or not hook_identity_available(payload)
    ):
        return output
    session_id = hook_session_id(payload)
    turn_id = hook_turn_id(payload)
    invocation_guard(args, session_id, turn_id, "post_tool_use", "jinhua_workflow", entry, mark=True)
    return output


def command_codex_post_tool_use(args: argparse.Namespace) -> None:
    payload = read_hook_payload(read_hook_stdin())
    apply_payload_project_root(args, payload)
    output = codex_post_tool_use_output(payload, args)
    print(json.dumps(output, ensure_ascii=False, indent=2 if args.pretty else None))


def command_global_propose(args: argparse.Namespace) -> None:
    ensure_global_runtime(args)
    cluster_state = read_global_clusters(args)
    clusters = cluster_state.get("clusters", {})
    cluster = clusters.get(args.method_fingerprint)
    if not cluster:
        raise SystemExit(f"Global cluster not found: {args.method_fingerprint!r}")
    if cluster.get("status") == "cooldown" and cooldown_is_active(cluster):
        raise SystemExit(f"Global cluster is in cooldown: {args.method_fingerprint}")
    if cluster.get("status") not in {"ready", "proposed"}:
        raise SystemExit("Global cluster is not ready.")

    records_by_id = {record.get("id", ""): record for record in read_jsonl(global_signal_path(args))}
    sample_records = [
        records_by_id[sid]
        for sid in cluster.get("sample_global_signal_ids", [])
        if sid in records_by_id
    ]
    skeleton = global_proposal_skeleton(cluster, sample_records, args)
    placement = normalize_placement(args.placement, skeleton.get("placement_hint", "personal_global_skill"))
    if placement not in GLOBAL_PROPOSAL_PLACEMENTS:
        raise SystemExit("Global proposals may use only skill_patch or personal_global_skill.")
    placement_reason = args.placement_reason or skeleton.get("placement_reason", "")
    recommended_skill = args.recommended_skill or skeleton.get("recommended_skill", "")
    recommended_skill_path = args.recommended_skill_path or skeleton.get("recommended_skill_path", "")
    if placement == "skill_patch" and (not recommended_skill or not recommended_skill_path):
        raise SystemExit("skill_patch requires a concrete recommended local Skill and path.")
    target = require_concrete_text(args.target, "--target")
    patch = require_markdown_patch(args.patch)
    risk = require_concrete_text(args.risk, "--risk")

    proposal_id = make_id("gprop")
    proposal = {
        "id": proposal_id,
        "timestamp": utc_now(),
        "method_fingerprint": args.method_fingerprint,
        "method_key": cluster.get("method_key", ""),
        "operator": cluster.get("operator", ""),
        "trigger": cluster.get("ready_reason", ""),
        "evidence_global_signal_ids": list(cluster.get("sample_global_signal_ids", []))[-3:],
        "placement": placement,
        "placement_reason": placement_reason,
        "recommended_skill": recommended_skill,
        "recommended_skill_path": recommended_skill_path,
        "recommended_skill_reason": skeleton.get("recommended_skill_reason", ""),
        "target": target,
        "patch": patch,
        "risk": risk,
        "project_count": len(set(cluster.get("project_hashes", []))),
        "evidence_count": int(cluster.get("evidence_count", 0)),
        "strength_sum": int(cluster.get("strength_sum", 0)),
        "status": "pending_user_gate",
        "user_gate": GLOBAL_USER_GATE,
    }
    append_jsonl(global_proposal_path(args), proposal)
    cluster["status"] = "proposed"
    cluster["last_proposal_id"] = proposal_id
    clusters[args.method_fingerprint] = cluster
    write_global_clusters(cluster_state, args)
    state = read_global_state(args)
    state["last_proposal_id"] = proposal_id
    write_global_state(state, args)

    evidence_text = "\n".join(f"- {s}" for s in cluster.get("summary_samples", [])[:3]) or "- No sample summaries found."
    print(f"""## Global Skill Evolution Proposal

Trigger:
{proposal['trigger']}

Recommended placement:
{proposal['placement']}

Placement reason:
{proposal['placement_reason']}

Evidence:
{evidence_text}

Recommended local Skill:
{proposal['recommended_skill'] or '[none]'}

Recommended Skill path:
{proposal['recommended_skill_path'] or '[none]'}

Target:
{proposal['target']}

Patch:
{proposal['patch']}

Risk:
{proposal['risk']}

User gate:
Choose: {GLOBAL_USER_GATE}
Choosing a placement means accepting that placement.

Proposal ID:
{proposal_id}
""")


def command_global_apply(args: argparse.Namespace) -> None:
    ensure_global_runtime(args)
    proposals, proposal = get_global_proposal(args, args.proposal_id)
    if proposal.get("status") != "pending_user_gate":
        raise SystemExit("Global proposal is not pending user gate.")

    final_placement = normalize_placement(args.placement)
    if final_placement not in GLOBAL_PROPOSAL_PLACEMENTS:
        raise SystemExit("Global proposals may use only skill_patch or personal_global_skill.")
    if final_placement == "skill_patch" and (
        not proposal.get("recommended_skill") or not proposal.get("recommended_skill_path")
    ):
        raise SystemExit(
            "skill_patch adoption requires a proposal with a concrete recommended Skill and path; "
            "revise the proposal first."
        )
    proposal["placement"] = final_placement
    if args.placement_reason:
        proposal["placement_reason"] = args.placement_reason
    applied_target = require_concrete_text(args.applied_target, "--applied-target")
    edit_summary = require_concrete_text(args.summary, "--summary")

    proposal["status"] = "applied"
    proposal["applied_at"] = utc_now()
    proposal["applied_target"] = applied_target
    save_global_proposals(args, proposals)

    cluster_state = read_global_clusters(args)
    cluster = cluster_state.get("clusters", {}).get(proposal["method_fingerprint"], {})
    cluster["status"] = "adopted"
    cluster_state["clusters"][proposal["method_fingerprint"]] = cluster
    write_global_clusters(cluster_state, args)

    adopt_record = {
        "id": make_id("gadopt"),
        "timestamp": utc_now(),
        "proposal_id": proposal["id"],
        "method_fingerprint": proposal["method_fingerprint"],
        "method_key": proposal.get("method_key", ""),
        "applied_target": applied_target,
        "edit_summary": edit_summary,
        "placement": proposal.get("placement", ""),
        "placement_reason": proposal.get("placement_reason", ""),
        "recommended_skill": proposal.get("recommended_skill", ""),
        "recommended_skill_path": proposal.get("recommended_skill_path", ""),
    }
    append_jsonl(adopted_global_path(args), adopt_record)
    print(json.dumps({"applied": True, "id": adopt_record["id"], "applied_target": applied_target}, ensure_ascii=False))


def command_global_reject(args: argparse.Namespace) -> None:
    ensure_global_runtime(args)
    proposals, proposal = get_global_proposal(args, args.proposal_id)
    if proposal.get("status") not in {"pending_user_gate", "needs_revision"}:
        raise SystemExit("Global proposal is not rejectable.")

    if args.revision:
        proposal["status"] = "needs_revision"
        proposal["revision_feedback"] = args.reason
        proposal["updated_at"] = utc_now()
        save_global_proposals(args, proposals)
        print(json.dumps({"revision_requested": True, "proposal_id": proposal["id"]}, ensure_ascii=False))
        return

    proposal["status"] = "rejected"
    proposal["rejected_at"] = utc_now()
    proposal["rejection_reason"] = args.reason
    save_global_proposals(args, proposals)

    cluster_state = read_global_clusters(args)
    cluster = cluster_state.get("clusters", {}).get(proposal["method_fingerprint"], {})
    cluster["status"] = "cooldown"
    cluster["cooldown_signal_remaining"] = COOLDOWN_SIGNAL_LIMIT
    cluster_state["clusters"][proposal["method_fingerprint"]] = cluster
    write_global_clusters(cluster_state, args)

    reject_record = {
        "id": make_id("grejprop"),
        "timestamp": utc_now(),
        "proposal_id": proposal["id"],
        "method_fingerprint": proposal["method_fingerprint"],
        "method_key": proposal.get("method_key", ""),
        "reason": args.reason,
        "cooldown_signal_remaining": cluster["cooldown_signal_remaining"],
        "evidence_global_signal_ids": proposal.get("evidence_global_signal_ids", []),
    }
    append_jsonl(rejected_global_path(args), reject_record)
    print(json.dumps({"rejected": True, "id": reject_record["id"]}, ensure_ascii=False))


def initialize_runtime(args: argparse.Namespace, quiet: bool = False) -> None:
    if is_skill_source_project(args) and not getattr(args, "allow_skill_source_runtime", False):
        raise SystemExit(
            "Current directory appears to be the Skill source directory. Runtime state should be created "
            "in the target project root, not the Skill source directory. To proceed anyway, use "
            "--allow-skill-source-runtime."
        )

    runtime = runtime_root(args)
    data = data_dir(args)
    data.mkdir(parents=True, exist_ok=True)

    for filename in JSONL_FILES:
        target = data / filename
        if target.exists():
            continue
        target.write_text("", encoding="utf-8")

    for filename in JSON_FILES:
        target = data / filename
        if target.exists():
            continue
        if filename == "cluster-state.json":
            write_json(target, default_cluster_state())
        else:
            write_json(target, default_state())

    state = read_state(args)
    write_state(args, state)
    clusters = read_cluster_state(args)
    write_cluster_state(args, clusters)

    if not quiet:
        print(f"Initialized runtime directory: {runtime}")


def command_init(args: argparse.Namespace) -> None:
    initialize_runtime(args)


def command_log_signal(args: argparse.Namespace) -> None:
    ensure_runtime(args, auto_init=getattr(args, "auto_init", False))
    operator = normalize_operator(args.operator)
    validate_cluster_key(args.cluster_key, operator)
    strength = clamp_strength(int(args.strength))
    signal_id = make_id("sig")
    signal = {
        "id": signal_id,
        "timestamp": utc_now(),
        "source_type": args.source_type,
        "summary": args.summary,
        "context": args.context,
        "operator": operator,
        "cluster_key": args.cluster_key,
        "strength": strength,
        "risk": args.risk or "",
        "status": "active",
        "immediate": bool(args.immediate),
    }
    for field in SIGNAL_CARD_FIELDS:
        value = compact_text(getattr(args, field, ""), limit=220)
        if value:
            signal[field] = value
    append_jsonl(data_dir(args) / "signals.jsonl", signal)
    cluster = update_cluster_for_signal(args, signal)
    state = read_state(args)
    state["total_signal_count"] = int(state.get("total_signal_count", 0)) + 1
    write_state(args, state)
    print(json.dumps({
        "logged": True,
        "id": signal_id,
        "cluster_key": args.cluster_key,
        "cluster_status": cluster.get("status"),
        "ready_reason": cluster.get("ready_reason", ""),
    }, ensure_ascii=False))


def command_list_clusters(args: argparse.Namespace) -> None:
    ensure_runtime(args)
    clusters = read_cluster_state(args).get("clusters", {})
    if not clusters:
        print("No signal clusters.")
        return
    for key in sorted(clusters):
        c = clusters[key]
        print(
            f"{key}  status={c.get('status')}  count={c.get('signal_count', 0)}  "
            f"strength={c.get('strength_sum', 0)}"
        )
        if c.get("ready_reason"):
            print(f"  ready_reason: {c.get('ready_reason')}")
        if c.get("cooldown_signal_remaining"):
            print(f"  cooldown_signal_remaining: {c.get('cooldown_signal_remaining', 0)}")


def find_signals_for_cluster(args: argparse.Namespace, cluster_key: str) -> list[dict]:
    signals = read_jsonl(data_dir(args) / "signals.jsonl")
    return [s for s in signals if s.get("cluster_key") == cluster_key and s.get("status") == "active"]


def command_propose(args: argparse.Namespace) -> None:
    ensure_runtime(args)
    cluster_state = read_cluster_state(args)
    clusters = cluster_state.get("clusters", {})
    cluster = clusters.get(args.cluster_key)
    if not cluster:
        raise SystemExit(f"Cluster not found: {args.cluster_key!r}")
    if cluster.get("status") == "cooldown" and cooldown_is_active(cluster):
        raise SystemExit(f"Cluster is in cooldown: {args.cluster_key}")
    if cluster.get("status") not in {"ready", "proposed"}:
        raise SystemExit("Cluster is not ready.")

    signals = find_signals_for_cluster(args, args.cluster_key)
    evidence = signals[-3:]
    skeleton = local_proposal_skeleton(cluster, signals, args)
    placement = normalize_placement(args.placement, skeleton.get("placement_hint", "project_rule"))
    placement_reason = args.placement_reason or skeleton.get("placement_reason", "")
    recommended_skill = args.recommended_skill or skeleton.get("recommended_skill", "")
    recommended_skill_path = args.recommended_skill_path or skeleton.get("recommended_skill_path", "")
    if placement == "skill_patch" and (not recommended_skill or not recommended_skill_path):
        raise SystemExit("skill_patch requires a concrete recommended local Skill and path.")
    if placement == "project_rule" and not skeleton.get("recommended_project_rule_file"):
        raise SystemExit("project_rule requires a concrete recommended project rule file.")
    target = require_concrete_text(args.target, "--target")
    patch = require_markdown_patch(args.patch)
    risk = require_concrete_text(args.risk, "--risk")
    proposal_id = make_id("prop")
    proposal = {
        "id": proposal_id,
        "timestamp": utc_now(),
        "cluster_key": args.cluster_key,
        "trigger": cluster.get("ready_reason", ""),
        "evidence_signal_ids": [s["id"] for s in evidence],
        "placement": placement,
        "placement_reason": placement_reason,
        "recommended_skill": recommended_skill,
        "recommended_skill_path": recommended_skill_path,
        "recommended_skill_reason": skeleton.get("recommended_skill_reason", ""),
        "agent_profile": skeleton.get("agent_profile", ""),
        "recommended_project_rule_file": skeleton.get("recommended_project_rule_file", ""),
        "recommended_project_rule_path": skeleton.get("recommended_project_rule_path", ""),
        "recommended_project_rule_reason": skeleton.get("recommended_project_rule_reason", ""),
        "project_rule_candidates": skeleton.get("project_rule_candidates", []),
        "target": target,
        "patch": patch,
        "risk": risk,
        "status": "pending_user_gate",
        "user_gate": PLACEMENT_USER_GATE,
    }
    append_jsonl(data_dir(args) / "proposals.jsonl", proposal)
    cluster["status"] = "proposed"
    cluster["last_proposal_id"] = proposal_id
    clusters[args.cluster_key] = cluster
    write_cluster_state(args, cluster_state)
    state = read_state(args)
    state["last_proposal_id"] = proposal_id
    write_state(args, state)

    evidence_text = "\n".join(f"- {s['id']}: {s.get('summary', '')}" for s in evidence) or "- No active signal evidence found."
    print(f"""## Skill Evolution Proposal

Trigger:
{proposal['trigger']}

Recommended placement:
{proposal['placement']}

Placement reason:
{proposal['placement_reason']}

Evidence:
{evidence_text}

Recommended local Skill:
{proposal['recommended_skill'] or '[none]'}

Recommended Skill path:
{proposal['recommended_skill_path'] or '[none]'}

Recommended project rule file:
{proposal['recommended_project_rule_file'] or '[none]'}

Project rule reason:
{proposal['recommended_project_rule_reason'] or '[none]'}

Target:
{proposal['target']}

Patch:
{proposal['patch']}

Risk:
{proposal['risk']}

User gate:
Choose: {PLACEMENT_USER_GATE}
Choosing a placement means accepting that placement.

Proposal ID:
{proposal_id}
""")


def load_proposals(args: argparse.Namespace) -> list[dict]:
    return read_jsonl(data_dir(args) / "proposals.jsonl")


def save_proposals(args: argparse.Namespace, proposals: list[dict]) -> None:
    write_jsonl(data_dir(args) / "proposals.jsonl", proposals)


def get_proposal(args: argparse.Namespace, proposal_id: str) -> tuple[list[dict], dict]:
    proposals = load_proposals(args)
    for proposal in proposals:
        if proposal.get("id") == proposal_id:
            return proposals, proposal
    raise SystemExit(f"Proposal not found: {proposal_id!r}")


def command_apply_proposal(args: argparse.Namespace) -> None:
    ensure_runtime(args)
    proposals, proposal = get_proposal(args, args.proposal_id)
    if proposal.get("status") != "pending_user_gate":
        raise SystemExit("Proposal is not pending user gate.")

    final_placement = normalize_placement(args.placement)
    if final_placement == "skill_patch" and (
        not proposal.get("recommended_skill") or not proposal.get("recommended_skill_path")
    ):
        raise SystemExit(
            "skill_patch adoption requires a proposal with a concrete recommended Skill and path; "
            "revise the proposal first."
        )
    if final_placement == "project_rule" and not proposal.get("recommended_project_rule_file"):
        raise SystemExit(
            "project_rule adoption requires a proposal with a concrete project rule file; "
            "revise the proposal first."
        )
    proposal["placement"] = final_placement
    if args.placement_reason:
        proposal["placement_reason"] = args.placement_reason
    applied_target = require_concrete_text(args.applied_target, "--applied-target")
    edit_summary = require_concrete_text(args.summary, "--summary")

    proposal["status"] = "applied"
    proposal["applied_at"] = utc_now()
    proposal["applied_target"] = applied_target
    save_proposals(args, proposals)

    cluster_state = read_cluster_state(args)
    cluster = cluster_state.get("clusters", {}).get(proposal["cluster_key"], {})
    cluster["status"] = "adopted"
    cluster_state["clusters"][proposal["cluster_key"]] = cluster
    write_cluster_state(args, cluster_state)

    adopt_record = {
        "id": make_id("adopt"),
        "timestamp": utc_now(),
        "proposal_id": proposal["id"],
        "cluster_key": proposal["cluster_key"],
        "applied_target": applied_target,
        "edit_summary": edit_summary,
        "placement": proposal.get("placement", ""),
        "placement_reason": proposal.get("placement_reason", ""),
        "recommended_skill": proposal.get("recommended_skill", ""),
        "recommended_skill_path": proposal.get("recommended_skill_path", ""),
        "agent_profile": proposal.get("agent_profile", ""),
        "recommended_project_rule_file": proposal.get("recommended_project_rule_file", ""),
        "recommended_project_rule_path": proposal.get("recommended_project_rule_path", ""),
        "recommended_project_rule_reason": proposal.get("recommended_project_rule_reason", ""),
    }
    append_jsonl(data_dir(args) / "adopted-edits.jsonl", adopt_record)

    state = read_state(args)
    state["adopted_edit_count"] = int(state.get("adopted_edit_count", 0)) + 1
    write_state(args, state)
    print(json.dumps({"applied": True, "id": adopt_record["id"], "applied_target": applied_target}, ensure_ascii=False))


def command_reject_proposal(args: argparse.Namespace) -> None:
    ensure_runtime(args)
    proposals, proposal = get_proposal(args, args.proposal_id)
    if proposal.get("status") not in {"pending_user_gate", "needs_revision"}:
        raise SystemExit("Proposal is not rejectable.")

    if args.revision:
        proposal["status"] = "needs_revision"
        proposal["revision_feedback"] = args.reason
        proposal["updated_at"] = utc_now()
        save_proposals(args, proposals)
        print(json.dumps({"revision_requested": True, "proposal_id": proposal["id"]}, ensure_ascii=False))
        return

    proposal["status"] = "rejected"
    proposal["rejected_at"] = utc_now()
    proposal["rejection_reason"] = args.reason
    save_proposals(args, proposals)

    cluster_state = read_cluster_state(args)
    cluster = cluster_state.get("clusters", {}).get(proposal["cluster_key"], {})
    cluster["status"] = "cooldown"
    cluster["cooldown_signal_remaining"] = COOLDOWN_SIGNAL_LIMIT
    cluster_state["clusters"][proposal["cluster_key"]] = cluster
    write_cluster_state(args, cluster_state)

    reject_record = {
        "id": make_id("rejprop"),
        "timestamp": utc_now(),
        "proposal_id": proposal["id"],
        "cluster_key": proposal["cluster_key"],
        "reason": args.reason,
        "cooldown_signal_remaining": cluster["cooldown_signal_remaining"],
        "evidence_signal_ids": proposal.get("evidence_signal_ids", []),
    }
    append_jsonl(data_dir(args) / "rejected-proposals.jsonl", reject_record)

    state = read_state(args)
    state["rejected_proposal_count"] = int(state.get("rejected_proposal_count", 0)) + 1
    write_state(args, state)
    print(json.dumps({"rejected": True, "id": reject_record["id"]}, ensure_ascii=False))


def command_status(args: argparse.Namespace) -> None:
    ensure_runtime(args)
    state = read_state(args)
    signals = read_jsonl(data_dir(args) / "signals.jsonl")
    proposals = read_jsonl(data_dir(args) / "proposals.jsonl")
    adopted = read_jsonl(data_dir(args) / "adopted-edits.jsonl")
    rejected_props = read_jsonl(data_dir(args) / "rejected-proposals.jsonl")
    clusters = read_cluster_state(args).get("clusters", {})
    counts = Counter(c.get("status", "unknown") for c in clusters.values())
    proposal_counts = Counter(p.get("status", "unknown") for p in proposals)

    print(f"{STATUS_LABELS['runtime']}: {runtime_root(args)}")
    print(f"{STATUS_LABELS['signals']}: {len(signals)}")
    print(f"{STATUS_LABELS['clusters']}: {len(clusters)}")
    print(f"  {STATUS_LABELS['active']}:   {counts.get('active', 0)}")
    print(f"  {STATUS_LABELS['ready']}:    {counts.get('ready', 0)}")
    print(f"  {STATUS_LABELS['proposed']}: {counts.get('proposed', 0)}")
    print(f"  {STATUS_LABELS['cooldown']}: {counts.get('cooldown', 0)}")
    print(f"{STATUS_LABELS['proposals']}: {len(proposals)}")
    print(f"  {STATUS_LABELS['pending_user_gate']}: {proposal_counts.get('pending_user_gate', 0)}")
    print(f"  {STATUS_LABELS['needs_revision']}:    {proposal_counts.get('needs_revision', 0)}")
    print(f"{STATUS_LABELS['adopted_skill_edits']}: {len(adopted)}")
    print(f"{STATUS_LABELS['rejected_proposals']}: {len(rejected_props)}")
    print(f"{STATUS_LABELS['last_proposal_id']}: {state.get('last_proposal_id', '')}")


def collect_runtime_summary(args: argparse.Namespace) -> dict:
    state = read_state(args)
    signals = read_jsonl(data_dir(args) / "signals.jsonl")
    proposals = read_jsonl(data_dir(args) / "proposals.jsonl")
    adopted = read_jsonl(data_dir(args) / "adopted-edits.jsonl")
    rejected_props = read_jsonl(data_dir(args) / "rejected-proposals.jsonl")
    clusters = read_cluster_state(args).get("clusters", {})
    cluster_counts = Counter(c.get("status", "unknown") for c in clusters.values())
    proposal_counts = Counter(p.get("status", "unknown") for p in proposals)
    signals_by_cluster: dict[str, list[dict]] = {}
    for signal in signals:
        if signal.get("status") == "active":
            signals_by_cluster.setdefault(signal.get("cluster_key", ""), []).append(signal)

    ready_clusters = []
    for key, cluster in sorted(clusters.items()):
        if cluster.get("status") == "ready":
            cluster_signals = signals_by_cluster.get(key, [])
            ready_clusters.append({
                "cluster_key": key,
                "operator": cluster.get("operator", ""),
                "signal_count": int(cluster.get("signal_count", 0)),
                "strength_sum": int(cluster.get("strength_sum", 0)),
                "ready_reason": cluster.get("ready_reason", ""),
                "samples": [compact_text(s.get("summary", ""), 140) for s in cluster_signals[-3:]],
                "skeleton": local_proposal_skeleton(cluster, cluster_signals, args),
            })

    pending_proposals = []
    for proposal in proposals:
        if proposal.get("status") in {"pending_user_gate", "needs_revision"}:
            pending_proposals.append({
                "proposal_id": proposal.get("id", ""),
                "cluster_key": proposal.get("cluster_key", ""),
                "placement": proposal.get("placement", ""),
                "recommended_skill": proposal.get("recommended_skill", ""),
                "recommended_project_rule_file": proposal.get("recommended_project_rule_file", ""),
                "status": proposal.get("status", ""),
                "target": proposal.get("target", ""),
            })

    return {
        "runtime": str(runtime_root(args)),
        "signals": len(signals),
        "clusters": len(clusters),
        "cluster_counts": dict(cluster_counts),
        "proposals": len(proposals),
        "proposal_counts": dict(proposal_counts),
        "adopted_skill_edits": len(adopted),
        "rejected_proposals": len(rejected_props),
        "last_proposal_id": state.get("last_proposal_id", ""),
        "ready_clusters": ready_clusters,
        "pending_proposals": pending_proposals,
    }


def command_cycle(args: argparse.Namespace) -> None:
    initialized = False
    if not runtime_exists(args):
        if args.no_init:
            raise SystemExit("Runtime directory not initialized. Run without --no-init to create it.")
        initialize_runtime(args, quiet=True)
        initialized = True
    else:
        migrate_local_runtime(args)

    summary = collect_runtime_summary(args)
    summary["initialized"] = initialized
    write_state(args, read_state(args))
    if not getattr(args, "no_global", False):
        import_result = import_local_signals_to_global(args)
        summary["global"] = collect_global_summary(args, import_result)

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        pending_gate = bool(summary["pending_proposals"] or (
            summary.get("global") and summary["global"]["pending_proposals"]
        ))
        if getattr(args, "fail_on_pending_gate", False) and pending_gate:
            raise SystemExit(2)
        return

    state_label = STATUS_LABELS["created"] if initialized else STATUS_LABELS["ready_state"]
    print(f"{STATUS_LABELS['runtime']}: {summary['runtime']} ({state_label})")
    print(
        "{signals_label}: {signals} | {clusters_label}: {clusters} | {ready_label}: {ready} | {pending_label}: {pending}".format(
            signals_label=STATUS_LABELS["signals"],
            signals=summary["signals"],
            clusters_label=STATUS_LABELS["clusters"],
            clusters=summary["clusters"],
            ready_label=STATUS_LABELS["ready"],
            ready=summary["cluster_counts"].get("ready", 0),
            pending_label=STATUS_LABELS["pending_gates"],
            pending=summary["proposal_counts"].get("pending_user_gate", 0),
        )
    )

    global_summary = summary.get("global")
    if global_summary:
        print(
            "{global_label}: {imported_label} {imported} | {projects_label} {projects} | "
            "{clusters_label} {clusters} | {ready_label} {ready} | {pending_label} {pending}".format(
                global_label=STATUS_LABELS["global"],
                imported_label=STATUS_LABELS["imported"],
                imported=global_summary["imported"],
                projects_label=STATUS_LABELS["projects"],
                projects=global_summary["projects"],
                clusters_label=STATUS_LABELS["clusters"],
                clusters=global_summary["clusters"],
                ready_label=STATUS_LABELS["ready"],
                ready=global_summary["cluster_counts"].get("ready", 0),
                pending_label=STATUS_LABELS["pending_gates"],
                pending=global_summary["proposal_counts"].get("pending_user_gate", 0),
            )
        )

    if summary["pending_proposals"]:
        print("\nPending user gates:")
        for proposal in summary["pending_proposals"]:
            print(
                f"- {proposal['proposal_id']}  status={proposal['status']}  "
                f"placement={proposal.get('placement', '')}  "
                f"cluster={proposal['cluster_key']}"
            )
            if proposal.get("recommended_skill"):
                print(f"  recommended_skill: {proposal.get('recommended_skill')}")

    if global_summary and global_summary["pending_proposals"]:
        print("\nPending global user gates:")
        for proposal in global_summary["pending_proposals"]:
            print(
                f"- {proposal['proposal_id']}  status={proposal['status']}  "
                f"placement={proposal.get('placement', '')}  "
                f"method={proposal['method_fingerprint']}"
            )
            if proposal.get("recommended_skill"):
                print(f"  recommended_skill: {proposal.get('recommended_skill')}")

    if summary["ready_clusters"]:
        print("\nReady clusters:")
        for cluster in summary["ready_clusters"]:
            print(
                f"- {cluster['cluster_key']}  count={cluster['signal_count']}  "
                f"strength={cluster['strength_sum']}  reason={cluster['ready_reason']}"
            )
            skeleton = cluster.get("skeleton", {})
            if skeleton:
                print(f"  placement_hint: {skeleton.get('placement_hint', '')}")
                print(f"  placement_reason: {skeleton.get('placement_reason', '')}")
                if skeleton.get("recommended_skill"):
                    print(f"  recommended_skill: {skeleton.get('recommended_skill', '')}")
                    print(f"  recommended_skill_path: {skeleton.get('recommended_skill_path', '')}")
                if skeleton.get("recommended_project_rule_file"):
                    print(f"  agent_profile: {skeleton.get('agent_profile', '')}")
                    print(f"  recommended_project_rule_file: {skeleton.get('recommended_project_rule_file', '')}")
                    print(f"  recommended_project_rule_reason: {skeleton.get('recommended_project_rule_reason', '')}")
                print(f"  target_hint: {skeleton.get('target_hint', '')}")
                print(f"  patch_hint: {skeleton.get('patch_hint', '')}")
                print(f"  risk_hint: {skeleton.get('risk_hint', '')}")
        print(
            "\nNext: run `propose` with the refined skeleton, then ask the user to choose "
            f"{PLACEMENT_USER_GATE}."
        )

    if global_summary and global_summary["ready_clusters"]:
        print("\nReady global clusters:")
        for cluster in global_summary["ready_clusters"]:
            print(
                f"- {cluster['method_fingerprint']}  projects={cluster['project_count']}  "
                f"evidence={cluster['evidence_count']}  strength={cluster['strength_sum']}  "
                f"method={cluster['method_key']}"
            )
            skeleton = cluster.get("skeleton", {})
            if skeleton:
                print(f"  placement_hint: {skeleton.get('placement_hint', '')}")
                print(f"  placement_reason: {skeleton.get('placement_reason', '')}")
                if skeleton.get("recommended_skill"):
                    print(f"  recommended_skill: {skeleton.get('recommended_skill', '')}")
                    print(f"  recommended_skill_path: {skeleton.get('recommended_skill_path', '')}")
                print(f"  target_hint: {skeleton.get('target_hint', '')}")
                print(f"  patch_hint: {skeleton.get('patch_hint', '')}")
                print(f"  risk_hint: {skeleton.get('risk_hint', '')}")
        print(
            "\nNext: run `global-propose` with the refined skeleton, then ask the user to choose "
            f"{GLOBAL_USER_GATE}."
        )
    elif not summary["pending_proposals"] and not summary["ready_clusters"] and not (
        global_summary and (global_summary["pending_proposals"] or global_summary["ready_clusters"])
    ):
        print("\nNext: continue the task; log only clear reusable methodology signals.")

    pending_gate = bool(summary["pending_proposals"] or (
        global_summary and global_summary["pending_proposals"]
    ))
    if getattr(args, "fail_on_pending_gate", False) and pending_gate:
        raise SystemExit(2)


def command_validate(args: argparse.Namespace) -> None:
    ensure_runtime(args)
    errors: list[str] = []
    data = data_dir(args)

    required_by_file = {
        "signals.jsonl": ["id", "timestamp", "source_type", "summary", "context", "operator", "cluster_key", "strength", "status"],
        "proposals.jsonl": ["id", "timestamp", "cluster_key", "trigger", "evidence_signal_ids", "target", "patch", "risk", "status", "placement"],
        "adopted-edits.jsonl": ["id", "timestamp", "proposal_id", "applied_target", "edit_summary", "placement"],
        "rejected-proposals.jsonl": ["id", "timestamp", "proposal_id", "cluster_key", "reason", "cooldown_signal_remaining"],
    }

    signal_ids: set[str] = set()
    cluster_keys: set[str] = set(read_cluster_state(args).get("clusters", {}).keys())

    for filename, required_fields in required_by_file.items():
        path = data / filename
        try:
            records = read_jsonl(path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        for index, record in enumerate(records, 1):
            for field in required_fields:
                if field not in record:
                    errors.append(f"{path}:{index}: missing required field '{field}'")

            if filename == "signals.jsonl":
                signal_ids.add(record.get("id", ""))
                if record.get("source_type") not in SOURCE_TYPES:
                    errors.append(f"{path}:{index}: invalid source_type: {record.get('source_type')!r}")
                op = record.get("operator")
                if op not in VALID_OPERATOR_IDS:
                    errors.append(f"{path}:{index}: invalid operator: {op!r}")
                if not str(record.get("cluster_key", "")).startswith(f"{op}:"):
                    errors.append(f"{path}:{index}: cluster_key must start with operator prefix")
                try:
                    strength = int(record.get("strength"))
                    if strength < 1 or strength > 3:
                        errors.append(f"{path}:{index}: strength must be 1..3")
                except (TypeError, ValueError):
                    errors.append(f"{path}:{index}: invalid strength")
                if record.get("status") not in SIGNAL_STATUSES:
                    errors.append(f"{path}:{index}: invalid signal status: {record.get('status')!r}")
                for field in SIGNAL_CARD_FIELDS:
                    if field in record and not isinstance(record.get(field), str):
                        errors.append(f"{path}:{index}: {field} must be a string")
                if "confidence" in record:
                    errors.append(f"{path}:{index}: removed field 'confidence'")

            if filename == "proposals.jsonl":
                if record.get("cluster_key") not in cluster_keys:
                    errors.append(f"{path}:{index}: proposal references missing cluster_key")
                if "decision" in record:
                    errors.append(f"{path}:{index}: removed field 'decision'")
                if record.get("placement") not in PROPOSAL_PLACEMENTS:
                    errors.append(f"{path}:{index}: invalid placement: {record.get('placement')!r}")
                if record.get("status") not in PROPOSAL_STATUSES:
                    errors.append(f"{path}:{index}: invalid proposal status: {record.get('status')!r}")
                if record.get("status") in {"pending_user_gate", "needs_revision"}:
                    if not str(record.get("target", "")).strip() or str(record.get("target", "")).startswith("["):
                        errors.append(f"{path}:{index}: target must be concrete")
                    if not re.search(r"(?m)^#{1,6}\s+\S", str(record.get("patch", ""))):
                        errors.append(f"{path}:{index}: patch must be a complete Markdown block")
                    if not str(record.get("risk", "")).strip() or str(record.get("risk", "")).startswith("["):
                        errors.append(f"{path}:{index}: risk must be concrete")
                    if record.get("placement") == "skill_patch" and (
                        not record.get("recommended_skill") or not record.get("recommended_skill_path")
                    ):
                        errors.append(f"{path}:{index}: skill_patch requires recommended Skill and path")
                    if record.get("placement") == "project_rule" and not record.get("recommended_project_rule_file"):
                        errors.append(f"{path}:{index}: project_rule requires recommended project rule file")
                for sid in record.get("evidence_signal_ids", []):
                    if sid not in signal_ids:
                        errors.append(f"{path}:{index}: proposal references missing signal id: {sid}")

            for removed_field in ["cooldown_until", "applied_path", "write_status", "target_skill"]:
                if removed_field in record:
                    errors.append(f"{path}:{index}: removed field '{removed_field}'")

    _validate_cluster_state(args, signal_ids, errors)
    _validate_state(args, errors)
    if global_runtime_exists(args):
        _validate_global_runtime(args, errors)

    if (data / "crystallized-operators.jsonl").exists():
        errors.append(f"{data / 'crystallized-operators.jsonl'}: removed operator seed file still exists")

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"  - {error}")
        raise SystemExit(1)
    print("Validation passed.")


def _validate_global_runtime(args: argparse.Namespace, errors: list[str]) -> None:
    ensure_global_runtime(args)
    data = global_data_dir(args)
    try:
        state = read_global_state(args)
        if state.get("schema_version") != "2.0":
            errors.append(f"{global_state_path(args)}: schema_version must be 2.0")
    except Exception as exc:
        errors.append(f"{global_state_path(args)}: invalid JSON: {exc}")
    required_by_file = {
        "global-signals.jsonl": [
            "id", "timestamp", "project_hash", "source_signal_id", "dedupe_key",
            "method_fingerprint", "method_key", "operator", "summary", "source_type",
            "strength", "status",
        ],
        "global-proposals.jsonl": [
            "id", "timestamp", "method_fingerprint", "trigger", "evidence_global_signal_ids",
            "target", "patch", "risk", "status", "placement",
        ],
        "adopted-global-edits.jsonl": ["id", "timestamp", "proposal_id", "applied_target", "edit_summary", "placement"],
        "rejected-global-proposals.jsonl": ["id", "timestamp", "proposal_id", "method_fingerprint", "reason", "cooldown_signal_remaining"],
    }

    global_signal_ids: set[str] = set()
    cluster_keys: set[str] = set(read_global_clusters(args).get("clusters", {}).keys())
    for filename, required_fields in required_by_file.items():
        path = data / filename
        try:
            records = read_jsonl(path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        for index, record in enumerate(records, 1):
            for field in required_fields:
                if field not in record:
                    errors.append(f"{path}:{index}: missing required field '{field}'")
            if filename == "global-signals.jsonl":
                global_signal_ids.add(record.get("id", ""))
                if record.get("operator") not in VALID_OPERATOR_IDS:
                    errors.append(f"{path}:{index}: invalid operator: {record.get('operator')!r}")
                try:
                    strength = int(record.get("strength"))
                    if strength < 1 or strength > 3:
                        errors.append(f"{path}:{index}: strength must be 1..3")
                except (TypeError, ValueError):
                    errors.append(f"{path}:{index}: invalid strength")
                if record.get("status") != "active":
                    errors.append(f"{path}:{index}: invalid status: {record.get('status')!r}")
                for field in SIGNAL_CARD_FIELDS + ["method_signature"]:
                    if field in record and not isinstance(record.get(field), str):
                        errors.append(f"{path}:{index}: {field} must be a string")
                if "confidence" in record:
                    errors.append(f"{path}:{index}: removed field 'confidence'")
            if filename == "global-proposals.jsonl":
                if record.get("method_fingerprint") not in cluster_keys:
                    errors.append(f"{path}:{index}: proposal references missing method_fingerprint")
                if "decision" in record:
                    errors.append(f"{path}:{index}: removed field 'decision'")
                if record.get("placement") not in GLOBAL_PROPOSAL_PLACEMENTS:
                    errors.append(f"{path}:{index}: invalid placement: {record.get('placement')!r}")
                if record.get("status") not in PROPOSAL_STATUSES:
                    errors.append(f"{path}:{index}: invalid proposal status: {record.get('status')!r}")
                if record.get("status") in {"pending_user_gate", "needs_revision"}:
                    if not str(record.get("target", "")).strip() or str(record.get("target", "")).startswith("["):
                        errors.append(f"{path}:{index}: target must be concrete")
                    if not re.search(r"(?m)^#{1,6}\s+\S", str(record.get("patch", ""))):
                        errors.append(f"{path}:{index}: patch must be a complete Markdown block")
                    if not str(record.get("risk", "")).strip() or str(record.get("risk", "")).startswith("["):
                        errors.append(f"{path}:{index}: risk must be concrete")
                    if record.get("placement") == "skill_patch" and (
                        not record.get("recommended_skill") or not record.get("recommended_skill_path")
                    ):
                        errors.append(f"{path}:{index}: skill_patch requires recommended Skill and path")
                for sid in record.get("evidence_global_signal_ids", []):
                    if sid not in global_signal_ids:
                        errors.append(f"{path}:{index}: proposal references missing global signal id: {sid}")
            for removed_field in ["cooldown_until", "applied_path", "write_status", "target_skill"]:
                if removed_field in record:
                    errors.append(f"{path}:{index}: removed field '{removed_field}'")

    _validate_global_clusters(args, global_signal_ids, errors)
    _validate_project_index(args, errors)


def _validate_global_clusters(args: argparse.Namespace, global_signal_ids: set[str], errors: list[str]) -> None:
    path = global_cluster_path(args)
    try:
        state = read_global_clusters(args)
    except Exception as exc:
        errors.append(f"{path}: invalid JSON: {exc}")
        return
    clusters = state.get("clusters")
    if state.get("schema_version") != "2.0":
        errors.append(f"{path}: schema_version must be 2.0")
    if not isinstance(clusters, dict):
        errors.append(f"{path}: clusters must be object")
        return
    for fingerprint, cluster in clusters.items():
        for field in [
            "method_fingerprint", "method_key", "operator", "evidence_count", "strength_sum",
            "project_hashes", "sample_global_signal_ids", "status",
        ]:
            if field not in cluster:
                errors.append(f"{path}:{fingerprint}: missing field '{field}'")
        if cluster.get("method_fingerprint") != fingerprint:
            errors.append(f"{path}:{fingerprint}: method_fingerprint mismatch")
        if cluster.get("operator") not in VALID_OPERATOR_IDS:
            errors.append(f"{path}:{fingerprint}: invalid operator")
        if cluster.get("status") not in CLUSTER_STATUSES:
            errors.append(f"{path}:{fingerprint}: invalid status")
        if "cooldown_until" in cluster:
            errors.append(f"{path}:{fingerprint}: removed field 'cooldown_until'")
        if not isinstance(cluster.get("project_hashes", []), list):
            errors.append(f"{path}:{fingerprint}: project_hashes must be list")
        for sid in cluster.get("sample_global_signal_ids", []):
            if sid not in global_signal_ids:
                errors.append(f"{path}:{fingerprint}: sample_global_signal_ids references missing global signal id: {sid}")


def _validate_project_index(args: argparse.Namespace, errors: list[str]) -> None:
    path = project_index_path(args)
    try:
        state = read_project_index(args)
    except Exception as exc:
        errors.append(f"{path}: invalid JSON: {exc}")
        return
    projects = state.get("projects")
    if state.get("schema_version") != "2.0":
        errors.append(f"{path}: schema_version must be 2.0")
    if not isinstance(projects, dict):
        errors.append(f"{path}: projects must be object")
        return
    for project_hash, project in projects.items():
        for field in ["project_hash", "identity_source", "first_seen", "last_seen", "imported_signal_count"]:
            if field not in project:
                errors.append(f"{path}:{project_hash}: missing field '{field}'")
        if project.get("project_hash") != project_hash:
            errors.append(f"{path}:{project_hash}: project_hash mismatch")


def _validate_cluster_state(args: argparse.Namespace, signal_ids: set[str], errors: list[str]) -> None:
    path = cluster_path(args)
    try:
        state = read_cluster_state(args)
    except Exception as exc:
        errors.append(f"{path}: invalid JSON: {exc}")
        return
    clusters = state.get("clusters")
    if state.get("schema_version") != "3.0":
        errors.append(f"{path}: schema_version must be 3.0")
    if not isinstance(clusters, dict):
        errors.append(f"{path}: clusters must be object")
        return
    for key, cluster in clusters.items():
        for field in ["cluster_key", "operator", "signal_count", "strength_sum", "sample_signal_ids", "last_seen", "status"]:
            if field not in cluster:
                errors.append(f"{path}:{key}: missing field '{field}'")
        if cluster.get("cluster_key") != key:
            errors.append(f"{path}:{key}: cluster_key mismatch")
        if cluster.get("operator") not in VALID_OPERATOR_IDS:
            errors.append(f"{path}:{key}: invalid operator")
        if cluster.get("status") not in CLUSTER_STATUSES:
            errors.append(f"{path}:{key}: invalid status")
        if "cooldown_until" in cluster:
            errors.append(f"{path}:{key}: removed field 'cooldown_until'")
        for sid in cluster.get("sample_signal_ids", []):
            if sid not in signal_ids:
                errors.append(f"{path}:{key}: sample_signal_ids references missing signal id: {sid}")


def _validate_state(args: argparse.Namespace, errors: list[str]) -> None:
    sp = state_path(args)
    try:
        state = read_state(args)
        if state.get("schema_version") != "3.0":
            errors.append(f"{sp}: schema_version must be 3.0")
        for field in ["schema_version", "total_signal_count", "adopted_edit_count", "rejected_proposal_count", "updated_at"]:
            if field not in state:
                errors.append(f"{sp}: missing field '{field}'")
    except Exception as exc:
        errors.append(f"{sp}: invalid JSON: {exc}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="jinhua local ledger CLI")
    parser.add_argument("--project-root", default=".", help="Project root. Defaults to current directory.")
    parser.add_argument(
        "--project-id",
        default="",
        help=(
            "Override global project identity. Use a stable project or conversation key when one "
            "workspace contains unrelated projects. The value is hashed before storage."
        ),
    )
    parser.add_argument("--runtime-dir", default="", help="Override runtime directory. Defaults to .jinhua.")
    parser.add_argument(
        "--global-runtime-dir",
        default="",
        help="Override global promotion directory. Defaults to the Skill's global-data directory.",
    )
    parser.add_argument(
        "--agent-profile",
        default="",
        help="Project-rule target profile: codex, claude, copilot, trae, hermes, openclaw, workbuddy, or generic.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize runtime directory")
    init_parser.add_argument("--allow-skill-source-runtime", action="store_true")
    init_parser.set_defaults(func=command_init)

    cycle_parser = subparsers.add_parser("cycle", help="Initialize if needed and print closed-loop next actions")
    cycle_parser.add_argument("--no-init", action="store_true", help="Fail instead of creating a missing runtime directory")
    cycle_parser.add_argument("--allow-skill-source-runtime", action="store_true")
    cycle_parser.add_argument("--json", action="store_true", help="Emit machine-readable status")
    cycle_parser.add_argument("--no-global", action="store_true", help="Skip automatic global promotion scan")
    cycle_parser.add_argument(
        "--fail-on-pending-gate",
        action="store_true",
        help="Exit 2 when local or global pending user gates are present.",
    )
    cycle_parser.set_defaults(func=command_cycle)

    global_cycle_parser = subparsers.add_parser("global-cycle", help="Import local signals and print global promotion state")
    global_cycle_parser.add_argument("--json", action="store_true", help="Emit machine-readable status")
    global_cycle_parser.add_argument(
        "--fail-on-pending-gate",
        action="store_true",
        help="Exit 2 when pending user gates are present.",
    )
    global_cycle_parser.set_defaults(func=command_global_cycle)

    classify_parser = subparsers.add_parser("classify-input", help="Classify user correction state for the trigger layer")
    classify_parser.add_argument("--text", default="", help="User message to classify. Defaults to stdin.")
    classify_parser.add_argument("--json", action="store_true", help="Emit machine-readable result")
    classify_parser.set_defaults(func=command_classify_input)

    codex_prompt_parser = subparsers.add_parser(
        "codex-user-prompt-submit",
        help="Codex UserPromptSubmit trigger gate: local correction classifier only",
    )
    codex_prompt_parser.add_argument("--text", default="", help="Prompt text for tests. Defaults to stdin JSON.")
    codex_prompt_parser.add_argument("--pretty", action="store_true", help="Pretty-print hook JSON output.")
    codex_prompt_parser.set_defaults(func=command_codex_user_prompt_submit)

    codex_post_tool_parser = subparsers.add_parser(
        "codex-post-tool-use",
        help="Codex PostToolUse trigger gate: record jinhua invocations for duplicate protection",
    )
    codex_post_tool_parser.add_argument("--pretty", action="store_true", help="Pretty-print hook JSON output.")
    codex_post_tool_parser.set_defaults(func=command_codex_post_tool_use)

    guard_parser = subparsers.add_parser("guard", help="Run the jinhua invocation guard")
    guard_parser.add_argument("--session-id", default="")
    guard_parser.add_argument("--turn-id", default="")
    guard_parser.add_argument("--source", default="manual")
    guard_parser.add_argument("--reason", default="")
    guard_parser.add_argument("--entry", default="")
    guard_parser.add_argument("--mark", action="store_true")
    guard_parser.add_argument("--pretty", action="store_true")
    guard_parser.set_defaults(func=command_guard)

    signal_parser = subparsers.add_parser("log-signal", help="Record a model-detected methodology signal")
    signal_parser.add_argument("--source-type", required=True, choices=SOURCE_TYPES)
    signal_parser.add_argument("--summary", required=True)
    signal_parser.add_argument("--operator", required=True)
    signal_parser.add_argument("--cluster-key", required=True)
    signal_parser.add_argument("--context", required=True)
    signal_parser.add_argument("--strength", type=int, default=1)
    signal_parser.add_argument("--risk", default="")
    signal_parser.add_argument("--trigger", default="", help="Reusable condition that made the method relevant")
    signal_parser.add_argument("--action", default="", help="Reusable method action, phrased as an imperative")
    signal_parser.add_argument("--transfer-conditions", default="", help="Where this method transfers across tasks/projects")
    signal_parser.add_argument("--negative-cases", default="", help="When this method should not be used")
    signal_parser.add_argument("--verification-path", default="", help="How the method should be checked")
    signal_parser.add_argument("--immediate", action="store_true")
    signal_parser.add_argument("--auto-init", action="store_true", help="Create runtime state first if it is missing")
    signal_parser.set_defaults(func=command_log_signal)

    subparsers.add_parser("list-clusters", help="List signal clusters").set_defaults(func=command_list_clusters)

    propose_parser = subparsers.add_parser("propose", help="Create a user-gated evolution proposal for a ready cluster")
    propose_parser.add_argument("--cluster-key", required=True)
    propose_parser.add_argument("--placement", default="", choices=sorted(PROPOSAL_PLACEMENTS))
    propose_parser.add_argument("--placement-reason", default="")
    propose_parser.add_argument("--recommended-skill", default="")
    propose_parser.add_argument("--recommended-skill-path", default="")
    propose_parser.add_argument("--target", required=True)
    propose_parser.add_argument("--patch", required=True)
    propose_parser.add_argument("--risk", required=True)
    propose_parser.set_defaults(func=command_propose)

    apply_parser = subparsers.add_parser("apply-proposal", help="Record an accepted proposal after the agent edits and verifies the target")
    apply_parser.add_argument("--proposal-id", required=True)
    apply_parser.add_argument("--placement", required=True, choices=sorted(PROPOSAL_PLACEMENTS))
    apply_parser.add_argument("--applied-target", required=True)
    apply_parser.add_argument("--summary", required=True)
    apply_parser.add_argument("--placement-reason", default="")
    apply_parser.set_defaults(func=command_apply_proposal)

    reject_parser = subparsers.add_parser("reject-proposal", help="Reject a proposal or mark it for revision")
    reject_parser.add_argument("--proposal-id", required=True)
    reject_parser.add_argument("--reason", required=True)
    reject_parser.add_argument("--revision", action="store_true", help="Treat reason as user revision feedback")
    reject_parser.set_defaults(func=command_reject_proposal)

    global_propose_parser = subparsers.add_parser(
        "global-propose",
        help="Create a user-gated proposal for a ready cross-project method cluster",
    )
    global_propose_parser.add_argument("--method-fingerprint", required=True)
    global_propose_parser.add_argument("--placement", default="", choices=sorted(GLOBAL_PROPOSAL_PLACEMENTS))
    global_propose_parser.add_argument("--placement-reason", default="")
    global_propose_parser.add_argument("--recommended-skill", default="")
    global_propose_parser.add_argument("--recommended-skill-path", default="")
    global_propose_parser.add_argument("--target", required=True)
    global_propose_parser.add_argument("--patch", required=True)
    global_propose_parser.add_argument("--risk", required=True)
    global_propose_parser.set_defaults(func=command_global_propose)

    global_apply_parser = subparsers.add_parser("global-apply", help="Record an accepted global proposal after the agent edits and verifies the target")
    global_apply_parser.add_argument("--proposal-id", required=True)
    global_apply_parser.add_argument("--placement", required=True, choices=sorted(GLOBAL_PROPOSAL_PLACEMENTS))
    global_apply_parser.add_argument("--applied-target", required=True)
    global_apply_parser.add_argument("--summary", required=True)
    global_apply_parser.add_argument("--placement-reason", default="")
    global_apply_parser.set_defaults(func=command_global_apply)

    global_reject_parser = subparsers.add_parser("global-reject", help="Reject a global proposal or mark it for revision")
    global_reject_parser.add_argument("--proposal-id", required=True)
    global_reject_parser.add_argument("--reason", required=True)
    global_reject_parser.add_argument("--revision", action="store_true", help="Treat reason as user revision feedback")
    global_reject_parser.set_defaults(func=command_global_reject)

    subparsers.add_parser("status", help="Print runtime state").set_defaults(func=command_status)
    subparsers.add_parser("global-status", help="Print global promotion state").set_defaults(func=command_global_status)
    subparsers.add_parser("validate", help="Validate runtime JSON/JSONL data").set_defaults(func=command_validate)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
