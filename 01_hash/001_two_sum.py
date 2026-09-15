"""
Pattern: Hash Map

Core:
- BruteForce: 枚举所有 i < j 的下标对，内层从 i + 1 开始。
- Solution: 遍历时查 target - num 是否已在 seen 中；先查再存。

Time:
- BruteForce: O(n^2)
- Solution: O(n)

Space:
- BruteForce: O(1)
- Solution: O(n)

Mistake:
- 内层写 enumerate(nums) 会从 0 开始，j 可能等于 i，同一元素被用两次。
- enumerate(nums[i+1:]) 的 j 从 0 计数，原下标是 i + 1 + j。
"""


class SolutionBruteForce:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        n = len(nums)
        for i in range(n):
            for j in range(i + 1, n):
                if nums[i] + nums[j] == target:
                    return [i, j]


class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        seen = {}
        for i, num in enumerate(nums):
            other = target - num
            if other in seen:
                return [seen[other], i]
            seen[num] = i


if __name__ == "__main__":
    for s in (SolutionBruteForce(), Solution()):
        assert s.twoSum([2, 7, 11, 15], 9) == [0, 1]
        assert s.twoSum([3, 2, 4], 6) == [1, 2]
        assert s.twoSum([3, 3], 6) == [0, 1]
    print("ok")
