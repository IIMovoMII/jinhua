import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_claude_hooks_json() -> None:
    data = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    assert set(data["hooks"]) == {"UserPromptSubmit", "PostToolUse"}
    text = json.dumps(data)
    assert "${CLAUDE_PLUGIN_ROOT}" in text
    assert '"args"' not in text
    assert "claude-codex-hooks.json" not in text
    assert "output_state" not in text


def test_openclaw_manifest() -> None:
    data = json.loads((ROOT / "adapters" / "openclaw" / "openclaw.plugin.json").read_text(encoding="utf-8"))
    assert data["id"] == "jinhua"
    assert data["version"] == "2.0.0"
    assert data["skills"] == ["skills/jinhua"]
    assert (ROOT / "adapters" / "openclaw" / "skills" / "jinhua" / "SKILL.md").exists()


def test_skill_adapters_exist() -> None:
    for path in [
        ROOT / "adapters" / "hermes" / "skills" / "jinhua" / "SKILL.md",
        ROOT / "adapters" / "trae" / "skills" / "jinhua" / "SKILL.md",
        ROOT / "adapters" / "workbuddy" / "skills" / "jinhua" / "SKILL.md",
    ]:
        text = path.read_text(encoding="utf-8")
        assert "cycle" in text
        assert "user gate" in text.lower()
        assert "ledger" in text.lower()


if __name__ == "__main__":
    test_claude_hooks_json()
    test_openclaw_manifest()
    test_skill_adapters_exist()
    print("adapter tests passed")
