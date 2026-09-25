"""
Pattern: 数组原地重排

Core:
右移 k 位等价于「后 k 个搬到前面」。k 可能大于 n，先 k %= n。
- Reverse: 整体反转，再分别反转前 k 个和后 n - k 个。O(1) 空间，满足进阶要求。
- Solution: 切出后 k 个和前 n - k 个，按新位置写回原列表（写回用 nums[i] = ...，是原地修改）。

Time: O(n)。n = 10^5 实测：切片写回 2.2 ~ 2.7 ms，nums[:] = 一行切片赋值 0.3 ms，三次反转 5.0 ms
Space: Reverse O(1)；Solution O(n)（两个切片副本）。Python 里省空间的反转反而最慢，切片在 C 层完成

Mistake:
- （本题一次通过，未出错）

易错点:
- 必须原地修改：函数里 nums = ... 只是重新绑定局部名字，调用方拿到的列表没变（283 题同样的坑）。nums[:] = ... 才是改内容。
- k 要先取模：k 可以大于 n，[1,2] + k = 5 不取模会原样不动。
- nums[-k:] 在 k = 0 时取到的是整个列表而不是空列表，这里靠后面 range(0) 不执行才没出错；写 nums[n-k:] 更稳。
- 每次挪一格挪 k 次（pop + insert(0)）是 O(n * k)：n = 10^5、k = 5 万实测 1135 ms。
- 环状替换的环数是 gcd(n, k)，只走一个环会漏元素：[-1,-100,3,99] + k = 2 得到 [-1,-100,-1,99]。
"""


class SolutionReverse:
    def rotate(self, nums: list[int], k: int) -> None:
        n = len(nums)
        k %= n

        def rev(i: int, j: int) -> None:
            while i < j:
                nums[i], nums[j] = nums[j], nums[i]
                i += 1
                j -= 1

        rev(0, n - 1)
        rev(0, k - 1)
        rev(k, n - 1)


class Solution:
    def rotate(self, nums: list[int], k: int) -> None:
        n = len(nums)
        k = k % n
        r = nums[n - k:]
        l = nums[:n-k]
        for i in range(k):
            nums[i] = r[i]
        for j in range(n-k):
            nums[k+j] = l[j]


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
        # 传进去的列表必须被原地修改；超时直接中断，让 O(n * k) 写法快速失败
        arr = list(nums)
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            ret = cls().rotate(arr, k)
            return ret, arr, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, arr, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def reference(nums, k):
        # 一次挪一格，挪 k 次，只用于生成小数据的期望值
        arr = list(nums)
        for _ in range(k % len(arr) if arr else 0):
            arr.insert(0, arr.pop())
        return arr

    cases = [
        # 题目示例
        ([1, 2, 3, 4, 5, 6, 7], 3, [5, 6, 7, 1, 2, 3, 4]),
        ([-1, -100, 3, 99], 2, [3, 99, -1, -100]),
        # k = 0：数组不能被改动
        ([1, 2, 3], 0, [1, 2, 3]),
        # k 等于 / 超过 n：要先取模
        ([1, 2, 3], 3, [1, 2, 3]),
        ([1, 2, 3], 4, [3, 1, 2]),
        ([1, 2, 3], 300, [1, 2, 3]),
        ([1, 2], 5, [2, 1]),
        # 单个元素
        ([1], 0, [1]),
        ([1], 1, [1]),
        ([1], 7, [1]),
        # 两个元素
        ([1, 2], 1, [2, 1]),
        ([1, 2], 2, [1, 2]),
        # 有重复值 / 负数
        ([7, 7, 7], 2, [7, 7, 7]),
        ([1, 1, 2, 2], 1, [2, 1, 1, 2]),
        ([-1, -2, -3, -4], 1, [-4, -1, -2, -3]),
        # n 与 k 不互质：按环旋转时环数等于 gcd(n, k)，容易漏掉某些环
        ([1, 2, 3, 4, 5, 6], 2, [5, 6, 1, 2, 3, 4]),
        ([1, 2, 3, 4, 5, 6], 3, [4, 5, 6, 1, 2, 3]),
        ([1, 2, 3, 4, 5, 6], 4, [3, 4, 5, 6, 1, 2]),
    ]

    # 随机小数据，和逐格挪动的暴力结果对比
    random.seed(0)
    for _ in range(500):
        nums = [random.randint(-9, 9) for _ in range(random.randint(1, 12))]
        k = random.randint(0, 15)
        cases.append((nums, k, reference(nums, k)))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for nums, k, expected in cases:
            ret, arr, _ = call_with_limit(cls, nums, k, 1.0)
            assert ret is not TIMED_OUT, f"{cls.__name__} nums={nums} k={k}: 超过 1s，可能死循环"
            assert ret is None, f"{cls.__name__} nums={nums} k={k}: 应该原地修改并返回 None，得到 {ret}"
            assert arr == expected, f"{cls.__name__} nums={nums} k={k}: 期望 {expected}，得到 {arr}（注意是否原地修改）"

    # 题目 n <= 10^5，k <= 10^5。只对最终解 Solution 计时，超过 0.5s 直接中断。
    # 本地实测：三次反转 5 ~ 6ms，环状替换 0 ~ 7ms，切片赋值 <1ms；
    # 每次挪一格挪 k 次（pop + insert(0)）在 k = 5 万时 1135ms
    # 结果不写进文件：用 got[i] == nums[(i - k) % n] 逐点验证（抽查 200 个位置），再比总和与长度
    n = 100_000
    random.seed(1)
    base = [random.randint(-10**6, 10**6) for _ in range(n)]
    perf_cases = [("k = 5 万", 50_000), ("k = 1", 1), ("k = n", n), ("k = 3n + 7", 3 * n + 7), ("k = 0", 0)]
    timings = []

    for name, k in perf_cases:
        ret, arr, elapsed = call_with_limit(Solution, base, k, 0.5)
        assert ret is not TIMED_OUT, f"Solution 大数据（{name}）超过 0.5s 被中断，可能是每次只挪一格"
        assert ret is None, f"Solution 大数据（{name}）: 应该返回 None，得到 {ret}"
        assert len(arr) == n, f"Solution 大数据（{name}）: 长度变成了 {len(arr)}"
        assert sum(arr) == sum(base), f"Solution 大数据（{name}）: 元素总和变了，不是一个重排"
        for i in random.sample(range(n), 200):
            assert arr[i] == base[(i - k) % n], f"Solution 大数据（{name}）: 下标 {i} 期望 {base[(i - k) % n]}，得到 {arr[i]}"
        timings.append(f"{name} {elapsed * 1000:.0f} ms")

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {', '.join(timings)})")
