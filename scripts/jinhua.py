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
import shutil
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
    "crystallized-operators.jsonl",
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

SIGNAL_STATUSES = {"active", "compacted", "ignored"}
CLUSTER_STATUSES = {"active", "ready", "proposed", "adopted", "cooldown"}
PROPOSAL_STATUSES = {"pending_user_gate", "applied", "rejected", "needs_revision"}
PROPOSAL_DECISIONS = {
    "proposed_edit",
    "crystallize_experience",
    "merge_rule",
    "experimental_operator",
    "core_operator_promotion",
    "reject",
}
PROPOSAL_PLACEMENTS = {
    "project_rule",
    "skill_patch",
    "personal_global_skill",
}
PLACEMENT_USER_GATE = (
    "project_rule(Yes) / skill_patch(Yes) / personal_global_skill(Yes) / No / Revision"
)
OPERATOR_TIERS = {"core", "experimental", "deprecated", "none"}
SCORE_KEYS = [
    "problem_representation",
    "knowledge_access",
    "search_path",
    "constraint_recognition",
    "candidate_comparison",
    "failure_prediction",
    "compression",
]

SIGNAL_COUNT_THRESHOLD = 3
SIGNAL_STRENGTH_THRESHOLD = 5
COOLDOWN_DAYS = 7
COOLDOWN_SIGNAL_LIMIT = 5
GLOBAL_PROJECT_THRESHOLD = 3
GLOBAL_EVIDENCE_THRESHOLD = 5
GLOBAL_STRENGTH_THRESHOLD = 7
GLOBAL_FAST_PROJECT_THRESHOLD = 2
GLOBAL_FAST_STRENGTH_THRESHOLD = 6
DEFAULT_RUNTIME_DIR_NAME = ".jinhua"

WAKE_POSITIVE_PATTERNS = [
    r"\bjinhua(?:\.skill)?\b",
    r"\b(skill|tool|procedure|workflow|verification|reasoning|methodology)\b.*\b(trigger|wake|activate|route|call|load|select|missed|should have)\b",
    r"\b(trigger|wake|activate|route|call|load|select|missed|should have)\b.*\b(skill|tool|procedure|workflow|verification|reasoning|methodology)\b",
    r"\b(remember|crystallize|preserve|generalize|write|save)\b.*\b(skill|rule|practice|method|workflow|procedure|agents\.md|claude\.md)\b",
    r"\b(next time|future|from now on|going forward)\b.*\b(should|must|always|never|verify|check|use|run|call)\b",
    r"\bshould have\b.*\b(verified|checked|used|called|run|triggered|loaded|selected)\b",
    r"\b(verify|check|use|call|run|trigger|load|select)\b.*\bbefore\b.*\b(answering|finishing|claiming|recommending)\b",
    r"为什么.*(没|沒有|没有|未).*(触发|调用|唤醒|啟動|启动|執行|执行)",
    r"(应该|應該|本该|本應|需要).*(触发|调用|唤醒|啟動|启动|執行|执行).*(skill|工具|流程|jinhua)",
    r"(以后|下次|今后|往后).*(应该|應該|必须|一定|先|记住|沉淀|写进)",
    r"(工作流|流程|验证|驗證|推理|工具|skill|技能|规则|規則).*(不对|不對|错了|錯了|漏了|没做|沒做|应该|應該)",
    r"(应该|應該|必须|一定|先).*(验证|驗證|检查|檢查|确认|確認).*(再|后|後).*(回答|完成|判断|判斷|推荐|推薦)",
]

WAKE_NEGATIVE_PATTERNS = [
    r"^\s*(no|不是|不对|不對|错了|錯了)[，,:\s]+.{0,80}$",
    r"\b(page|slide|line|row|column|cell|chapter|section)\s+\d+",
    r"\btypo\b|\bspelling\b|\bgrammar\b",
    r"(页|頁|行|列|段|章|节|節|幻灯片|投影片)\s*\d+",
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


def apply_text_patch(target: Path, patch: str, insert_after: str = "") -> str:
    text = target.read_text(encoding="utf-8")
    block = patch.strip()
    if block in text:
        return "already_present"

    if insert_after:
        marker = insert_after.strip()
        index = text.find(marker)
        if index == -1:
            raise SystemExit(f"Insert marker not found: {marker!r}")
        insert_at = index + len(marker)
        text = text[:insert_at].rstrip() + "\n\n" + block + "\n\n" + text[insert_at:].lstrip()
    else:
        text = text.rstrip() + "\n\n" + block + "\n"

    with target.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return "written"


def validate_skill_write_target(args: argparse.Namespace, target: Path) -> None:
    allowed_roots = [
        project_root(args),
        codex_home() / "skills",
        skill_root(),
    ]
    if not any(path_is_relative_to(target, root.resolve()) for root in allowed_roots):
        raise SystemExit("Target must be under project root, CODEX_HOME/skills, or this Skill root.")

    lower_parts = {part.lower() for part in target.parts}
    if target.name == "SKILL.md":
        return
    if "references" in lower_parts and target.suffix.lower() == ".md":
        return
    raise SystemExit("apply may only write SKILL.md or references/*.md")


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
        "schema_version": "2.0",
        "last_proposal_id": "",
        "total_signal_count": 0,
        "adopted_edit_count": 0,
        "rejected_proposal_count": 0,
        "updated_at": "",
    }


def default_cluster_state() -> dict:
    return {"schema_version": "2.0", "clusters": {}, "updated_at": ""}


def default_global_state() -> dict:
    return {
        "schema_version": "1.0",
        "last_scan_at": "",
        "last_scan_project_count": 0,
        "last_scan_signal_count": 0,
        "last_ready_cluster_count": 0,
        "last_proposal_id": "",
        "updated_at": "",
    }


def default_global_cluster_state() -> dict:
    return {"schema_version": "1.0", "clusters": {}, "updated_at": ""}


def default_project_index() -> dict:
    return {"schema_version": "1.0", "projects": {}, "updated_at": ""}


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


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if records:
        text = "\n".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in records) + "\n"
    else:
        text = ""
    path.write_text(text, encoding="utf-8")


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def read_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return dict(default)
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def regex_hits(patterns: list[str], text: str) -> list[str]:
    return [pattern for pattern in patterns if re.search(pattern, text, flags=re.I)]


def read_state(args: argparse.Namespace) -> dict:
    state = default_state()
    state.update(read_json(state_path(args), default_state()))
    if state.get("schema_version") == "1.1":
        state["schema_version"] = "2.0"
    return state


def write_state(args: argparse.Namespace, state: dict) -> None:
    clean_state = default_state()
    for key in clean_state:
        if key in state:
            clean_state[key] = state[key]
    clean_state["schema_version"] = "2.0"
    clean_state["updated_at"] = utc_now()
    write_json(state_path(args), clean_state)


def read_cluster_state(args: argparse.Namespace) -> dict:
    state = default_cluster_state()
    state.update(read_json(cluster_path(args), default_cluster_state()))
    state.setdefault("clusters", {})
    return state


def write_cluster_state(args: argparse.Namespace, state: dict) -> None:
    state["schema_version"] = "2.0"
    state["updated_at"] = utc_now()
    write_json(cluster_path(args), state)


def read_global_state(args: argparse.Namespace | None = None) -> dict:
    state = default_global_state()
    state.update(read_json(global_state_path(args), default_global_state()))
    return state


def write_global_state(state: dict, args: argparse.Namespace | None = None) -> None:
    state["schema_version"] = "1.0"
    state["updated_at"] = utc_now()
    write_json(global_state_path(args), state)


def read_global_clusters(args: argparse.Namespace | None = None) -> dict:
    state = default_global_cluster_state()
    state.update(read_json(global_cluster_path(args), default_global_cluster_state()))
    state.setdefault("clusters", {})
    return state


def write_global_clusters(state: dict, args: argparse.Namespace | None = None) -> None:
    state["schema_version"] = "1.0"
    state["updated_at"] = utc_now()
    write_json(global_cluster_path(args), state)


def read_project_index(args: argparse.Namespace | None = None) -> dict:
    state = default_project_index()
    state.update(read_json(project_index_path(args), default_project_index()))
    state.setdefault("projects", {})
    return state


def write_project_index(state: dict, args: argparse.Namespace | None = None) -> None:
    state["schema_version"] = "1.0"
    state["updated_at"] = utc_now()
    write_json(project_index_path(args), state)


def runtime_exists(args: argparse.Namespace) -> bool:
    return data_dir(args).exists() and state_path(args).exists()


def ensure_runtime(args: argparse.Namespace, auto_init: bool = False) -> None:
    if not runtime_exists(args):
        if auto_init:
            initialize_runtime(args, quiet=True)
            return
        raise SystemExit("Runtime directory not initialized. Run: jinhua.py init")


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


def clamp_confidence(value: float | None) -> float | None:
    if value is None:
        return None
    if value < 0 or value > 1:
        raise SystemExit("--confidence must be between 0 and 1")
    return round(float(value), 3)


def cooldown_is_active(cluster: dict) -> bool:
    until = parse_utc(cluster.get("cooldown_until", ""))
    if until and until > datetime.now(timezone.utc):
        return True
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


def cluster_tokens(cluster: dict) -> set[str]:
    parts = [cluster.get("method_key", "")]
    parts.extend(cluster.get("summary_samples", []))
    parts.extend(cluster.get("method_signature_samples", []))
    tokens: set[str] = set()
    for part in parts:
        tokens.update(method_words(part))
    return tokens


def jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


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
        "cooldown_until": "",
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
    if signal.get("confidence") is not None:
        record["confidence"] = signal.get("confidence")
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
        "cooldown_until": "",
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
                "decision": proposal.get("decision", ""),
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

    print(f"Global runtime: {summary['global_runtime']}")
    print(
        "Imported: {imported} | Projects: {projects} | Global signals: {signals} | "
        "Clusters: {clusters} | Ready: {ready} | Pending gates: {pending}".format(
            imported=summary["imported"],
            projects=summary["projects"],
            signals=summary["global_signals"],
            clusters=summary["clusters"],
            ready=summary["cluster_counts"].get("ready", 0),
            pending=summary["proposal_counts"].get("pending_user_gate", 0),
        )
    )

    if summary["pending_proposals"]:
        print("\nPending global user gates:")
        for proposal in summary["pending_proposals"]:
            print(
                f"- {proposal['proposal_id']}  status={proposal['status']}  "
                f"decision={proposal['decision']}  placement={proposal.get('placement', '')}  "
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
    print(f"Global runtime: {summary['global_runtime']}")
    print(f"Projects: {summary['projects']}")
    print(f"Global signals: {summary['global_signals']}")
    print(f"Global clusters: {summary['clusters']}")
    print(f"  active:   {summary['cluster_counts'].get('active', 0)}")
    print(f"  ready:    {summary['cluster_counts'].get('ready', 0)}")
    print(f"  proposed: {summary['cluster_counts'].get('proposed', 0)}")
    print(f"  cooldown: {summary['cluster_counts'].get('cooldown', 0)}")
    print(f"Global proposals: {summary['global_proposals']}")
    print(f"  pending user gate: {summary['proposal_counts'].get('pending_user_gate', 0)}")
    print(f"  needs revision:    {summary['proposal_counts'].get('needs_revision', 0)}")
    print(f"Adopted global edits: {summary['adopted_global_edits']}")
    print(f"Rejected global proposals: {summary['rejected_global_proposals']}")


def command_global_merge_suggestions(args: argparse.Namespace) -> None:
    ensure_global_runtime(args)
    clusters = read_global_clusters(args).get("clusters", {})
    candidates = []
    items = [
        (fingerprint, cluster)
        for fingerprint, cluster in sorted(clusters.items())
        if cluster.get("status") not in {"adopted", "cooldown"}
    ]
    token_cache = {fingerprint: cluster_tokens(cluster) for fingerprint, cluster in items}
    for left_index, (left_fp, left_cluster) in enumerate(items):
        for right_fp, right_cluster in items[left_index + 1:]:
            if left_cluster.get("operator") != right_cluster.get("operator"):
                continue
            score = jaccard(token_cache[left_fp], token_cache[right_fp])
            if score < args.min_similarity:
                continue
            overlap = sorted(token_cache[left_fp] & token_cache[right_fp])[:12]
            candidates.append({
                "left": left_fp,
                "right": right_fp,
                "operator": left_cluster.get("operator", ""),
                "similarity": round(score, 3),
                "left_method": left_cluster.get("method_key", ""),
                "right_method": right_cluster.get("method_key", ""),
                "shared_terms": overlap,
                "recommendation": "merge_candidate",
                "safety": "review only; this command never mutates global clusters",
            })
    candidates.sort(key=lambda item: item["similarity"], reverse=True)
    candidates = candidates[: max(0, args.limit)]
    if args.json:
        print(json.dumps({"merge_suggestions": candidates}, ensure_ascii=False, indent=2))
        return
    if not candidates:
        print("No global merge suggestions.")
        return
    print("Global merge suggestions:")
    for item in candidates:
        print(
            f"- {item['left']} <-> {item['right']}  "
            f"similarity={item['similarity']}  operator={item['operator']}"
        )
        print(f"  left:  {item['left_method']}")
        print(f"  right: {item['right_method']}")
        print(f"  shared_terms: {', '.join(item['shared_terms'])}")
        print("  action: review before any merge proposal; no files were changed.")


def wake_check_result(text: str) -> dict:
    normalized = " ".join(str(text or "").strip().split()).lower()
    positive = regex_hits(WAKE_POSITIVE_PATTERNS, normalized)
    negative = regex_hits(WAKE_NEGATIVE_PATTERNS, normalized)
    should_route = bool(positive) and not (negative and len(positive) == 1 and "jinhua" not in normalized)
    if should_route:
        reason = "meta-workflow correction or Skill-evolution cue"
    elif negative:
        reason = "likely task-local correction"
    else:
        reason = "no reusable workflow cue"
    return {
        "should_route": should_route,
        "reason": reason,
        "positive_matches": positive[:3],
        "negative_matches": negative[:3],
        "next_command": "cycle" if should_route else "",
    }


def command_wake_check(args: argparse.Namespace) -> None:
    if args.text:
        text = args.text
    else:
        text = sys.stdin.read()
    result = wake_check_result(text)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"should_route: {str(result['should_route']).lower()}")
        print(f"reason: {result['reason']}")
        if result["next_command"]:
            print(f"next: {result['next_command']}")
    if args.exit_code and not result["should_route"]:
        raise SystemExit(1)


def command_global_propose(args: argparse.Namespace) -> None:
    ensure_global_runtime(args)
    cluster_state = read_global_clusters(args)
    clusters = cluster_state.get("clusters", {})
    cluster = clusters.get(args.method_fingerprint)
    if not cluster:
        raise SystemExit(f"Global cluster not found: {args.method_fingerprint!r}")
    if cluster.get("status") == "cooldown" and cooldown_is_active(cluster):
        raise SystemExit(f"Global cluster is in cooldown: {args.method_fingerprint}")
    if cluster.get("status") not in {"ready", "proposed"} and not args.force:
        raise SystemExit("Global cluster is not ready. Use --force only for an explicit immediate trigger.")

    records_by_id = {record.get("id", ""): record for record in read_jsonl(global_signal_path(args))}
    sample_records = [
        records_by_id[sid]
        for sid in cluster.get("sample_global_signal_ids", [])
        if sid in records_by_id
    ]
    skeleton = global_proposal_skeleton(cluster, sample_records, args)
    placement = normalize_placement(args.placement, skeleton.get("placement_hint", "personal_global_skill"))
    placement_reason = args.placement_reason or skeleton.get("placement_reason", "")
    recommended_skill = args.recommended_skill or skeleton.get("recommended_skill", "")
    recommended_skill_path = args.recommended_skill_path or skeleton.get("recommended_skill_path", "")
    target = args.target or skeleton.get("target_hint", "") or "[target Skill / file / insertion location]"

    proposal_id = make_id("gprop")
    proposal = {
        "id": proposal_id,
        "timestamp": utc_now(),
        "method_fingerprint": args.method_fingerprint,
        "method_key": cluster.get("method_key", ""),
        "operator": cluster.get("operator", ""),
        "decision": args.decision,
        "trigger": cluster.get("ready_reason") or "forced immediate global proposal",
        "evidence_global_signal_ids": list(cluster.get("sample_global_signal_ids", []))[-3:],
        "placement": placement,
        "placement_reason": placement_reason,
        "recommended_skill": recommended_skill,
        "recommended_skill_path": recommended_skill_path,
        "recommended_skill_reason": skeleton.get("recommended_skill_reason", ""),
        "target": target,
        "patch": args.patch or "[1-3 sentence patch or structured operator definition]",
        "risk": args.risk or "[main risk or side effect]",
        "project_count": len(set(cluster.get("project_hashes", []))),
        "evidence_count": int(cluster.get("evidence_count", 0)),
        "strength_sum": int(cluster.get("strength_sum", 0)),
        "status": "pending_user_gate",
        "user_gate": PLACEMENT_USER_GATE,
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

Decision:
{proposal['decision']}

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
Choose: Project Rule / Skill Patch / Personal Global Skill / No / Revision
(Choosing a placement counts as Yes for that placement.)

Proposal ID:
{proposal_id}
""")


def command_global_apply(args: argparse.Namespace) -> None:
    ensure_global_runtime(args)
    proposals, proposal = get_global_proposal(args, args.proposal_id)
    if proposal.get("status") != "pending_user_gate" and not args.force:
        raise SystemExit("Global proposal is not pending user gate. Use --force to override.")

    final_placement = normalize_placement(args.placement, proposal.get("placement", ""))
    if args.placement:
        proposal["placement"] = final_placement
    if args.placement_reason:
        proposal["placement_reason"] = args.placement_reason

    applied_path = ""
    write_status = ""
    if args.target_skill_path:
        target = Path(args.target_skill_path).resolve()
        if not target.exists():
            raise SystemExit(f"Target file not found: {target}")
        validate_skill_write_target(args, target)
        patch = args.patch or proposal.get("patch", "")
        if not patch or patch.startswith("["):
            raise SystemExit("No concrete patch content supplied. Provide --patch.")
        write_status = apply_text_patch(target, patch, args.insert_after)
        applied_path = str(target)

    proposal["status"] = "applied"
    proposal["applied_at"] = utc_now()
    proposal["applied_path"] = applied_path
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
        "target_skill": args.target_skill or proposal.get("target", ""),
        "edit_summary": args.summary or proposal.get("patch", "")[:160],
        "decision": proposal.get("decision", ""),
        "placement": proposal.get("placement", ""),
        "placement_reason": proposal.get("placement_reason", ""),
        "recommended_skill": proposal.get("recommended_skill", ""),
        "recommended_skill_path": proposal.get("recommended_skill_path", ""),
        "applied_path": applied_path,
        "write_status": write_status,
    }
    append_jsonl(adopted_global_path(args), adopt_record)
    print(json.dumps({"applied": True, "id": adopt_record["id"], "applied_path": applied_path}, ensure_ascii=False))


def command_global_reject(args: argparse.Namespace) -> None:
    ensure_global_runtime(args)
    proposals, proposal = get_global_proposal(args, args.proposal_id)
    if proposal.get("status") not in {"pending_user_gate", "needs_revision"} and not args.force:
        raise SystemExit("Global proposal is not rejectable. Use --force to override.")

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
    cluster["cooldown_until"] = (datetime.now(timezone.utc) + timedelta(days=args.cooldown_days)).replace(
        microsecond=0
    ).isoformat().replace("+00:00", "Z")
    cluster["cooldown_signal_remaining"] = args.cooldown_signals
    cluster_state["clusters"][proposal["method_fingerprint"]] = cluster
    write_global_clusters(cluster_state, args)

    reject_record = {
        "id": make_id("grejprop"),
        "timestamp": utc_now(),
        "proposal_id": proposal["id"],
        "method_fingerprint": proposal["method_fingerprint"],
        "method_key": proposal.get("method_key", ""),
        "reason": args.reason,
        "cooldown_until": cluster["cooldown_until"],
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

    seed_data = skill_root() / "data"
    for filename in JSONL_FILES:
        target = data / filename
        if target.exists():
            continue
        source = seed_data / filename
        if filename == "crystallized-operators.jsonl" and source.exists():
            shutil.copyfile(source, target)
        else:
            target.write_text("", encoding="utf-8")

    for filename in JSON_FILES:
        target = data / filename
        if target.exists():
            continue
        source = seed_data / filename
        if source.exists():
            shutil.copyfile(source, target)
        elif filename == "cluster-state.json":
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
    confidence = clamp_confidence(getattr(args, "confidence", None))
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
    if confidence is not None:
        signal["confidence"] = confidence
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
        if c.get("cooldown_until") or c.get("cooldown_signal_remaining"):
            print(f"  cooldown_until: {c.get('cooldown_until', '')}  "
                  f"cooldown_signal_remaining: {c.get('cooldown_signal_remaining', 0)}")


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
    if cluster.get("status") not in {"ready", "proposed"} and not args.force:
        raise SystemExit("Cluster is not ready. Use --force only when the model has an explicit immediate trigger.")

    signals = find_signals_for_cluster(args, args.cluster_key)
    evidence = signals[-3:]
    skeleton = local_proposal_skeleton(cluster, signals, args)
    placement = normalize_placement(args.placement, skeleton.get("placement_hint", "project_rule"))
    placement_reason = args.placement_reason or skeleton.get("placement_reason", "")
    recommended_skill = args.recommended_skill or skeleton.get("recommended_skill", "")
    recommended_skill_path = args.recommended_skill_path or skeleton.get("recommended_skill_path", "")
    target = args.target or skeleton.get("target_hint", "") or "[target Skill / file / insertion location]"
    proposal_id = make_id("prop")
    proposal = {
        "id": proposal_id,
        "timestamp": utc_now(),
        "cluster_key": args.cluster_key,
        "decision": args.decision,
        "trigger": cluster.get("ready_reason") or "forced immediate proposal",
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
        "patch": args.patch or "[1-3 sentence patch or structured operator definition]",
        "risk": args.risk or "[main risk or side effect]",
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

Decision:
{proposal['decision']}

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
Choose: Project Rule / Skill Patch / Personal Global Skill / No / Revision
(Choosing a placement counts as Yes for that placement.)

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
    if proposal.get("status") != "pending_user_gate" and not args.force:
        raise SystemExit("Proposal is not pending user gate. Use --force to override.")

    final_placement = normalize_placement(args.placement, proposal.get("placement", ""))
    if args.placement:
        proposal["placement"] = final_placement
    if args.placement_reason:
        proposal["placement_reason"] = args.placement_reason

    applied_path = ""
    write_status = ""
    if args.target_skill_path:
        target = Path(args.target_skill_path).resolve()
        if not target.exists():
            raise SystemExit(f"Target file not found: {target}")
        validate_skill_write_target(args, target)
        patch = args.patch or proposal.get("patch", "")
        if not patch or patch.startswith("["):
            raise SystemExit("No concrete patch content supplied. Provide --patch.")
        write_status = apply_text_patch(target, patch, args.insert_after)
        applied_path = str(target)

    proposal["status"] = "applied"
    proposal["applied_at"] = utc_now()
    proposal["applied_path"] = applied_path
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
        "target_skill": args.target_skill or proposal.get("target", ""),
        "edit_summary": args.summary or proposal.get("patch", "")[:160],
        "decision": proposal.get("decision", ""),
        "placement": proposal.get("placement", ""),
        "placement_reason": proposal.get("placement_reason", ""),
        "recommended_skill": proposal.get("recommended_skill", ""),
        "recommended_skill_path": proposal.get("recommended_skill_path", ""),
        "agent_profile": proposal.get("agent_profile", ""),
        "recommended_project_rule_file": proposal.get("recommended_project_rule_file", ""),
        "recommended_project_rule_path": proposal.get("recommended_project_rule_path", ""),
        "recommended_project_rule_reason": proposal.get("recommended_project_rule_reason", ""),
        "applied_path": applied_path,
        "write_status": write_status,
    }
    append_jsonl(data_dir(args) / "adopted-edits.jsonl", adopt_record)

    state = read_state(args)
    state["adopted_edit_count"] = int(state.get("adopted_edit_count", 0)) + 1
    write_state(args, state)
    print(json.dumps({"applied": True, "id": adopt_record["id"], "applied_path": applied_path}, ensure_ascii=False))


def command_reject_proposal(args: argparse.Namespace) -> None:
    ensure_runtime(args)
    proposals, proposal = get_proposal(args, args.proposal_id)
    if proposal.get("status") not in {"pending_user_gate", "needs_revision"} and not args.force:
        raise SystemExit("Proposal is not rejectable. Use --force to override.")

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
    cluster["cooldown_until"] = (datetime.now(timezone.utc) + timedelta(days=args.cooldown_days)).replace(
        microsecond=0
    ).isoformat().replace("+00:00", "Z")
    cluster["cooldown_signal_remaining"] = args.cooldown_signals
    cluster_state["clusters"][proposal["cluster_key"]] = cluster
    write_cluster_state(args, cluster_state)

    reject_record = {
        "id": make_id("rejprop"),
        "timestamp": utc_now(),
        "proposal_id": proposal["id"],
        "cluster_key": proposal["cluster_key"],
        "reason": args.reason,
        "cooldown_until": cluster["cooldown_until"],
        "cooldown_signal_remaining": cluster["cooldown_signal_remaining"],
        "evidence_signal_ids": proposal.get("evidence_signal_ids", []),
    }
    append_jsonl(data_dir(args) / "rejected-proposals.jsonl", reject_record)

    state = read_state(args)
    state["rejected_proposal_count"] = int(state.get("rejected_proposal_count", 0)) + 1
    write_state(args, state)
    print(json.dumps({"rejected": True, "id": reject_record["id"]}, ensure_ascii=False))


def command_compact(args: argparse.Namespace) -> None:
    ensure_runtime(args)
    signals_path = data_dir(args) / "signals.jsonl"
    signals = read_jsonl(signals_path)
    cluster_state = read_cluster_state(args)
    sample_ids: set[str] = set()
    for cluster in cluster_state.get("clusters", {}).values():
        sample_ids.update(cluster.get("sample_signal_ids", []))
    retained: list[dict] = []
    compacted = 0
    for signal in signals:
        if signal.get("id") in sample_ids or signal.get("strength", 1) >= args.keep_strength_at_least:
            retained.append(signal)
        else:
            compacted += 1
    if not args.dry_run:
        write_jsonl(signals_path, retained)
    print(json.dumps({"dry_run": args.dry_run, "retained": len(retained), "compacted": compacted}, ensure_ascii=False))


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

    print(f"Runtime: {runtime_root(args)}")
    print(f"Signals: {len(signals)}")
    print(f"Clusters: {len(clusters)}")
    print(f"  active:   {counts.get('active', 0)}")
    print(f"  ready:    {counts.get('ready', 0)}")
    print(f"  proposed: {counts.get('proposed', 0)}")
    print(f"  cooldown: {counts.get('cooldown', 0)}")
    print(f"Proposals: {len(proposals)}")
    print(f"  pending user gate: {proposal_counts.get('pending_user_gate', 0)}")
    print(f"  needs revision:    {proposal_counts.get('needs_revision', 0)}")
    print(f"Adopted Skill edits: {len(adopted)}")
    print(f"Rejected proposals: {len(rejected_props)}")
    print(f"Last proposal ID: {state.get('last_proposal_id', '')}")


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
                "decision": proposal.get("decision", ""),
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

    state_label = "created" if initialized else "ready"
    print(f"Runtime: {summary['runtime']} ({state_label})")
    print(
        "Signals: {signals} | Clusters: {clusters} | Ready: {ready} | Pending gates: {pending}".format(
            signals=summary["signals"],
            clusters=summary["clusters"],
            ready=summary["cluster_counts"].get("ready", 0),
            pending=summary["proposal_counts"].get("pending_user_gate", 0),
        )
    )

    global_summary = summary.get("global")
    if global_summary:
        print(
            "Global: Imported {imported} | Projects {projects} | Clusters {clusters} | "
            "Ready {ready} | Pending gates {pending}".format(
                imported=global_summary["imported"],
                projects=global_summary["projects"],
                clusters=global_summary["clusters"],
                ready=global_summary["cluster_counts"].get("ready", 0),
                pending=global_summary["proposal_counts"].get("pending_user_gate", 0),
            )
        )

    if summary["pending_proposals"]:
        print("\nPending user gates:")
        for proposal in summary["pending_proposals"]:
            print(
                f"- {proposal['proposal_id']}  status={proposal['status']}  "
                f"decision={proposal['decision']}  placement={proposal.get('placement', '')}  "
                f"cluster={proposal['cluster_key']}"
            )
            if proposal.get("recommended_skill"):
                print(f"  recommended_skill: {proposal.get('recommended_skill')}")

    if global_summary and global_summary["pending_proposals"]:
        print("\nPending global user gates:")
        for proposal in global_summary["pending_proposals"]:
            print(
                f"- {proposal['proposal_id']}  status={proposal['status']}  "
                f"decision={proposal['decision']}  placement={proposal.get('placement', '')}  "
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
            "Project Rule / Skill Patch / Personal Global Skill / No / Revision."
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
            "Skill Patch / Personal Global Skill / No / Revision."
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
        "proposals.jsonl": ["id", "timestamp", "cluster_key", "decision", "trigger", "evidence_signal_ids", "target", "patch", "risk", "status"],
        "adopted-edits.jsonl": ["id", "timestamp"],
        "rejected-proposals.jsonl": ["id", "timestamp", "proposal_id", "cluster_key", "reason"],
        "crystallized-operators.jsonl": ["id", "name", "type", "record_status", "operator_tier", "four_gates", "intelligence_score", "score_evidence"],
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
                    try:
                        confidence = float(record.get("confidence"))
                        if confidence < 0 or confidence > 1:
                            errors.append(f"{path}:{index}: confidence must be 0..1")
                    except (TypeError, ValueError):
                        errors.append(f"{path}:{index}: invalid confidence")

            if filename == "proposals.jsonl":
                if record.get("cluster_key") not in cluster_keys:
                    errors.append(f"{path}:{index}: proposal references missing cluster_key")
                if record.get("decision") not in PROPOSAL_DECISIONS:
                    errors.append(f"{path}:{index}: invalid decision: {record.get('decision')!r}")
                if "placement" in record and record.get("placement") not in PROPOSAL_PLACEMENTS:
                    errors.append(f"{path}:{index}: invalid placement: {record.get('placement')!r}")
                if record.get("status") not in PROPOSAL_STATUSES:
                    errors.append(f"{path}:{index}: invalid proposal status: {record.get('status')!r}")
                for sid in record.get("evidence_signal_ids", []):
                    if sid not in signal_ids:
                        errors.append(f"{path}:{index}: proposal references missing signal id: {sid}")

            if filename == "crystallized-operators.jsonl":
                if record.get("record_status") not in {"crystallized", "candidate", "proven", "rejected", "merged"}:
                    errors.append(f"{path}:{index}: unexpected record_status for crystallized-operators")
                if record.get("operator_tier") not in OPERATOR_TIERS:
                    errors.append(f"{path}:{index}: invalid operator_tier: {record.get('operator_tier')!r}")
                _validate_four_gates(record, path, index, errors)
                _validate_score_evidence(record, path, index, errors)

    _validate_cluster_state(args, signal_ids, errors)
    _validate_state(args, errors)
    if global_runtime_exists(args):
        _validate_global_runtime(args, errors)

    crystallized_path = data / "crystallized-operators.jsonl"
    try:
        crystallized = read_jsonl(crystallized_path)
        core_ids = {item.get("id") for item in crystallized if item.get("operator_tier") == "core"}
        missing_core = [oid for oid in CORE_OPERATOR_IDS if oid not in core_ids]
        if missing_core:
            errors.append(f"missing required core operators: {', '.join(missing_core)}")
    except ValueError:
        pass

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"  - {error}")
        raise SystemExit(1)
    print("Validation passed.")


def _validate_global_runtime(args: argparse.Namespace, errors: list[str]) -> None:
    ensure_global_runtime(args)
    data = global_data_dir(args)
    required_by_file = {
        "global-signals.jsonl": [
            "id", "timestamp", "project_hash", "source_signal_id", "dedupe_key",
            "method_fingerprint", "method_key", "operator", "summary", "source_type",
            "strength", "status",
        ],
        "global-proposals.jsonl": [
            "id", "timestamp", "method_fingerprint", "decision", "trigger",
            "evidence_global_signal_ids", "target", "patch", "risk", "status",
        ],
        "adopted-global-edits.jsonl": ["id", "timestamp"],
        "rejected-global-proposals.jsonl": ["id", "timestamp", "proposal_id", "method_fingerprint", "reason"],
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
                if record.get("status") not in {"active", "compacted"}:
                    errors.append(f"{path}:{index}: invalid status: {record.get('status')!r}")
                for field in SIGNAL_CARD_FIELDS + ["method_signature"]:
                    if field in record and not isinstance(record.get(field), str):
                        errors.append(f"{path}:{index}: {field} must be a string")
                if "confidence" in record:
                    try:
                        confidence = float(record.get("confidence"))
                        if confidence < 0 or confidence > 1:
                            errors.append(f"{path}:{index}: confidence must be 0..1")
                    except (TypeError, ValueError):
                        errors.append(f"{path}:{index}: invalid confidence")
            if filename == "global-proposals.jsonl":
                if record.get("method_fingerprint") not in cluster_keys:
                    errors.append(f"{path}:{index}: proposal references missing method_fingerprint")
                if record.get("decision") not in PROPOSAL_DECISIONS:
                    errors.append(f"{path}:{index}: invalid decision: {record.get('decision')!r}")
                if "placement" in record and record.get("placement") not in PROPOSAL_PLACEMENTS:
                    errors.append(f"{path}:{index}: invalid placement: {record.get('placement')!r}")
                if record.get("status") not in PROPOSAL_STATUSES:
                    errors.append(f"{path}:{index}: invalid proposal status: {record.get('status')!r}")
                for sid in record.get("evidence_global_signal_ids", []):
                    if sid not in global_signal_ids:
                        errors.append(f"{path}:{index}: proposal references missing global signal id: {sid}")

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
        for sid in cluster.get("sample_signal_ids", []):
            if sid not in signal_ids:
                errors.append(f"{path}:{key}: sample_signal_ids references missing signal id: {sid}")


def _validate_state(args: argparse.Namespace, errors: list[str]) -> None:
    sp = state_path(args)
    try:
        state = read_state(args)
        for field in ["schema_version", "total_signal_count", "adopted_edit_count", "rejected_proposal_count", "updated_at"]:
            if field not in state:
                errors.append(f"{sp}: missing field '{field}'")
    except Exception as exc:
        errors.append(f"{sp}: invalid JSON: {exc}")


def _validate_four_gates(record: dict, path: Path, index: int, errors: list[str]) -> None:
    gates = record.get("four_gates")
    if gates is None:
        return
    for gate in ["abstraction", "transfer", "intelligence", "compression"]:
        value = gates.get(gate) if isinstance(gates, dict) else None
        if not isinstance(value, dict) or "passed" not in value or not value.get("reason"):
            errors.append(f"{path}:{index}: invalid four_gates.{gate}")


def _validate_score_evidence(record: dict, path: Path, index: int, errors: list[str]) -> None:
    score = record.get("intelligence_score")
    if not isinstance(score, dict):
        return
    evidence = record.get("score_evidence", {})
    counter = record.get("counter_evidence", {})
    if not isinstance(evidence, dict):
        errors.append(f"{path}:{index}: score_evidence must be object")
        return
    if counter and not isinstance(counter, dict):
        errors.append(f"{path}:{index}: counter_evidence must be object")
        return
    for key in SCORE_KEYS:
        try:
            value = int(score.get(key, 0))
        except (TypeError, ValueError):
            errors.append(f"{path}:{index}: invalid intelligence_score.{key}")
            continue
        if value > 0 and not evidence.get(key):
            errors.append(f"{path}:{index}: missing score_evidence.{key} (non-zero score requires evidence)")
        if value == 2 and not counter.get(key):
            errors.append(f"{path}:{index}: missing counter_evidence.{key} (2-point score requires counter evidence)")
    expected = sum(int(score.get(key, 0)) for key in SCORE_KEYS)
    if int(score.get("total", expected)) != expected:
        errors.append(f"{path}:{index}: intelligence_score.total mismatch")


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

    wake_parser = subparsers.add_parser("wake-check", help="Cheap read-only check for whether jinhua should be routed")
    wake_parser.add_argument("--text", default="", help="User message to classify. Defaults to stdin.")
    wake_parser.add_argument("--json", action="store_true", help="Emit machine-readable routing result")
    wake_parser.add_argument("--exit-code", action="store_true", help="Exit 0 when routed, 1 when skipped.")
    wake_parser.set_defaults(func=command_wake_check)

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
    signal_parser.add_argument("--confidence", type=float, default=None, help="Optional 0..1 model confidence for ranking only")
    signal_parser.add_argument("--immediate", action="store_true")
    signal_parser.add_argument("--auto-init", action="store_true", help="Create runtime state first if it is missing")
    signal_parser.set_defaults(func=command_log_signal)

    subparsers.add_parser("list-clusters", help="List signal clusters").set_defaults(func=command_list_clusters)

    propose_parser = subparsers.add_parser("propose", help="Create a user-gated evolution proposal for a ready cluster")
    propose_parser.add_argument("--cluster-key", required=True)
    propose_parser.add_argument("--decision", default="proposed_edit", choices=sorted(PROPOSAL_DECISIONS))
    propose_parser.add_argument("--placement", default="", choices=sorted(PROPOSAL_PLACEMENTS))
    propose_parser.add_argument("--placement-reason", default="")
    propose_parser.add_argument("--recommended-skill", default="")
    propose_parser.add_argument("--recommended-skill-path", default="")
    propose_parser.add_argument("--target", default="")
    propose_parser.add_argument("--patch", default="")
    propose_parser.add_argument("--risk", default="")
    propose_parser.add_argument("--force", action="store_true")
    propose_parser.set_defaults(func=command_propose)

    apply_parser = subparsers.add_parser("apply-proposal", help="Apply or record an accepted proposal after user says yes")
    apply_parser.add_argument("--proposal-id", required=True)
    apply_parser.add_argument("--target-skill", default="")
    apply_parser.add_argument("--summary", default="")
    apply_parser.add_argument("--placement", default="", choices=sorted(PROPOSAL_PLACEMENTS))
    apply_parser.add_argument("--placement-reason", default="")
    apply_parser.add_argument("--target-skill-path", default="")
    apply_parser.add_argument("--patch", default="")
    apply_parser.add_argument("--insert-after", default="", help="Insert patch after this exact marker instead of appending")
    apply_parser.add_argument("--force", action="store_true")
    apply_parser.set_defaults(func=command_apply_proposal)

    reject_parser = subparsers.add_parser("reject-proposal", help="Reject a proposal or mark it for revision")
    reject_parser.add_argument("--proposal-id", required=True)
    reject_parser.add_argument("--reason", required=True)
    reject_parser.add_argument("--revision", action="store_true", help="Treat reason as user revision feedback")
    reject_parser.add_argument("--cooldown-days", type=int, default=COOLDOWN_DAYS)
    reject_parser.add_argument("--cooldown-signals", type=int, default=COOLDOWN_SIGNAL_LIMIT)
    reject_parser.add_argument("--force", action="store_true")
    reject_parser.set_defaults(func=command_reject_proposal)

    global_propose_parser = subparsers.add_parser(
        "global-propose",
        help="Create a user-gated proposal for a ready cross-project method cluster",
    )
    global_propose_parser.add_argument("--method-fingerprint", required=True)
    global_propose_parser.add_argument("--decision", default="proposed_edit", choices=sorted(PROPOSAL_DECISIONS))
    global_propose_parser.add_argument("--placement", default="", choices=sorted(PROPOSAL_PLACEMENTS))
    global_propose_parser.add_argument("--placement-reason", default="")
    global_propose_parser.add_argument("--recommended-skill", default="")
    global_propose_parser.add_argument("--recommended-skill-path", default="")
    global_propose_parser.add_argument("--target", default="")
    global_propose_parser.add_argument("--patch", default="")
    global_propose_parser.add_argument("--risk", default="")
    global_propose_parser.add_argument("--force", action="store_true")
    global_propose_parser.set_defaults(func=command_global_propose)

    merge_parser = subparsers.add_parser(
        "global-merge-suggestions",
        help="Suggest similar global method clusters without modifying data",
    )
    merge_parser.add_argument("--min-similarity", type=float, default=0.45)
    merge_parser.add_argument("--limit", type=int, default=10)
    merge_parser.add_argument("--json", action="store_true", help="Emit machine-readable suggestions")
    merge_parser.set_defaults(func=command_global_merge_suggestions)

    global_apply_parser = subparsers.add_parser("global-apply", help="Apply or record an accepted global proposal")
    global_apply_parser.add_argument("--proposal-id", required=True)
    global_apply_parser.add_argument("--target-skill", default="")
    global_apply_parser.add_argument("--summary", default="")
    global_apply_parser.add_argument("--placement", default="", choices=sorted(PROPOSAL_PLACEMENTS))
    global_apply_parser.add_argument("--placement-reason", default="")
    global_apply_parser.add_argument("--target-skill-path", default="")
    global_apply_parser.add_argument("--patch", default="")
    global_apply_parser.add_argument("--insert-after", default="", help="Insert patch after this exact marker instead of appending")
    global_apply_parser.add_argument("--force", action="store_true")
    global_apply_parser.set_defaults(func=command_global_apply)

    global_reject_parser = subparsers.add_parser("global-reject", help="Reject a global proposal or mark it for revision")
    global_reject_parser.add_argument("--proposal-id", required=True)
    global_reject_parser.add_argument("--reason", required=True)
    global_reject_parser.add_argument("--revision", action="store_true", help="Treat reason as user revision feedback")
    global_reject_parser.add_argument("--cooldown-days", type=int, default=COOLDOWN_DAYS)
    global_reject_parser.add_argument("--cooldown-signals", type=int, default=COOLDOWN_SIGNAL_LIMIT)
    global_reject_parser.add_argument("--force", action="store_true")
    global_reject_parser.set_defaults(func=command_global_reject)

    compact_parser = subparsers.add_parser("compact", help="Compact raw signals while preserving cluster summaries")
    compact_parser.add_argument("--keep-strength-at-least", type=int, default=3)
    compact_parser.add_argument("--dry-run", action="store_true")
    compact_parser.set_defaults(func=command_compact)

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
