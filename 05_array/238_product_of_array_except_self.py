"""
Pattern: 前缀积 / 后缀积

Core:
res[i] = (i 左边所有数之积) * (i 右边所有数之积)。两个积都不含 nums[i]，所以 0 不需要特判：0 落在左边或右边时，对应的那个积自然是 0。
- ZeroCase: 先数 0 的个数分三种情况处理，非零时再用两个辅助数组求左右积。分支多、空间 O(n)。
- Solution: 第一趟把左边积写进 res，第二趟用一个变量从右往左累乘右边积。除输出外 O(1) 空间。

Time: O(n)。n = 10^5 实测约 7 ~ 10 ms；逐位重算的 O(n^2) 暴力 3 s 以上
Space: Solution 除输出外 O(1)；ZeroCase O(n)

Mistake:
- nums.index(0) 写在循环条件里：index 每次从头扫，n = 10^5 时退化成 O(n^2)，性能用例超时。提到循环外后同一组从超时降到 5.3 ms。
- 对 0 做了三种特判（没有 0 / 一个 0 / 多个 0）：前后缀写法天然覆盖，三个分支都可以删掉。

易错点:
- 前缀积不能把自己乘进去：先 p *= nums[i] 再 res[i] = p，示例会得到 [24, 24, 24, 24]。
- 不能用除法（题目要求），而且有 0 时会 ZeroDivisionError。
"""


class SolutionZeroCase:
    def productExceptSelf(self, nums: list[int]) -> list[int]:
        n = len(nums)
        cnt = nums.count(0)
        res = [0] * n
        if cnt == 1:
            prod = 1
            idx = nums.index(0)
            for i in range(n):
                if i != idx:
                    prod *= nums[i]
            res[idx] = prod
            return res
        elif cnt > 1:
            return res

        forward = [nums[0]] * (n - 1)
        for i in range(1, n - 1):
            forward[i] = nums[i] * forward[i - 1]
        backward = [nums[n - 1]] * (n - 1)
        for i in range(1, n - 1):
            backward[i] = nums[n - i - 1] * backward[i - 1]
        for i in range(1, n - 1):
            res[i] = forward[i - 1] * backward[n - i - 2]
        res[0] = backward[-1]
        res[-1] = forward[-1]
        return res


class Solution:
    def productExceptSelf(self, nums: list[int]) -> list[int]:
        n = len(nums)
        res = [1] * n
        for i in range(1, n):
            res[i] = nums[i - 1] * res[i - 1]
        cur = 1
        for i in range(n - 1, -1, -1):
            res[i] *= cur
            cur *= nums[i]
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

    def call_with_limit(cls, nums, seconds):
        # 超时直接中断，让 O(n^2) 写法快速失败
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().productExceptSelf(list(nums))
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def reference(nums):
        # 逐个位置把其余元素乘一遍，只用于生成小数据的期望值
        n = len(nums)
        out = []
        for i in range(n):
            p = 1
            for j in range(n):
                if j != i:
                    p *= nums[j]
            out.append(p)
        return out

    cases = [
        # 题目示例
        ([1, 2, 3, 4], [24, 12, 8, 6]),
        ([-1, 1, 0, -3, 3], [0, 0, 9, 0, 0]),
        # 最短输入
        ([2, 3], [3, 2]),
        ([-1, -1], [-1, -1]),
        # 恰好一个 0：只有 0 所在位置非零，其余都是 0
        ([0, 1], [1, 0]),
        ([1, 0], [0, 1]),
        ([0, 2, 3], [6, 0, 0]),
        ([2, 0, 3], [0, 6, 0]),
        ([1, 2, 0, 4], [0, 0, 8, 0]),
        # 两个及以上 0：全是 0
        ([0, 0], [0, 0]),
        ([0, 0, 0], [0, 0, 0]),
        # 负数与符号
        ([-1, 2, -3, 4], [-24, 12, -8, 6]),
        # 重复值 / 数值边界
        ([5, 5, 5], [25, 25, 25]),
        ([1, 1, 1, 1], [1, 1, 1, 1]),
        ([30, -30, 1], [-30, 30, -900]),
    ]

    # 随机小数据，和暴力结果对比。取值范围小且含 0，制造大量零和符号变化
    random.seed(0)
    for _ in range(500):
        nums = [random.randint(-4, 4) for _ in range(random.randint(2, 10))]
        cases.append((nums, reference(nums)))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for nums, expected in cases:
            got, _ = call_with_limit(cls, nums, 1.0)
            assert got is not TIMED_OUT, f"{cls.__name__} {nums}: 超过 1s，可能死循环"
            assert got is not None, f"{cls.__name__} {nums}: 返回了 None"
            assert list(got) == expected, f"{cls.__name__} {nums}: 期望 {expected}，得到 {got}"

    # 题目 n <= 10^5，且保证结果在 32 位整数范围内，所以大数据只能用 ±1 加少量小因子。
    # 只对最终解 Solution 计时，超过 0.5s 直接中断。
    # 本地实测：前后缀两次扫描 6 ~ 7ms（O(1) 额外空间），左右两个数组 11 ~ 14ms，先算总积再除 3 ~ 4ms；
    # 逐个位置重算的 O(n^2) 暴力 3s 以上
    n = 100_000
    random.seed(1)

    def expected_of(nums):
        # 用「总积 / 自己」的思路独立算一遍期望值（除法只在这里用，解法里不该用）
        zeros = nums.count(0)
        prod = 1
        for x in nums:
            if x:
                prod *= x
        if zeros > 1:
            return [0] * len(nums)
        if zeros == 1:
            return [prod if x == 0 else 0 for x in nums]
        return [prod // x for x in nums]

    few = [random.choice([1, 1, 1, 1, -1]) for _ in range(n - 4)] + [2, 3, -2, 1]
    random.shuffle(few)
    perf_cases = [
        ("全 1", [1] * n),
        ("随机 ±1", [random.choice([1, -1]) for _ in range(n)]),
        ("恰好一个 0", [random.choice([1, -1]) for _ in range(n - 1)] + [0]),
        ("两个 0", [0] + [random.choice([1, -1]) for _ in range(n - 2)] + [0]),
        ("少量 2 和 3", few),
    ]
    timings = []

    for name, nums in perf_cases:
        expected = expected_of(nums)
        got, elapsed = call_with_limit(Solution, nums, 0.5)
        assert got is not TIMED_OUT, f"Solution 大数据（{name}）超过 0.5s 被中断，可能是 O(n^2)"
        assert got is not None, f"Solution 大数据（{name}）: 返回了 None"
        got = list(got)
        assert len(got) == n, f"Solution 大数据（{name}）: 期望长度 {n}，得到 {len(got)}"
        assert got == expected, f"Solution 大数据（{name}）: 结果不对（先比对到的位置：{next(i for i in range(n) if got[i] != expected[i])}）"
        timings.append(f"{name} {elapsed * 1000:.0f} ms")

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {', '.join(timings)})")
