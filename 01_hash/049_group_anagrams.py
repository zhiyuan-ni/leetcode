"""
Pattern: Hash Map

Core:
- BruteForce: 逐个与已有各组的第一个串比较 sorted 结果，匹配就加入，否则新开一组。
- Solution: 以 "".join(sorted(s)) 作 key，dict 分组，一次遍历。

Time:
- BruteForce: O(n^2 * k log k)
- Solution: O(n * k log k)

Space:
- BruteForce: O(n * k)
- Solution: O(n * k)

Mistake:
- 字符和作 key 会冲突："ad" 与 "bc" 都是 197。key 必须唯一标识一组。
- sorted() 返回 list，不可哈希，要转 str 或 tuple。
- dict.get(key, []) 的默认值不会存进字典，要用 setdefault / defaultdict。
"""


class SolutionBruteForce:
    def groupAnagrams(self, strs: list[str]) -> list[list[str]]:
        res = []
        for s in strs:
            n = len(s)
            for e in res:
                if (len(e[0]) == n) and (sorted(s) == sorted(e[0])):
                    e.append(s)
                    break
            else:
                res.append([s])
        return res


class Solution:
    def groupAnagrams(self, strs: list[str]) -> list[list[str]]:
        res = {}
        for s in strs:
            res.setdefault("".join(sorted(s)), []).append(s)
        return list(res.values())


if __name__ == "__main__":
    def normalize(groups):
        # 组的顺序和组内顺序都不限，统一排序后再比较
        return sorted(sorted(g) for g in groups)

    cases = [
        # 题目示例
        (["eat", "tea", "tan", "ate", "nat", "bat"], [["bat"], ["nat", "tan"], ["ate", "eat", "tea"]]),
        # 只有一个空字符串
        ([""], [[""]]),
        # 只有一个字符串
        (["a"], [["a"]]),
        # 多个空字符串属于同一组
        (["", ""], [["", ""]]),
        # 完全相同的字符串属于同一组，且都要保留
        (["a", "a"], [["a", "a"]]),
        # 字母种类相同但次数不同，不是异位词
        (["aab", "abb"], [["aab"], ["abb"]]),
        # 长度不同，不是异位词
        (["ab", "a"], [["ab"], ["a"]]),
        # 互不相同，各自成组
        (["abc", "def", "ghi"], [["abc"], ["def"], ["ghi"]]),
        # 字符和相同但不是异位词，检查 key 冲突
        (["ad", "bc"], [["ad"], ["bc"]]),
    ]

    for cls in (SolutionBruteForce, Solution):
        for strs, expected in cases:
            got = cls().groupAnagrams(list(strs))
            assert got is not None, f"{cls.__name__} {strs}: 没有返回值"
            assert normalize(got) == normalize(expected), f"{cls.__name__} {strs}: 期望 {expected}，得到 {got}"
    print("ok")
