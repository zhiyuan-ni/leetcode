"""
Pattern: 单调队列（滑动窗口最大值）

Core:
队列存下标，对应的值从大到小。新数进来时，右端所有 <= 它的下标都可以扔掉：它们更靠左（更早过期）且更小，永远轮不到它们当最大值。队首就是当前窗口最大值，过期（下标滑出窗口）时从左端弹出。
- OnePass: 按窗口右端 i 遍历，i >= k - 1 时开始记录答案，前 k 个数不用单独初始化，过期条件 q[0] <= i - k。
- Solution: 先把前 k 个数入队，再按窗口左端 i 遍历，过期条件 q[0] < i。

Time: O(n)，每个下标最多入队、出队各一次
Space: O(k)

Mistake:
- 新数淘汰的是右端，不是左端：写成 while cur >= nums[q[0]]: q.popleft() 会把还在窗口里的最大值弹掉，且弹空后 q[0] 报 IndexError（缺 q and 判空）。
- 初始队列写成 deque(range(k))：队列里的值必须单调递减，前 k 个数也要走一遍入队流程。
- 左端弹出是有条件的（队首过期才弹），不能每轮无条件 popleft。
- 过期条件和 i 的基准必须一致：i 是右端用 q[0] <= i - k，i 是左端用 q[0] < i。混用会让结果整体错位一格。
"""


from collections import deque


class SolutionOnePass:
    """统一按窗口右端 i 遍历，前 k 个数不用单独初始化。"""

    def maxSlidingWindow(self, nums: list[int], k: int) -> list[int]:
        q = deque()
        res = []
        for i, x in enumerate(nums):
            while q and nums[q[-1]] <= x:
                q.pop()
            q.append(i)
            if q[0] <= i - k:
                q.popleft()
            if i >= k - 1:
                res.append(nums[q[0]])
        return res


class Solution:
    def maxSlidingWindow(self, nums: list[int], k: int) -> list[int]:
        n = len(nums)
        q = deque()

        j = 0
        while j < k:
            while q and nums[j] >= nums[q[-1]]:
                q.pop()
            q.append(j)
            j += 1

        res = [nums[q[0]]]
        for i in range(1, n - k + 1):
            cur = nums[i+k-1]
            while q and cur >= nums[q[-1]]:
                q.pop()
            q.append(i+k-1)
            if q[0] < i:
                q.popleft()
            res.append(nums[q[0]])
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

    def call_with_limit(cls, nums, k, seconds):
        # 超时直接中断，让每个窗口重新取 max 的写法快速失败
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().maxSlidingWindow(list(nums), k)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def reference(nums, k):
        # 每个窗口取 max，只用于生成小数据的期望值
        return [max(nums[i:i + k]) for i in range(len(nums) - k + 1)]

    cases = [
        # 题目示例
        ([1, 3, -1, -3, 5, 3, 6, 7], 3, [3, 3, 5, 5, 6, 7]),
        ([1], 1, [1]),
        # k = 1：每个窗口就是元素自己
        ([9, 8, 7], 1, [9, 8, 7]),
        ([1, -1], 1, [1, -1]),
        # k = n：只有一个窗口
        ([1, 2, 3], 3, [3]),
        ([2, 1, 2], 3, [2]),
        ([10000, -10000], 2, [10000]),
        # 相等的值：弹右端时用 <= 还是 <，都要能得到正确结果
        ([2, 2, 2], 2, [2, 2]),
        ([-7, -8, 7, 5, 7, 1, 6, 0], 4, [7, 7, 7, 7, 7]),
        # 单调递减：最大值每一步都离开窗口，队列会一直有 k 个下标
        ([5, 4, 3, 2, 1], 2, [5, 4, 3, 2]),
        ([-1, -2, -3], 2, [-1, -2]),
        # 单调递增：每个新数都把队列清空
        ([1, 2, 3, 4, 5], 2, [2, 3, 4, 5]),
        # 最大值离开后要能接上次大的
        ([7, 2, 4], 2, [7, 4]),
        ([1, 3, 1, 2, 0, 5], 3, [3, 3, 2, 5]),
    ]

    # 随机小数据，和暴力结果对比。取值范围小，制造大量相等的值
    random.seed(0)
    for _ in range(500):
        nums = [random.randint(-5, 5) for _ in range(random.randint(1, 12))]
        k = random.randint(1, len(nums))
        cases.append((nums, k, reference(nums, k)))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for nums, k, expected in cases:
            got, _ = call_with_limit(cls, nums, k, 1.0)
            assert got is not TIMED_OUT, f"{cls.__name__} nums={nums} k={k}: 超过 1s，可能死循环"
            assert got is not None, f"{cls.__name__} nums={nums} k={k}: 返回了 None"
            assert list(got) == expected, f"{cls.__name__} nums={nums} k={k}: 期望 {expected}，得到 {got}"

    # 题目 n <= 10^5。只对最终解 Solution 计时，超过 1s 直接中断。
    # 本地实测：单调队列 10 ~ 14ms；每个窗口重新 max() 在 k = 5 万时 5s 以上。
    # 用 list 代替 deque（pop(0) 是 O(k)）在「递减 k = 5 万」这组要 300ms，能过但明显更慢。
    # 结果太长不写进文件：先比长度和总和，再抽查若干位置
    n = 100_000
    random.seed(1)
    perf_cases = [
        ("随机 k = 5 万", [random.randint(-10**4, 10**4) for _ in range(n)], 50_000, 50001, 499989953),
        ("随机 k = 3", [random.randint(-10**4, 10**4) for _ in range(n)], 3, 99998, 499130980),
        ("递减 k = 5 万", list(range(n, 0, -1)), 50_000, 50001, 3750075000),
        ("递增 k = 5 万", list(range(n)), 50_000, 50001, 3750024999),
        ("全相同 k = 2", [7] * n, 2, 99999, 699993),
        ("k = 1", [random.randint(-10**4, 10**4) for _ in range(n)], 1, 100000, 175481),
        ("k = n", [random.randint(-10**4, 10**4) for _ in range(n)], n, 1, 10000),
    ]
    timings = []

    for name, nums, k, expected_len, expected_sum in perf_cases:
        got, elapsed = call_with_limit(Solution, nums, k, 1.0)
        assert got is not TIMED_OUT, f"Solution 大数据（{name}）超过 1s 被中断，可能对每个窗口重新取 max"
        assert got is not None, f"Solution 大数据（{name}）: 返回了 None"
        got = list(got)
        assert len(got) == expected_len, f"Solution 大数据（{name}）: 期望长度 {expected_len}，得到 {len(got)}"
        assert sum(got) == expected_sum, f"Solution 大数据（{name}）: 总和期望 {expected_sum}，得到 {sum(got)}"
        for i in random.sample(range(expected_len), min(20, expected_len)):
            assert got[i] == max(nums[i:i + k]), f"Solution 大数据（{name}）: 第 {i} 个窗口期望 {max(nums[i:i + k])}，得到 {got[i]}"
        timings.append(f"{name} {elapsed * 1000:.0f} ms")

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {', '.join(timings)})")
