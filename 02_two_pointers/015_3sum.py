"""
Pattern: Two Pointers（排序 + 对撞指针）

Core:
- HashSet: 固定 nums[i]，在 i 后面用「先查再放」的 seen 找两数之和为 -nums[i]；seen 只含 (i, j) 之间的数，三个下标天然不同。三元组排序后转 tuple 放进 set 去重。
- Count: Counter 计数后只在不同的值上枚举，按「几个值相同」分四类：(0,0,0)、(v,v,-2v)、(v,-v/2,-v/2)、v<c<b 三个都不同。外层只枚举负数 v 作最小值；三个都不同时 b 只需在 (-v/2, -2v) 内枚举并查 c = -v-b 是否存在，区间保证严格递增，天然无重复。
- Solution: 先排序，固定 a = nums[i]，l、r 从两端向中间找 b + c = -a：和小移 l，和大移 r。去重靠跳过相同值：a 处理完跳过所有相同的 a；找到一组后 l 跳过所有相同的 b。a > 0 时后面不可能和为 0，直接结束。

Time:
- HashSet: O(n^2)，每次命中还要排序 + 建 tuple；重复值多时命中次数远多于结果组数（全是 0 时命中 450 万次，结果 1 组）
- Count: O(n + m^2)，m 为不同值个数；n = 3000 随机数据实测约 30 ms，双指针约 150 ~ 350 ms。快在只枚举不同值、区间更窄、每步只查一次字典，复杂度不变
- Solution: O(n^2)，排序 O(n log n)

Space:
- HashSet: O(n)
- Count: O(m)
- Solution: O(n)，sorted 复制了一份；结果不计

Mistake:
- 想「找到一组就从 nums 里删掉」：一个数可以属于多组，删掉会漏解；只删一份又去不掉重复。
- sorted(tuple(...)) 顺序反了，sorted 总是返回 list，不可哈希。
- HashSet 第一版 j 从头遍历、seen 放在循环外不清空，同一元素被用多次。
- 双指针：第二个判断写成 if 而不是 elif，和不为 0 也进了 else；r 分支判断 nums[l]（和 11 题同一个复制错误）；内层 while 没有边界检查。
- 在 for i in range(n) 里改 i 不生效；tuple(a, b, c) 用法错误，应写 (a, b, c)。
"""
from bisect import bisect_left, bisect_right
from collections import Counter


class SolutionHashSet:
    def threeSum(self, nums: list[int]) -> list[list[int]]:
        res = set()
        n = len(nums)
        for i in range(n):
            a = nums[i]
            seen = set()
            for j in range(i + 1, n):
                b = nums[j]
                c = -a - b
                if c in seen:
                    res.add(tuple(sorted([a, b, c])))
                seen.add(b)
        return [list(t) for t in res]


class SolutionCount:
    def threeSum(self, nums: list[int]) -> list[list[int]]:
        cnt = Counter(nums)
        res = []
        if cnt[0] >= 3:
            res.append([0, 0, 0])
        vals = sorted(cnt)
        for v in vals:
            if v >= 0:
                break
            if cnt[v] >= 2 and -2 * v in cnt:
                res.append([v, v, -2 * v])
            if v % 2 == 0 and cnt[-v // 2] >= 2:
                res.append([v, -v // 2, -v // 2])
            lo = bisect_right(vals, -v // 2)
            hi = bisect_left(vals, -2 * v)
            for b in vals[lo:hi]:
                if -v - b in cnt:
                    res.append([v, -v - b, b])
        return res


class Solution:
    def threeSum(self, nums: list[int]) -> list[list[int]]:
        n = len(nums)
        nums = sorted(nums)
        res = []
        i = 0
        while i < n:
            a = nums[i]
            if a > 0:
                break
            l, r = i + 1, n - 1
            while l < r:
                b = nums[l]
                c = nums[r]
                s = a + b + c
                if s < 0:
                    l += 1
                elif s > 0:
                    r -= 1
                else:
                    res.append([a, b, c])
                    while l < r and nums[l] == b:
                        l += 1
            while i < n and nums[i] == a:
                i += 1
        return res


if __name__ == "__main__":
    import random
    import signal
    import time
    from collections import Counter
    from itertools import combinations

    class Timeout(Exception):
        pass

    def _on_alarm(signum, frame):
        raise Timeout

    signal.signal(signal.SIGALRM, _on_alarm)
    TIMED_OUT = object()  # 和「忘了 return」得到的 None 区分开

    def call_with_limit(cls, nums, seconds):
        # 超时直接中断，让 O(n^3) 写法快速失败
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().threeSum(list(nums))
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def normalize(triplets):
        # 三元组之间、三元组内部的顺序都不限，统一排序后再比较
        return sorted(tuple(sorted(t)) for t in triplets)

    def check(cls_name, nums, got, expected_count):
        # 逐项检查，报错时指出具体是哪一种问题
        label = f"{cls_name} {nums if len(nums) <= 20 else f'(n={len(nums)})'}"
        assert got is not None, f"{label}: 返回了 None"
        available = Counter(nums)
        for t in got:
            assert len(t) == 3, f"{label}: {t} 不是三个数"
            assert sum(t) == 0, f"{label}: {t} 的和不是 0"
            assert not Counter(t) - available, f"{label}: {t} 用到的数超过了 nums 里的个数（同一个元素被用了多次？）"
        norm = normalize(got)
        dup = [t for t, c in Counter(norm).items() if c > 1]
        assert not dup, f"{label}: 有重复的三元组，例如 {list(dup[0])}"
        assert len(norm) == expected_count, f"{label}: 期望 {expected_count} 组，得到 {len(norm)} 组（漏了）"

    def reference(nums):
        # 暴力枚举，只用于生成小数据的期望值
        return sorted({tuple(sorted(t)) for t in combinations(nums, 3) if sum(t) == 0})

    cases = [
        # 题目示例
        ([-1, 0, 1, 2, -1, -4], [[-1, -1, 2], [-1, 0, 1]]),
        ([0, 1, 1], []),
        ([0, 0, 0], [[0, 0, 0]]),
        # 多于三个 0，只算一组
        ([0, 0, 0, 0], [[0, 0, 0]]),
        # 全是正数 / 全是负数
        ([1, 2, 3], []),
        ([-3, -2, -1], []),
        # 同一个值出现两次，可以合法地各用一次
        ([-1, -1, 2], [[-1, -1, 2]]),
        ([-4, 2, 2], [[-4, 2, 2]]),
        # 同一个元素不能用两次：-1 + -1 + 2 = 0，但只有一个 -1
        ([-1, 2, 0], []),
        ([-2, 1, 3], []),
        # 大量重复值
        ([-2, 0, 0, 2, 2], [[-2, 0, 2]]),
        ([-1, -1, -1, 2, 2], [[-1, -1, 2]]),
        ([-1, 0, 1, 0], [[-1, 0, 1]]),
        # 同一个固定值对应多组
        ([3, 0, -2, -1, 1, 2], [[-2, -1, 3], [-2, 0, 2], [-1, 0, 1]]),
        ([-2, 0, 1, 1, 2], [[-2, 0, 2], [-2, 1, 1]]),
        # 数值范围边界
        ([-100000, 50000, 50000], [[-100000, 50000, 50000]]),
    ]

    # 随机小数据，和暴力结果对比。取值范围小，制造大量重复值
    random.seed(0)
    for _ in range(500):
        nums = [random.randint(-5, 5) for _ in range(random.randint(3, 10))]
        cases.append((nums, [list(t) for t in reference(nums)]))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for nums, expected in cases:
            got, _ = call_with_limit(cls, nums, 1.0)
            assert got is not TIMED_OUT, f"{cls.__name__} {nums}: 超过 1s，可能死循环"
            check(cls.__name__, nums, got, len(expected))
            assert normalize(got) == normalize(expected), f"{cls.__name__} {nums}: 期望 {expected}，得到 {got}"

    # 题目 n <= 3000，要求 O(n^2)。只对最终解 Solution 计时，超过 3s 直接中断。
    # 本地实测：O(n^2) 写法 0.2 ~ 0.5s；O(n^3) 暴力每组都要几分钟；
    # 找到后用 `if t not in res` 在列表里查重，结果多时退化，「小范围随机」要 8s 以上。
    # 期望组数是事先用正确解算好的；check 会逐项验证合法、无重复，再比组数，三者合起来等价于结果完全正确
    n = 3000
    random.seed(1)
    perf_cases = [
        ("大范围随机", [random.randint(-10**5, 10**5) for _ in range(n)], 16377),
        ("小范围随机", [random.randint(-1500, 1500) for _ in range(n)], 277427),
        ("全是 0", [0] * n, 1),
        ("少量值大量重复", [random.choice([-2, -1, 0, 1, 2]) for _ in range(n)], 5),
        ("全是正数", [random.randint(1, 10**5) for _ in range(n)], 0),
    ]
    timings = []

    for name, nums, expected_count in perf_cases:
        got, elapsed = call_with_limit(Solution, nums, 3.0)
        assert got is not TIMED_OUT, f"Solution 大数据（{name}）超过 3s 被中断，可能不是 O(n^2)"
        check(f"Solution 大数据（{name}）", nums, got, expected_count)
        timings.append(f"{name} {elapsed * 1000:.0f} ms")

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {', '.join(timings)})")
