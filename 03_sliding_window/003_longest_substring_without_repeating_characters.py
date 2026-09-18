"""
Pattern: Sliding Window

Core:
last 记录每个字符上次出现的下标。r 向右扫，若 s[r] 上次出现的位置还在窗口内（last[c] >= l），左端直接跳到 last[c] + 1；否则不动。l 只往右走，窗口长度 r - l + 1。

Time: O(n)
Space: O(字符集)，最多 95 个可见字符

Mistake:
- 窗口两端都包含，长度是 r - l + 1，写成 r - l 少算 1。
- 直接 l = last[c] + 1，没判断上次位置是否还在窗口内：'abba' 最后一步 l 从 2 退回 1，得到 3（期望 2）。
"""


class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        last = {}
        l = 0
        res = 0
        for r, c in enumerate(s):
            if c in last and last[c] >= l:
                l = last[c] + 1
            if r - l + 1 > res:
                res = r - l + 1
            last[c] = r
        return res


if __name__ == "__main__":
    import random
    import signal
    import time

    class Timeout(Exception):
        pass

    def _on_alarm(signum, frame):
        raise Timeout

    signal.signal(signal.SIGALRM, _on_alarm)
    TIMED_OUT = object()  # 和「忘了 return」得到的 None 区分开

    def call_with_limit(cls, s, seconds):
        # 超时直接中断，让 O(n^2) 写法快速失败
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().lengthOfLongestSubstring(s)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def reference(s):
        # 枚举所有子串逐个检查，只用于生成小数据的期望值
        n = len(s)
        return max((j - i for i in range(n) for j in range(i + 1, n + 1) if len(set(s[i:j])) == j - i), default=0)

    cases = [
        # 题目示例
        ("abcabcbb", 3),
        ("bbbbb", 1),
        ("pwwkew", 3),
        # 空串 / 单个字符 / 空格
        ("", 0),
        ("a", 1),
        (" ", 1),
        ("  ", 1),
        ("au", 2),
        # 全都不同，答案是整个串
        ("abcdef", 6),
        # 大小写是不同字符
        ("Aa", 2),
        # 数字、符号、空格
        ("0123456789", 10),
        ("!@#$%^&*()", 10),
        ("a b c a", 3),
        # 重复出现后，左端只能跳到重复字符的下一位，不能清空整个窗口
        ("dvdf", 3),
        # 上次出现的位置已经在窗口左边：左端不能往回退
        ("abba", 2),
        ("tmmzuxt", 5),
        # 最长的在末尾
        ("abcaxyz", 6),
        ("aab", 2),
        ("abcb", 3),
        ("ababab", 2),
    ]

    # 随机小数据，和暴力结果对比。字符集小，制造大量重复
    random.seed(0)
    for _ in range(500):
        s = "".join(random.choice("abc d") for _ in range(random.randint(0, 12)))
        cases.append((s, reference(s)))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for s, expected in cases:
            got, _ = call_with_limit(cls, s, 1.0)
            assert got is not TIMED_OUT, f"{cls.__name__} {s!r}: 超过 1s，可能死循环"
            assert got == expected, f"{cls.__name__} {s!r}: 期望 {expected}，得到 {got}"

    # 题目 n <= 5 * 10^4。只对最终解 Solution 计时，超过 1s 直接中断。
    # 本地实测：滑动窗口 3 ~ 11ms；枚举所有子串的暴力 5s 以上。
    # 注意：「每个起点往右延伸、遇到重复就 break」只要 12 ~ 240ms，这里测不出来：
    # 字符集最多 95 个可见字符，每个起点最多走 95 步，它其实是 O(n * 95)
    n = 50_000
    chars = [chr(c) for c in range(32, 127)]
    random.seed(1)
    perf_cases = [
        ("随机可见字符", "".join(random.choice(chars) for _ in range(n)), 46),
        ("全相同", "a" * n, 1),
        ("95 个字符循环", "".join(chars[i % 95] for i in range(n)), 95),
        ("只有小写字母", "".join(random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(n)), 21),
    ]
    timings = []

    for name, s, expected in perf_cases:
        got, elapsed = call_with_limit(Solution, s, 1.0)
        assert got is not TIMED_OUT, f"Solution 大数据（{name}）超过 1s 被中断，可能是 O(n^2)"
        assert got == expected, f"Solution 大数据（{name}）: 期望 {expected}，得到 {got}"
        timings.append(f"{name} {elapsed * 1000:.0f} ms")

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {', '.join(timings)})")
