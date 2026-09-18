"""
Pattern: Sliding Window（固定长度）

Core:
窗口长度固定为 len(p)。need、win 两个 26 位计数数组；窗口右移一格时 win 减去移出的字符、加上移入的字符，再和 need 比较，相等就记下起点。

Time: O(26 * n)，列表比较在 C 层完成
Space: O(1)，两个长度 26 的数组

Mistake:
- 字符转编码写成 oct(c)：oct 是整数转八进制字符串，应为 ord(c)。
"""


class Solution:
    def findAnagrams(self, s: str, p: str) -> list[int]:
        n, k = len(s), len(p)
        if n < k:
            return []

        a = ord("a")
        need = [0] * 26
        win = [0] * 26
        for c in p:
            need[ord(c) - a] += 1
        for c in s[:k]:
            win[ord(c) - a] += 1

        res = [0] if win == need else []
        for i in range(1, n - k + 1):
            win[ord(s[i - 1]) - a] -= 1
            win[ord(s[i + k - 1]) - a] += 1
            if win == need:
                res.append(i)
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

    def call_with_limit(cls, s, p, seconds):
        # 超时直接中断，让逐个窗口重新排序 / 重新计数的写法快速失败
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().findAnagrams(s, p)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def reference(s, p):
        # 逐个窗口排序比较，只用于生成小数据的期望值
        m = len(p)
        return [i for i in range(len(s) - m + 1) if sorted(s[i:i + m]) == sorted(p)]

    cases = [
        # 题目示例
        ("cbaebabacd", "abc", [0, 6]),
        ("abab", "ab", [0, 1, 2]),
        # 单个字符
        ("a", "a", [0]),
        ("a", "b", []),
        # p 比 s 长
        ("a", "ab", []),
        ("ab", "abc", []),
        # s 和 p 一样长
        ("abc", "cba", [0]),
        # 窗口重叠、全是同一个字母
        ("aaaa", "aa", [0, 1, 2]),
        ("aaaa", "a", [0, 1, 2, 3]),
        ("zzz", "z", [0, 1, 2]),
        # 移出窗口的字母计数减到 0：用 dict / Counter 时别留下值为 0 的键
        # （本地 Python 3.9 的 Counter 比较会把 {'b': 0} 当成不相等；LeetCode 的 3.10+ 不会，所以那边能过、这里会失败）
        ("baa", "aa", [1]),
        ("eidbaooo", "ab", [3]),
        # 匹配在最后一个窗口
        ("abcd", "dc", [2]),
        # 字母种类对但次数不对
        ("aab", "ab", [1]),
        ("aaabbb", "ab", [2]),
        # 连续多个匹配
        ("abacbabc", "abc", [1, 2, 3, 5]),
    ]

    # 随机小数据，和暴力结果对比。字母只用 abc，制造大量匹配
    random.seed(0)
    for _ in range(500):
        s = "".join(random.choice("abc") for _ in range(random.randint(1, 12)))
        p = "".join(random.choice("abc") for _ in range(random.randint(1, 5)))
        cases.append((s, p, reference(s, p)))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for s, p, expected in cases:
            got, _ = call_with_limit(cls, s, p, 1.0)
            assert got is not TIMED_OUT, f"{cls.__name__} s={s!r} p={p!r}: 超过 1s，可能死循环"
            assert got is not None, f"{cls.__name__} s={s!r} p={p!r}: 返回了 None"
            # 下标顺序不限，排序后比较
            assert sorted(got) == expected, f"{cls.__name__} s={s!r} p={p!r}: 期望 {expected}，得到 {got}"

    # 题目 len(s), len(p) <= 3 * 10^4。只对最终解 Solution 计时，超过 1s 直接中断。
    # 本地实测：滑动窗口 3 ~ 6ms；每个窗口重新 sorted 1.3 ~ 5s 以上，每个窗口重新 Counter 约 3s。
    # p 很短时逐个窗口重算也很快，所以要用长 p（1 万）才能测出来。
    # 结果太长不写进文件，只比个数和下标之和；「随机 abc」这组再逐个验证每个下标
    n = 30_000
    random.seed(1)
    perf_cases = [
        ("随机 abc，p 长 3", "".join(random.choice("abc") for _ in range(n)), "abc", 6701, 100712385),
        ("全 a，p 长 1 万", "a" * n, "a" * 10_000, 20001, 200010000),
        ("随机 26 字母，p 长 1 万",
         "".join(random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(n)),
         "".join(random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(10_000)), 0, 0),
        ("ab 交替，p 长 1 万", "ab" * (n // 2), "ab" * 5000, 20001, 200010000),
        ("p 比 s 长", "a" * 10_000, "a" * n, 0, 0),
    ]
    timings = []

    for name, s, p, expected_len, expected_sum in perf_cases:
        got, elapsed = call_with_limit(Solution, s, p, 1.0)
        assert got is not TIMED_OUT, f"Solution 大数据（{name}）超过 1s 被中断，可能在逐个窗口重新计数或排序"
        assert got is not None, f"Solution 大数据（{name}）: 返回了 None"
        assert len(set(got)) == len(got), f"Solution 大数据（{name}）: 有重复的下标"
        assert len(got) == expected_len, f"Solution 大数据（{name}）: 期望 {expected_len} 个下标，得到 {len(got)} 个"
        assert sum(got) == expected_sum, f"Solution 大数据（{name}）: 下标之和期望 {expected_sum}，得到 {sum(got)}"
        if len(p) <= 3:
            bad = [i for i in got if sorted(s[i:i + len(p)]) != sorted(p)]
            assert not bad, f"Solution 大数据（{name}）: 下标 {bad[0]} 处不是异位词"
        timings.append(f"{name} {elapsed * 1000:.0f} ms")

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {', '.join(timings)})")
