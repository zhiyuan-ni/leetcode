"""
Pattern: 排序 + 一遍扫描（区间合并）

Core:
按左端点排序后，能合并的区间一定相邻。扫一遍，当前区间左端 <= 上一段右端就合并（右端取较大值），否则新起一段。
- Track: 用 start / end 跨轮携带当前这一段，遇到接不上的就把 [start, end] 收进结果并重开一段。
- Solution: 单层循环，能合就改 res[-1][1]，否则 append；少了 start / end 和 i+1 的边界判断。

Time: O(n log n)，瓶颈是排序
Space: O(n)（排序副本 + 结果），除结果外 O(1)

Mistake:
- （本题一次通过，未出错；第一版内层 while 忘了推进 l 导致下标越界，补上即正确）

易错点:
- 端点相接也要合并：判断用 a <= res[-1][1]，写成 < 会让 [[1,4],[4,5]] 分成两段。
- 合并时右端取 max：直接赋新右端会让被完全包含的区间缩小右端，[[1,4],[2,3]] 得到 [[1,3]]。
- 忘了排序：[[6,7],[2,4],[5,9]] 得到 [[6,9]]。
- 反复两两合并到稳定是 O(n^2)：n = 10^4「互不相交」实测 897 ms，排序扫描 1 ~ 4 ms。
"""


class SolutionTrack:
    def merge(self, intervals: list[list[int]]) -> list[list[int]]:
        intervals = sorted(intervals)
        res = []
        i = 0
        start = intervals[i][0]
        end = intervals[i][1]
        while i < len(intervals):
            if i+1 < len(intervals) and intervals[i+1][0] <= end:
                end = max(end, intervals[i+1][1])
            else:
                res.append([start, end])
                if i+1 < len(intervals):
                    start = intervals[i+1][0]
                    end = intervals[i+1][1]
            i += 1
        return res


class Solution:
    def merge(self, intervals: list[list[int]]) -> list[list[int]]:
        res = []
        for a, b in sorted(intervals):
            if res and a <= res[-1][1]:
                if b > res[-1][1]:
                    res[-1][1] = b
            else:
                res.append([a, b])
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

    def call_with_limit(cls, intervals, seconds):
        # 超时直接中断，让 O(n^2) 反复合并的写法快速失败
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().merge([list(x) for x in intervals])
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def normalize(res):
        # 每段可以是 list 或 tuple，统一成 list 再比较；顺序按左端点排
        return sorted([list(x) for x in res])

    def reference(intervals):
        # 覆盖点法（坐标乘 2，保证 [1,4] 和 [5,6] 之间的空隙不会被填上），只用于小数据
        pts = set()
        for a, b in intervals:
            pts.update(range(2 * a, 2 * b + 1))
        res = []
        for p in sorted(pts):
            if res and p == res[-1][1] + 1:
                res[-1][1] = p
            else:
                res.append([p, p])
        return [[a // 2, b // 2] for a, b in res]

    cases = [
        # 题目示例
        ([[1, 3], [2, 6], [8, 10], [15, 18]], [[1, 6], [8, 10], [15, 18]]),
        ([[1, 4], [4, 5]], [[1, 5]]),
        # 端点相邻但不重叠：[1,4] 和 [5,6] 不合并
        ([[1, 4], [5, 6]], [[1, 4], [5, 6]]),
        ([[6, 7], [2, 4], [5, 9]], [[2, 4], [5, 9]]),
        # 一段完全包含另一段：右端不能被缩小
        ([[1, 4], [2, 3]], [[1, 4]]),
        ([[0, 10000], [1, 2]], [[0, 10000]]),
        # 单段 / 退化成一个点
        ([[1, 1]], [[1, 1]]),
        ([[10000, 10000]], [[10000, 10000]]),
        ([[0, 0], [0, 0]], [[0, 0]]),
        # 输入无序
        ([[2, 3], [1, 5]], [[1, 5]]),
        ([[5, 6], [1, 2], [3, 4]], [[1, 2], [3, 4], [5, 6]]),
        ([[1, 2], [3, 4], [2, 3]], [[1, 4]]),
        # 完全相同
        ([[1, 4], [1, 4]], [[1, 4]]),
        # 链式合并：合并后的右端要能继续往后吃
        ([[1, 3], [3, 5], [5, 7]], [[1, 7]]),
        ([[1, 10], [2, 3], [4, 5], [6, 7]], [[1, 10]]),
    ]

    # 随机小数据，和覆盖点法对比。坐标范围小，制造大量重叠和相邻
    random.seed(0)
    for _ in range(500):
        iv = []
        for _ in range(random.randint(1, 8)):
            a = random.randint(0, 10)
            iv.append([a, a + random.randint(0, 3)])
        cases.append((iv, reference(iv)))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for iv, expected in cases:
            got, _ = call_with_limit(cls, iv, 1.0)
            assert got is not TIMED_OUT, f"{cls.__name__} {iv}: 超过 1s，可能死循环"
            assert got is not None, f"{cls.__name__} {iv}: 返回了 None"
            for seg in got:
                assert len(list(seg)) == 2, f"{cls.__name__} {iv}: {seg} 不是 [start, end] 这样的两元素区间"
            assert normalize(got) == normalize(expected), f"{cls.__name__} {iv}: 期望 {expected}，得到 {got}"

    # 题目 n <= 10^4，坐标 <= 10^4。只对最终解 Solution 计时，超过 0.5s 直接中断。
    # 本地实测：排序后一遍扫描 1 ~ 4ms；反复两两合并直到稳定在「互不相交」这组要 897ms
    # 结果可能很长，只比段数和所有端点之和，再抽查排序后的前后几段
    n = 10_000
    random.seed(1)

    def rnd(count, span):
        out = []
        for _ in range(count):
            a = random.randint(0, 10**4 - span)
            out.append([a, a + random.randint(0, span)])
        return out

    perf_cases = [
        ("随机短区间", rnd(n, 5), 509, 5067109),
        ("随机长区间", rnd(n, 2000), 1, 9962),
        ("全部重叠", [[0, 10**4] for _ in range(n)], 1, 10000),
        ("互不相交", [[2 * i, 2 * i + 1] for i in range(n)], 10000, 199990000),
        ("全相同", [[3, 7] for _ in range(n)], 1, 10),
    ]
    timings = []

    for name, iv, expected_len, expected_sum in perf_cases:
        got, elapsed = call_with_limit(Solution, iv, 0.5)
        assert got is not TIMED_OUT, f"Solution 大数据（{name}）超过 0.5s 被中断，可能在反复扫描"
        assert got is not None, f"Solution 大数据（{name}）: 返回了 None"
        got = normalize(got)
        assert len(got) == expected_len, f"Solution 大数据（{name}）: 期望 {expected_len} 段，得到 {len(got)}"
        assert sum(a + b for a, b in got) == expected_sum, f"Solution 大数据（{name}）: 端点之和期望 {expected_sum}，得到 {sum(a + b for a, b in got)}"
        for i in range(len(got) - 1):
            assert got[i][0] <= got[i][1], f"Solution 大数据（{name}）: 第 {i} 段左端大于右端：{got[i]}"
            assert got[i][1] < got[i + 1][0], f"Solution 大数据（{name}）: 第 {i} 段和第 {i + 1} 段还能合并：{got[i]} {got[i + 1]}"
        timings.append(f"{name} {elapsed * 1000:.0f} ms")

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {', '.join(timings)})")
