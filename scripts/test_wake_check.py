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


if __name__ == "__main__":
    test_wake_check_cases()
    print("wake-check tests passed")
