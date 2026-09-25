"""
Pattern: DP / 递推（Kadane）

Core:
枚举「以当前元素结尾的最大子数组和」cur：前面那段和为负就丢掉、从当前元素重新开始，否则接上去；答案取所有 cur 的最大值。
- SkipSmaller: 第一版写法。pre >= 0 时先把上一轮的 pre 记进 res 再累加；pre < 0 时只在 num >= pre 时才重新开始（两个负数时保留较大的那个，什么都不做也正确），结尾用 max(pre, res) 收尾。
- Solution: 每轮统一做两件事，cur < 0 就从 num 重新开始，否则累加，然后更新 best。分支少、res 不滞后。

Time: O(n)。n = 10^5 实测：SkipSmaller 5.6 ~ 5.9 ms（每轮一次 max() + 浮点比较），Solution 2.6 ~ 2.9 ms
Space: O(1)

Mistake:
- （本题一次通过，未出错）

易错点:
- 答案初值不能设成 0：子数组非空，全负时会错误返回 0（[-1] 应为 -1）。
- 换成前缀和思路时，要先用当前 pre 减去「之前的最小前缀」更新答案，再更新最小前缀；顺序反了等于允许空子数组，[-1] 会得到 0。
- 进阶的分治 O(n log n) 本地约 35 ms，且 n = 10^5 时要调大递归深度；线性递推 2 ~ 3 ms。
"""


class SolutionSkipSmaller:
    def maxSubArray(self, nums: list[int]) -> int:
        pre = res = -float("inf")
        for num in nums:
            if pre >= 0:
                res = max(pre, res)
                pre += num
            elif num >= pre:
                pre = num
        return max(pre, res)


class Solution:
    def maxSubArray(self, nums: list[int]) -> int:
        cur = best = -float('inf')
        for num in nums:
            if cur < 0:
                cur = num
            else:
                cur = cur + num
            best = max(best, cur)
        return best


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

    def call_with_limit(cls, nums, seconds):
        # 超时直接中断，让 O(n^2) 写法快速失败
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().maxSubArray(list(nums))
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def reference(nums):
        # 枚举所有子数组，只用于生成小数据的期望值
        n = len(nums)
        return max(sum(nums[i:j]) for i in range(n) for j in range(i + 1, n + 1))

    cases = [
        # 题目示例
        ([-2, 1, -3, 4, -1, 2, 1, -5, 4], 6),
        ([1], 1),
        ([5, 4, -1, 7, 8], 23),
        # 子数组非空：全是负数时答案是最大的那个负数，不是 0
        ([-1], -1),
        ([-2, -1], -1),
        ([-3, -2, -5], -2),
        ([-10000], -10000),
        # 有 0
        ([0], 0),
        ([0, 0], 0),
        ([-1, 0, -2], 0),
        # 全正：答案是整个数组
        ([1, 2, 3], 6),
        # 中间的负数要不要跨过去
        ([-1, 2, -1, 2, -1], 3),
        ([2, -1, 2], 3),
        ([3, -1, -1, -1, 3], 3),
        ([1, -2, 3, -2, 3], 4),
        ([-5, 4, -1, 7, -2], 10),
        # 数值边界
        ([10000, -10000, 10000], 10000),
    ]

    # 随机小数据，和暴力结果对比。取值范围小且有正有负
    random.seed(0)
    for _ in range(500):
        nums = [random.randint(-5, 5) for _ in range(random.randint(1, 12))]
        cases.append((nums, reference(nums)))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for nums, expected in cases:
            got, _ = call_with_limit(cls, nums, 1.0)
            assert got is not TIMED_OUT, f"{cls.__name__} {nums}: 超过 1s，可能死循环"
            assert got == expected, f"{cls.__name__} {nums}: 期望 {expected}，得到 {got}"

    # 题目 n <= 10^5。只对最终解 Solution 计时，超过 1s 直接中断。
    # 本地实测：O(n) 递推 2 ~ 3ms；分治 O(n log n) 约 35ms（还要调大递归深度）；枚举所有子数组 5s 以上
    n = 100_000
    random.seed(1)
    perf_cases = [
        ("随机正负", [random.randint(-10**4, 10**4) for _ in range(n)], 3369589),
        ("全负", [-random.randint(1, 10**4) for _ in range(n)], -1),
        ("全正", [random.randint(1, 10**4) for _ in range(n)], 500143685),
        ("前半负后半正", [-10**4] * (n // 2) + [10**4] * (n // 2), 500000000),
    ]
    timings = []

    for name, nums, expected in perf_cases:
        got, elapsed = call_with_limit(Solution, nums, 1.0)
        assert got is not TIMED_OUT, f"Solution 大数据（{name}）超过 1s 被中断，可能是 O(n^2)"
        assert got == expected, f"Solution 大数据（{name}）: 期望 {expected}，得到 {got}"
        timings.append(f"{name} {elapsed * 1000:.0f} ms")

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {', '.join(timings)})")
