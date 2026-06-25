import jinhua


CASES = [
    ("为什么没触发jinhua.skill？", True),
    ("This should have triggered your methodology skill.", True),
    ("以后推荐 GitHub 项目前应该先读 README 和源码。", True),
    ("不是第 13 页，是第 6 页。", False),
    ("Fix the typo in the heading.", False),
]


def test_wake_check_cases() -> None:
    for text, expected in CASES:
        actual = jinhua.wake_check_result(text)["should_route"]
        assert actual is expected, (text, actual, expected)


def test_user_prompt_submit_hook_routes_only_matched_prompts() -> None:
    payload = jinhua.read_hook_payload('{"input": {"prompt": "jinhua should have triggered"}}')
    assert jinhua.extract_hook_prompt(payload) == "jinhua should have triggered"

    routed = jinhua.user_prompt_submit_hook_output({"prompt": "为什么没触发jinhua.skill？"})
    assert routed["continue"] is True
    assert "hookSpecificOutput" in routed
    assert "additionalContext" in routed["hookSpecificOutput"]

    with_cwd = jinhua.user_prompt_submit_hook_output({
        "prompt": "jinhua should have triggered",
        "cwd": r"D:\Jinhua",
    })
    assert r'--project-root "D:\Jinhua"' in with_cwd["hookSpecificOutput"]["additionalContext"]

    skipped = jinhua.user_prompt_submit_hook_output({"prompt": "不是第 13 页，是第 6 页。"})
    assert skipped == {"continue": True}


if __name__ == "__main__":
    test_wake_check_cases()
    test_user_prompt_submit_hook_routes_only_matched_prompts()
    print("wake-check tests passed")
