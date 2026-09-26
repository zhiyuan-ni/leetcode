"""
Pattern: 原地哈希（用数组下标当哈希表）

Core:
答案一定在 [1, n + 1] 内（n 个数最多覆盖 1..n），所以只关心落在 [1, n] 的值：把值 v 换到下标 v - 1 上，再扫一遍，第一个 nums[i] != i + 1 的位置就是答案，全对上则返回 n + 1。
- Set: 建一次 set，从 1 开始逐个试。O(n) 时间但 O(n) 空间。
- Solution: 按下标交换归位，O(1) 额外空间。交换循环的条件是「目标位置上放的不是正确的值」，而不是「当前位置不对」，否则重复值会来回对调。

Time: O(n)。每次成功交换都让一个值永久归位，总交换次数 <= n
Space: Set O(n)；Solution O(1)

Mistake:
- set(nums) 写在 while 条件里，每判断一次重建一遍集合：n = 2000 时 23.2 ms（提到循环外 0.1 ms），n = 10^5 直接超时。和 238 的 nums.index(0)、128 的 min() 是同一类错。
- 「归位」写成和邻居交换（nums[i] 与 nums[i+1]）：值和下标之间没建立对应关系，[3,4,-1,1] 得到 1（期望 2）；而且缺少兜底 return。
- nums[i], nums[nums[i] - 1] = nums[nums[i] - 1], nums[i]：Python 右边先整体求值，再从左到右赋值，第二个目标的下标用的是已经改过的 nums[i]，[3,4,-1,1] 两个状态来回翻导致死循环。要先把 j = nums[i] - 1 存下来。
- 范围判断只在外层做一次：内层每交换一次 nums[i] 都会变，新值可能越界或为负（负下标会从末尾绕回去，更难查）。判断要放进 while 条件里。

易错点:
- 交换条件写成 nums[i] != i + 1：重复值会两个位置反复对调，[1,1] 死循环。
- 1..n 全都在时答案是 n + 1，不是 n。
"""


class SolutionSet:
    def firstMissingPositive(self, nums: list[int]) -> int:
        num = 1
        nums = set(nums)
        while num in nums:
            num += 1
        return num


class Solution:
    def firstMissingPositive(self, nums: list[int]) -> int:
        n = len(nums)
        for i in range(n):
            while 1 <= nums[i] <= n and nums[nums[i] - 1] != nums[i]:
                j = nums[i] - 1
                nums[i], nums[j] = nums[j], nums[i]
        for i in range(n):
            if nums[i] != i + 1:
                return i + 1
        return n + 1


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
        # 超时直接中断：交换条件写错时会死循环，这里能抓出来
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().firstMissingPositive(list(nums))
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def reference(nums):
        # 用 set 逐个试，只用于生成期望值（O(n) 额外空间，解法要 O(1)）
        s = set(nums)
        i = 1
        while i in s:
            i += 1
        return i

    cases = [
        # 题目示例
        ([1, 2, 0], 3),
        ([3, 4, -1, 1], 2),
        ([7, 8, 9, 11, 12], 1),
        # 单个元素
        ([1], 2),
        ([2], 1),
        ([0], 1),
        ([-1], 1),
        # 1..n 全在：答案是 n + 1
        ([1, 2, 3], 4),
        ([3, 2, 1], 4),
        ([2, 1], 3),
        ([5, 4, 3, 2, 1], 6),
        # 重复值：按下标归位时，重复值容易让交换循环停不下来
        ([1, 1], 2),
        ([2, 2], 1),
        ([1, 2, 2, 3], 4),
        # 只有负数 / 只有 0
        ([-1, -2, -3], 1),
        ([0, 1, 2], 3),
        # 超出 [1, n] 范围的值要被忽略
        ([1, 3], 2),
        ([2, 3, 4], 1),
        ([1, 1000000], 2),
        # 32 位边界
        ([2147483647, 1], 2),
        ([-2147483648, 1, 2], 3),
    ]

    # 随机小数据，和 set 做法对比。取值范围小且含负数和重复
    random.seed(0)
    for _ in range(500):
        nums = [random.randint(-3, 8) for _ in range(random.randint(1, 10))]
        cases.append((nums, reference(nums)))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for nums, expected in cases:
            got, _ = call_with_limit(cls, nums, 1.0)
            assert got is not TIMED_OUT, f"{cls.__name__} {nums}: 超过 1s，可能死循环（交换条件？）"
            assert got == expected, f"{cls.__name__} {nums}: 期望 {expected}，得到 {got}"

    # 题目 n <= 10^5，要求 O(n) 时间、O(1) 额外空间。
    # 只对最终解 Solution 计时，超过 0.5s 直接中断。
    # 本地实测：按下标交换归位 2 ~ 20ms，正负号标记 9 ~ 16ms，set 1 ~ 3ms（但空间 O(n)），排序 2 ~ 10ms（O(n log n)）；
    # 交换条件写成 nums[i] != i + 1 的版本在「全是 1」「含极大值」这两组会死循环，被 0.5s 中断抓到
    n = 100_000
    random.seed(1)
    perm = list(range(1, n + 1))
    random.shuffle(perm)
    miss = list(range(1, n + 1))
    miss.remove(n // 2)
    miss.append(n + 10)
    random.shuffle(miss)
    perf_cases = [
        ("1..n 打乱", perm, n + 1),
        ("缺中间一个", miss, n // 2),
        ("全负", [-random.randint(1, 10**6) for _ in range(n)], 1),
        ("全是 1", [1] * n, 2),
        ("含极大值", [random.choice([2**31 - 1, -2**31, 1, 2]) for _ in range(n)], 3),
        ("随机大范围", [random.randint(-10**9, 10**9) for _ in range(n)], 1),
    ]
    timings = []

    for name, nums, expected in perf_cases:
        got, elapsed = call_with_limit(Solution, nums, 0.5)
        assert got is not TIMED_OUT, f"Solution 大数据（{name}）超过 0.5s 被中断，可能死循环或不是 O(n)"
        assert got == expected, f"Solution 大数据（{name}）: 期望 {expected}，得到 {got}"
        timings.append(f"{name} {elapsed * 1000:.0f} ms")

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {', '.join(timings)})")
