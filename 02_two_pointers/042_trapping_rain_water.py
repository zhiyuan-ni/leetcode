"""
Pattern: Two Pointers（对撞指针）

Core:
- 每格积水 = min(左边最高, 右边最高) - 自己的高度；最高值把自己也算进去，结果就不会为负。
- BruteForce: 对每一格向左、向右各扫一遍求最高值。
- TwoPass: 从左往右扫，遇到不低于 lmax 的柱子（>=）时，前面一段的水位就是 lmax；这样只能确定全局最高柱子左边的部分，再从右往左镜像扫一遍补上右边。
- Solution: l、r 从两端出发，移动较矮的一边。height[l] < height[r] 时 lmax <= rmax，而右边真正的最高只会 >= rmax，所以 l 这一格水位就是 lmax，不必知道右边全部。

Time:
- BruteForce: O(n^2)，n = 2 万约 8 s
- TwoPass: O(n)，每个下标最多被赋值一次
- Solution: O(n)，n = 2 万约 1.3 ms

Space:
- BruteForce: O(1)
- TwoPass: O(n)
- Solution: O(1)

Mistake:
- 暴力解左边扫描起点写成 l = 0，每次只读 height[0]；加 max(..., 0) 后结果从 -13 变成 0，bug 被藏住。
- TwoPass 只扫一遍，全局最高柱子右边没处理；判断用 > 而不是 >=，一样高的柱子不触发。
- 水位列表写成 [] / [n]（一个装着 n 的列表），赋值 IndexError；应为 [0] * n。
- 积水写成 height - level，减反了；return 了水位列表而不是结果。
"""


class SolutionBruteForce:
    def trap(self, height: list[int]) -> int:
        n = len(height)
        res = 0
        for i in range(1, n - 1):
            lmax = 0
            for j in range(i - 1, -1, -1):
                lmax = max(lmax, height[j])
            rmax = 0
            for j in range(i + 1, n):
                rmax = max(rmax, height[j])
            res += max(min(lmax, rmax) - height[i], 0)
        return res


class SolutionTwoPass:
    def trap(self, height: list[int]) -> int:
        n = len(height)
        level = [0] * n

        l, lmax = 0, height[0]
        for r in range(1, n):
            if height[r] >= lmax:
                for j in range(l, r):
                    level[j] = lmax
                lmax = height[r]
                l = r

        r, rmax = n - 1, height[-1]
        for l in range(n - 2, -1, -1):
            if height[l] >= rmax:
                for j in range(l + 1, r + 1):
                    level[j] = rmax
                rmax = height[l]
                r = l

        return sum(max(level[i] - height[i], 0) for i in range(n))


class Solution:
    def trap(self, height: list[int]) -> int:
        l, r = 0, len(height) - 1
        lmax = rmax = 0
        res = 0
        while l < r:
            if height[l] < height[r]:
                if height[l] > lmax:
                    lmax = height[l]
                res += lmax - height[l]
                l += 1
            else:
                if height[r] > rmax:
                    rmax = height[r]
                res += rmax - height[r]
                r -= 1
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

    def call_with_limit(cls, height, seconds):
        # 超时直接中断，让 O(n^2) 写法快速失败
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().trap(list(height))
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def reference(height):
        # 逐格按公式暴力计算，只用于生成小数据的期望值
        n = len(height)
        return sum(min(max(height[: i + 1]), max(height[i:])) - height[i] for i in range(n))

    cases = [
        # 题目示例
        ([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1], 6),
        ([4, 2, 0, 3, 2, 5], 9),
        # 少于 3 根柱子，接不住水
        ([5], 0),
        ([2, 1], 0),
        # 全平
        ([0, 0, 0], 0),
        ([5, 5, 5], 0),
        # 单调递增 / 单调递减
        ([1, 2, 3, 4], 0),
        ([4, 3, 2, 1], 0),
        # 一个坑，两边等高
        ([2, 0, 2], 2),
        ([3, 0, 0, 3], 6),
        # 中间比两边都高：不能算出负数
        ([1, 3, 2], 0),
        # 两边不等高，水位取矮的一边
        ([3, 1, 2], 1),
        ([2, 1, 3], 1),
        ([4, 2, 3], 1),
        # 右边最高的不在最右端
        ([5, 4, 1, 2], 1),
        # 多个坑，中间有更高的柱子隔开
        ([2, 0, 3, 0, 2], 4),
        # 坑里有小凸起，被水淹没
        ([3, 0, 1, 0, 3], 8),
        ([1, 0, 2, 0, 1, 0, 3], 6),
        # 数值上限
        ([100000, 0, 100000], 100000),
    ]

    # 随机小数据，和暴力结果对比
    random.seed(0)
    for _ in range(500):
        height = [random.randint(0, 6) for _ in range(random.randint(1, 12))]
        cases.append((height, reference(height)))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for height, expected in cases:
            got, _ = call_with_limit(cls, height, 1.0)
            assert got is not TIMED_OUT, f"{cls.__name__} {height}: 超过 1s，可能死循环"
            assert got == expected, f"{cls.__name__} {height}: 期望 {expected}，得到 {got}"

    # 题目 n <= 2 * 10^4，要求 O(n)。只对最终解 Solution 计时，超过 1s 直接中断。
    # 本地实测：O(n) 写法 2 ~ 4ms；逐格向两边扫描的 O(n^2) 写法用切片 max 约 2.5s，纯循环约 8s
    n = 20_000
    random.seed(1)
    perf_cases = [
        ("随机", [random.randint(0, 10**5) for _ in range(n)], 1000840109),
        ("中间一个高峰", [min(i, n - 1 - i) for i in range(n)], 0),
        ("V 形", [abs(n // 2 - i) for i in range(n)], 99980001),
        ("锯齿", [0 if i % 2 == 0 else 10**5 for i in range(n)], 999900000),
        ("全相同", [7] * n, 0),
    ]
    timings = []

    for name, height, expected in perf_cases:
        got, elapsed = call_with_limit(Solution, height, 1.0)
        assert got is not TIMED_OUT, f"Solution 大数据（{name}）超过 1s 被中断，可能不是 O(n)"
        assert got == expected, f"Solution 大数据（{name}）: 期望 {expected}，得到 {got}"
        timings.append(f"{name} {elapsed * 1000:.0f} ms")

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {', '.join(timings)})")
