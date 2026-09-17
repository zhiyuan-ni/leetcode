"""
Pattern: Two Pointers（对撞指针）

Core:
- BruteForce: 宽度 w 从 n - 1 递减到 1，枚举每个宽度下的所有左端点。
- TwoPointers: l、r 从两端出发，算完当前面积后移动较矮的一边。以矮边为一端的剩余组合高度不超过矮边、宽度更窄，都不会超过当前面积，所以可以丢掉；两边一样高时移动任意一边都对。
- Solution: 在 TwoPointers 基础上，移动矮边时连续跳过所有不高于它的线（同样高度不超过、宽度更窄）；一次比较同时决定高度和方向，不调用 min()。

Time:
- BruteForce: O(n^2)
- TwoPointers: O(n)
- Solution: O(n)，常数更小；n = 10^5 实测约 3 ms，TwoPointers 约 11 ms。严格递增时跳不过任何线，反而比只去掉 min() 的写法慢

Space:
- BruteForce: O(1)
- TwoPointers: O(1)
- Solution: O(1)

Mistake:
- 忘了 return res，返回 None。
- 移动矮边的理由不能只说「高度受限于矮边」，还要加上宽度一定变窄，两者合起来才能证明跳过的组合不会更大。
- 跳过优化：用了不存在的 ?: 三元写法且方向相反；cur 在 h 赋值前计算；else 分支从 if 复制过来，移动 r 却判断 height[l]，导致死循环或跳过最优解。
"""


class SolutionBruteForce:
    def maxArea(self, height: list[int]) -> int:
        res = 0
        w = len(height) - 1

        while w >= 1:
            l = 0
            for _ in range(len(height) - w):
                cur_h = min(height[l], height[l + w])
                if cur_h * w > res:
                    res = cur_h * w
                l += 1
            w -= 1
        return res


class SolutionTwoPointers:
    def maxArea(self, height: list[int]) -> int:
        l, r = 0, len(height) - 1
        res = 0
        while l < r:
            cur = min(height[l], height[r]) * (r - l)
            if cur > res:
                res = cur
            if height[l] < height[r]:
                l += 1
            else:
                r -= 1
        return res


class Solution:
    def maxArea(self, height: list[int]) -> int:
        l, r = 0, len(height) - 1
        res = 0
        while l < r:
            if height[l] < height[r]:
                h = height[l]
                cur = h * (r - l)
                while l < r and height[l] <= h:
                    l += 1
            else:
                h = height[r]
                cur = h * (r - l)
                while l < r and height[r] <= h:
                    r -= 1
            if cur > res:
                res = cur
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
        # 超时直接中断：既能让 O(n^2) 写法快速失败，也能抓住高度相等时指针不动的死循环
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().maxArea(list(height))
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def reference(height):
        # 暴力枚举，只用于生成小数据的期望值
        n = len(height)
        return max(min(height[i], height[j]) * (j - i) for i in range(n) for j in range(i + 1, n))

    cases = [
        # 题目示例
        ([1, 8, 6, 2, 5, 4, 8, 3, 7], 49),
        ([1, 1], 1),
        # 只有两条线，且有高度为 0
        ([0, 0], 0),
        ([0, 5], 0),
        # 数值上限
        ([10000, 10000], 10000),
        # 最优解就是最外侧两条
        ([4, 3, 2, 1, 4], 16),
        ([1, 2, 1], 2),
        ([1, 2, 4, 3], 4),
        # 最优解是中间相邻的两条高线，宽度只有 1
        ([2, 3, 4, 5, 18, 17, 6], 17),
        ([1, 1000, 1000, 1], 1000),
        # 高度全相同：两端高度相等时指针怎么移动
        ([5, 5, 5, 5, 5, 5], 25),
        # 单调递增 / 单调递减
        (list(range(1, 11)), 25),
        (list(range(10, 0, -1)), 25),
    ]

    # 随机小数据，和暴力结果对比。取值范围小，制造大量高度相等的情况
    random.seed(0)
    for _ in range(500):
        height = [random.randint(0, 10) for _ in range(random.randint(2, 12))]
        cases.append((height, reference(height)))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for height, expected in cases:
            got, _ = call_with_limit(cls, height, 1.0)
            assert got is not TIMED_OUT, f"{cls.__name__} {height}: 超过 1s，可能死循环"
            assert got == expected, f"{cls.__name__} {height}: 期望 {expected}，得到 {got}"

    # 题目 n <= 10^5，要求 O(n)。只对最终解 Solution 计时，超过 1s 直接中断：
    # O(n) 写法约 10ms；暴力 O(n^2) 在 n = 10^4 时已经要 4s，10^5 时约 7 分钟
    n = 100_000
    random.seed(1)
    rising = [i * 10**4 // (n - 1) for i in range(n)]

    perf_cases = [
        ("随机", [random.randint(0, 10**4) for _ in range(n)], 995355400),
        ("单调递增", rising, 249995000),
        ("单调递减", rising[::-1], 249995000),
        ("高度全相同", [10**4] * n, 999990000),
    ]
    timings = []

    for name, height, expected in perf_cases:
        got, elapsed = call_with_limit(Solution, height, 1.0)
        assert got is not TIMED_OUT, f"Solution 大数据（{name}）超过 1s 被中断，可能不是 O(n) 或死循环"
        assert got == expected, f"Solution 大数据（{name}）: 期望 {expected}，得到 {got}"
        timings.append(f"{name} {elapsed * 1000:.0f} ms")

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {', '.join(timings)})")
