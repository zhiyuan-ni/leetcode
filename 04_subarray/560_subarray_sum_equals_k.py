"""
Pattern: Prefix Sum + Hash（Two Sum 变形）

Core:
[i, j) 的和 = pre[j] - pre[i]，所以「和为 k 的子数组」等价于「pre[i] = pre[j] - k」。一边累加前缀和，一边用 {前缀和: 出现次数} 记录走过的前缀和；每步先查 pre - k 的次数累加进结果，再把当前 pre 记进去。初始放 {0: 1} 代表空前缀，从下标 0 开始的子数组才算得到。

Time: O(n)
Space: O(n)，最坏时 n + 1 个前缀和互不相同

Mistake:
- 建好前缀和数组后内层仍重新扫一遍统计，整体 O(n^2)，n = 2 万超时。
- 先存再查：把 pre[i] - pre[i] 这种长度为 0 的空子数组也算进去。k != 0 时查的不是自己那个键，看不出来；[1] + k = 0 得到 2。
- 有负数时滑动窗口不成立：窗口和不随两端移动单调变化，[1, -1, 1] + k = 1 没有收缩左端的依据。
"""


class Solution:
    def subarraySum(self, nums: list[int], k: int) -> int:
        cnt = {0: 1}
        pre = res = 0
        for num in nums:
            pre += num
            res += cnt.get(pre - k, 0)
            cnt[pre] = cnt.get(pre, 0) + 1
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
        # 超时直接中断，让 O(n^2) 写法快速失败
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().subarraySum(list(nums), k)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def reference(nums, k):
        # 枚举所有子数组，只用于生成小数据的期望值
        n = len(nums)
        return sum(1 for i in range(n) for j in range(i + 1, n + 1) if sum(nums[i:j]) == k)

    cases = [
        # 题目示例
        ([1, 1, 1], 2, 2),
        ([1, 2, 3], 3, 2),
        # 单个元素
        ([1], 1, 1),
        ([1], 0, 0),
        ([-1], -1, 1),
        # 从下标 0 开始的子数组：前缀和要有「空前缀 = 0」
        ([1, 2, 3], 6, 1),
        ([1, 2, 3], 7, 0),
        # k = 0 与 0 元素：同一个前缀和出现多次，要计次数而不是只记「出现过」
        ([0], 0, 1),
        ([0, 0, 0], 0, 6),
        ([1, -1, 0], 0, 3),
        ([5, -5, 5, -5], 0, 4),
        # 负数：滑动窗口不适用
        ([1, -1, 1], 1, 3),
        ([-1, -1, 1], 0, 1),
        ([-1000, -1000, -1000], -1000, 3),
        # 多个子数组重叠
        ([3, 4, 7, 2, -3, 1, 4, 2], 7, 4),
        ([1, 2, 1, 2, 1], 3, 4),
        # 数值边界
        ([1000, 1000, 1000], 3000, 1),
    ]

    # 随机小数据，和暴力结果对比。取值范围小且有正有负，制造大量重复前缀和
    random.seed(0)
    for _ in range(500):
        nums = [random.randint(-3, 3) for _ in range(random.randint(1, 12))]
        k = random.randint(-4, 4)
        cases.append((nums, k, reference(nums, k)))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for nums, k, expected in cases:
            got, _ = call_with_limit(cls, nums, k, 1.0)
            assert got is not TIMED_OUT, f"{cls.__name__} nums={nums} k={k}: 超过 1s，可能死循环"
            assert got == expected, f"{cls.__name__} nums={nums} k={k}: 期望 {expected}，得到 {got}"

    # 题目 n <= 2 * 10^4。只对最终解 Solution 计时，超过 1s 直接中断。
    # 本地实测：前缀和 + 哈希 1 ~ 2ms；固定起点往右累加的 O(n^2) 暴力 5s 以上
    n = 20_000
    random.seed(1)
    perf_cases = [
        ("随机正负", [random.randint(-1000, 1000) for _ in range(n)], 500, 4249),
        ("全 0，k = 0", [0] * n, 0, 200010000),
        ("1 和 -1 交替，k = 0", [1 if i % 2 == 0 else -1 for i in range(n)], 0, 100000000),
        ("全 1，k = 100", [1] * n, 100, 19901),
        ("全是 1000，k = 10^7", [1000] * n, 10**7, 10001),
    ]
    timings = []

    for name, nums, k, expected in perf_cases:
        got, elapsed = call_with_limit(Solution, nums, k, 1.0)
        assert got is not TIMED_OUT, f"Solution 大数据（{name}）超过 1s 被中断，可能是 O(n^2)"
        assert got == expected, f"Solution 大数据（{name}）: 期望 {expected}，得到 {got}"
        timings.append(f"{name} {elapsed * 1000:.0f} ms")

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {', '.join(timings)})")
