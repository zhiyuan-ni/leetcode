"""
Pattern: Sliding Window（可变长度）

Core:
右端扩张到窗口覆盖 t，再让左端收缩到不再覆盖，每次覆盖时用当前窗口更新答案；两个指针都只往右走，O(n)。
- Scan: 用 58 位计数数组，每次全扫一遍判断是否覆盖，判断 O(58)。
- Solution: 维护 missing =「还差多少个字符」。右端进来 c 时只有 need[c] > 0 才 missing -= 1；左端移出时先 need[c] += 1，加完 > 0 才 missing += 1。判断降到 O(1)。

Time: O(n * 58) / O(n)。n = 10^5 实测：Scan 260 ~ 320 ms，Solution 23 ~ 78 ms
Space: O(字符集)

Mistake:
- return 缩进进了 while 循环体，第一轮就返回。
- 统计窗口时写成 source[ord(subt) - ...]，subt 是上一段循环留下的变量，应为 s[r]。
- 计数数组只开 26：大小写字母下标最大 ord('z') - ord('A') = 57，要开 58 或用 Counter；判断也要扫满 58。
- 无解时 res 初值设成 s，返回了整个串，应为空串。
- 收缩时先 l += 1 再减计数，减掉的是新左端而不是被移出的字符。
- 收缩循环写成「先移出、再判断、退出后用 l - 1 补偿」：补偿只在「不再覆盖」这种退出下成立，窗口缩到只剩一个字符时 l 没有多走，('abcdef', 'f') 得到 'ef'。把更新答案放在移出之前、覆盖判断放在循环条件上，就不需要补偿。
"""

from collections import Counter


class SolutionScan:
    def minWindow(self, s: str, t: str) -> str:
        size = ord("z") - ord("A") + 1
        win = [0] * size
        need = [0] * size
        for c in t:
            need[ord(c) - ord("A")] += 1

        res = ""
        l = r = 0
        while r < len(s):
            win[ord(s[r]) - ord("A")] += 1
            covered = all(win[j] >= need[j] for j in range(size))
            while covered:
                cur = s[l:r + 1]
                if not res or len(cur) < len(res):
                    res = cur
                win[ord(s[l]) - ord("A")] -= 1
                covered = all(win[j] >= need[j] for j in range(size))
                l += 1
            r += 1
        return res


class Solution:
    def minWindow(self, s: str, t: str) -> str:
        need = Counter(t)
        missing = len(t)
        res = ""
        l = 0
        for r, c in enumerate(s):
            if need[c] > 0:
                missing -= 1
            need[c] -= 1
            while missing == 0:
                if not res or r - l + 1 < len(res):
                    res = s[l:r + 1]
                need[s[l]] += 1
                if need[s[l]] > 0:
                    missing += 1
                l += 1
        return res


if __name__ == "__main__":
    import random
    import string
    import signal
    import time
    from collections import Counter

    class Timeout(Exception):
        pass

    def _on_alarm(signum, frame):
        raise Timeout

    signal.signal(signal.SIGALRM, _on_alarm)
    TIMED_OUT = object()  # 和「忘了 return」得到的 None 区分开

    def call_with_limit(cls, s, t, seconds):
        # 超时直接中断，让枚举所有子串的写法快速失败
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().minWindow(s, t)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def reference(s, t):
        # 枚举每个起点，向右延伸到第一次覆盖 t，只用于生成小数据的期望值
        need = Counter(t)
        best = ""
        for i in range(len(s)):
            for j in range(i + 1, len(s) + 1):
                if not need - Counter(s[i:j]):
                    if best == "" or j - i < len(best):
                        best = s[i:j]
                    break
        return best

    cases = [
        # 题目示例
        ("ADOBECODEBANC", "ABC", "BANC"),
        ("a", "a", "a"),
        ("a", "aa", ""),
        # t 比 s 长 / s 缺字符：无解
        ("ab", "A", ""),
        # 顺序不要求
        ("ab", "ba", "ab"),
        ("abc", "cba", "abc"),
        ("bba", "ab", "ba"),
        # 大小写是不同字符
        ("aA", "Aa", "aA"),
        # t 里有重复字符，次数要够
        ("aa", "aa", "aa"),
        ("aaflslflsldkalskaaa", "aaa", "aaa"),
        ("aaaaaaaaab", "ab", "ab"),
        ("ADOBECODEBANC", "ABCC", "CODEBANC"),
        # 窗口里允许有 t 之外的字符
        ("cabwefgewcwaefgcf", "cae", "cwae"),
        ("abcabdebac", "cda", "cabd"),
        # 答案是整个 s / 在末尾 / 单字符
        ("xyz", "xyz", "xyz"),
        ("abcdef", "f", "f"),
    ]

    # 随机小数据，和暴力结果对比。字母只用 abc，制造大量重复
    random.seed(0)
    for _ in range(500):
        rs = "".join(random.choice("abc") for _ in range(random.randint(1, 12)))
        rt = "".join(random.choice("abc") for _ in range(random.randint(1, 4)))
        cases.append((rs, rt, reference(rs, rt)))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for cs, ct, expected in cases:
            got, _ = call_with_limit(cls, cs, ct, 1.0)
            assert got is not TIMED_OUT, f"{cls.__name__} s={cs!r} t={ct!r}: 超过 1s，可能死循环"
            assert got is not None, f"{cls.__name__} s={cs!r} t={ct!r}: 返回了 None（无解要返回空串）"
            assert got == expected, f"{cls.__name__} s={cs!r} t={ct!r}: 期望 {expected!r}，得到 {got!r}"

    # 题目 len(s), len(t) <= 10^5。只对最终解 Solution 计时，超过 1s 直接中断。
    # 本地实测：维护「还差多少个字符」的滑动窗口 9 ~ 26ms；每步比较两个 Counter 35 ~ 120ms（字符集只有 52 所以也能过）；
    # 枚举所有子串的暴力在 n = 10^5 远超 1s。
    # 答案太长不写进文件，只比长度，再验证它确实覆盖 t、且是 s 的子串
    n = 100_000
    random.seed(1)
    perf_cases = [
        ("随机大小写字母，t 长 10",
         "".join(random.choice(string.ascii_letters) for _ in range(n)),
         "".join(random.sample(string.ascii_letters, 10)), 21),
        ("全 a，t = a * 100", "a" * n, "a" * 100, 100),
        ("无解（缺一个字符）", "ab" * (n // 2), "abc", 0),
        ("t 长 5 万",
         "".join(random.choice("abc") for _ in range(n)),
         "".join(random.choice("abc") for _ in range(50_000)), 50230),
        ("答案在最末尾", "b" * (n - 3) + "abc", "abc", 3),
    ]
    timings = []

    for name, cs, ct, expected_len in perf_cases:
        got, elapsed = call_with_limit(Solution, cs, ct, 1.0)
        assert got is not TIMED_OUT, f"Solution 大数据（{name}）超过 1s 被中断，可能在枚举子串或反复重算"
        assert got is not None, f"Solution 大数据（{name}）: 返回了 None"
        assert len(got) == expected_len, f"Solution 大数据（{name}）: 期望长度 {expected_len}，得到 {len(got)}"
        if expected_len:
            assert got in cs, f"Solution 大数据（{name}）: 返回的不是 s 的子串"
            assert not Counter(ct) - Counter(got), f"Solution 大数据（{name}）: 返回的窗口没有覆盖 t"
        timings.append(f"{name} {elapsed * 1000:.0f} ms")

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {', '.join(timings)})")
