"""
Pattern: Two Pointers（快慢指针）

Core:
- Swap: sec 扫描，遇到非零就和 fst 交换并 fst += 1。fst < sec 时 nums[fst] 一定是 0，交换即把 0 往后挪；fst == sec 时自己换自己也不出错。
- Solution: sec 扫描，把非零数依次覆盖到 fst 位置，扫完后把 [fst, n) 补 0。

Time:
- Swap: O(n)
- Solution: O(n)

Space:
- Swap: O(1)
- Solution: O(1)

Mistake:
- 外层条件写成 sec != n - 1：最后一个元素没被处理；sec 跳过 n - 1 后还会停不下来。
- 内层 while 找非零数没检查边界，末尾全是 0 时越界。
- 先 nums[fst] = nums[sec] 再 nums[sec] = 0：fst == sec 时把非零数清成 0。
- 判断条件写成 nums[sec] != nums[fst]：要看的是 nums[sec] 是不是 0，和 fst 位置的值无关。
- 去掉补 0 循环却只覆盖不交换：数被复制，0 丢失。
"""


class SolutionSwap:
    def moveZeroes(self, nums: list[int]) -> None:
        fst = 0
        n = len(nums)
        for sec in range(n):
            if nums[sec] != 0:
                nums[fst], nums[sec] = nums[sec], nums[fst]
                fst += 1


class Solution:
    def moveZeroes(self, nums: list[int]) -> None:
        fst = 0
        n = len(nums)
        for sec in range(n):
            if nums[sec] != 0:
                nums[fst] = nums[sec]
                fst += 1

        for i in range(fst, n):
            nums[i] = 0


if __name__ == "__main__":
    import random
    import time

    def expected_of(nums):
        return [x for x in nums if x != 0] + [0] * nums.count(0)

    cases = [
        # 题目示例
        [0, 1, 0, 3, 12],
        [0],
        # 只有一个非零元素
        [5],
        # 没有 0，数组不能被改动
        [1, 2, 3],
        # 全是 0
        [0, 0, 0],
        # 0 已经全在末尾
        [1, 2, 0, 0],
        # 0 全在开头
        [0, 0, 1, 2],
        # 连续的 0：边遍历边删除时容易跳过第二个 0
        [1, 0, 0, 2],
        # 0 在末尾且前面也有 0
        [0, 1, 0],
        # 负数和重复值，检查相对顺序
        [-1, 0, 2, -1, 0, 2],
        # 数值范围边界
        [-2**31, 0, 2**31 - 1],
    ]

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for nums in cases:
            arr = list(nums)
            ret = cls().moveZeroes(arr)
            expected = expected_of(nums)
            assert ret is None, f"{cls.__name__} {nums}: 应该原地修改并返回 None，得到返回值 {ret}"
            assert arr == expected, f"{cls.__name__} {nums}: 期望 {expected}，得到 {arr}（注意是否原地修改）"

    # 题目 n <= 10^4，但这个规模下 O(n^2) 写法（如循环里 remove(0) / pop(i)）也只要几十 ms，测不出来。
    # 这里放大到 5 万：O(n) 写法约 2ms，循环里 remove(0) 约 1.4s
    random.seed(0)
    n = 50_000

    # 一半是 0，随机分布
    half_zeros = [0 if random.random() < 0.5 else random.randint(-9, 9) or 1 for _ in range(n)]

    # 0 全在开头：每次删除开头元素都要整体搬移
    zeros_front = [0] * (n // 2) + list(range(1, n // 2 + 1))

    perf_cases = [
        ("一半是 0", half_zeros),
        ("0 全在开头", zeros_front),
    ]
    timings = []

    for name, nums in perf_cases:
        arr = list(nums)
        start = time.perf_counter()
        SolutionSwap().moveZeroes(arr)
        elapsed = time.perf_counter() - start
        assert arr == expected_of(nums), f"Solution 大数据（{name}）: 结果错误"
        assert elapsed < 0.1, f"Solution 大数据（{name}）耗时 {elapsed:.2f}s，可能不是 O(n)"
        timings.append(f"{name} {elapsed * 1000:.0f} ms")

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {', '.join(timings)})")
