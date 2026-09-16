"""
Pattern: Hash Set

Core:
放进 set 去重，只从段首（num - 1 不在 set 中）向后数，每个数最多被访问两次。

Time: O(n)
Space: O(n)

Mistake:
- 用 min() 找段首：每段一次线性扫描，全不相邻时退化成 O(n^2)。
- cur_len 从 0 开始，长度少算 1。
- 外层遍历 nums 而不是 set：重复的段首会让同一段被反复数。
"""


class Solution:
    def longestConsecutive(self, nums: list[int]) -> int:
        deduplicate = set(nums)
        max_len = 0
        for num in deduplicate:
            if num-1 not in deduplicate:
                cur_len = 1
                nxt = num+1
                while nxt in deduplicate:
                    nxt += 1
                    cur_len += 1
                if cur_len > max_len:
                    max_len = cur_len
        return max_len

if __name__ == "__main__":
    import random
    import time

    cases = [
        # 题目示例
        ([100, 4, 200, 1, 3, 2], 4),
        ([0, 3, 7, 2, 5, 8, 4, 6, 0, 1], 9),
        ([1, 0, 1, 2], 3),
        # 空数组
        ([], 0),
        # 只有一个元素
        ([7], 1),
        # 全部重复，重复元素不延长序列
        ([1, 1, 1], 1),
        # 重复元素夹在序列中间
        ([1, 2, 2, 3], 3),
        # 没有任何相邻的数
        ([10, 30, 20], 1),
        # 负数和 0 跨越
        ([-2, -1, 0, 1], 4),
        # 多段序列，取最长的，且最长的不在开头
        ([1, 2, 10, 11, 12, 13, 5], 4),
        # 两段长度相同
        ([1, 2, 3, 7, 8, 9], 3),
        # 数值范围边界
        ([-10**9, 10**9, 10**9 - 1], 2),
    ]

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for nums, expected in cases:
            got = cls().longestConsecutive(list(nums))
            assert got == expected, f"{cls.__name__} {nums}: 期望 {expected}，得到 {got}"

    # 题目要求 O(n)，n 最大 10^5。只对最终解 Solution 计时
    random.seed(0)

    # 一整段连续数字：只有 1 段
    one_run = list(range(-50_000, 50_000))
    random.shuffle(one_run)

    # 全是偶数，互不相邻：每个数自成一段。找每段起点若用 min() 等线性操作会退化成 O(n^2)。
    # 这里只用 2 万个数：O(n^2) 写法约 7s（用 10^5 要等 2 分半才失败），O(n) 写法约 10ms
    all_isolated = [x * 2 for x in range(20_000)]
    random.shuffle(all_isolated)

    # 段首大量重复：外层若遍历 nums 而不是 set，这一段会被重数 5 万次，退化成 O(n^2)
    repeated_head = [1] * 50_000 + list(range(1, 50_001))
    random.shuffle(repeated_head)

    perf_cases = [
        ("一整段", one_run, 100_000),
        ("全不相邻", all_isolated, 1),
        ("段首重复", repeated_head, 50_000),
    ]
    timings = []

    for name, nums, expected in perf_cases:
        start = time.perf_counter()
        got = Solution().longestConsecutive(list(nums))
        elapsed = time.perf_counter() - start
        assert got == expected, f"Solution 大数据（{name}）: 期望 {expected}，得到 {got}"
        assert elapsed < 1.0, f"Solution 大数据（{name}）耗时 {elapsed:.2f}s，可能不是 O(n)"
        timings.append(f"{name} {elapsed * 1000:.0f} ms")

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {', '.join(timings)})")
