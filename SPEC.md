# LeetCode Hot100 Repository Spec

## 1. Purpose

本仓库用于系统刷完并复习 LeetCode Hot 100。

目标不是收集尽可能多的题解，而是形成一套可长期复用的算法知识结构：

* 按题型组织题目
* 保存每题最终可提交代码
* 记录真正遇到的错误
* 从重复出现的解法中提炼算法模板
* 支持一刷、二刷和面试前快速复习

核心原则：

**题目只是样本，最终需要记住的是 Pattern。**

## 2. Scope

当前仓库只覆盖：

* LeetCode Hot 100
* Python 3
* 面试常见算法与数据结构
* 个人刷题记录、错误和总结

暂不扩展到：

* LeetCode 全题库
* 周赛 / 竞赛题
* Java / C++ 等其他语言
* 算法理论教材式笔记
* 每题完整长篇题解

完成 Hot 100 至少一轮后，再决定是否扩大仓库范围。

## 3. Repository Structure

```text
leetcode-hot100/
├── README.md
├── SPEC.md
│
├── notes/
│   ├── patterns.md
│   ├── mistakes.md
│   └── review.md
│
├── templates/
│   ├── binary_search.py
│   ├── sliding_window.py
│   ├── bfs_dfs.py
│   ├── backtracking.py
│   └── union_find.py
│
├── 01_hash/
├── 02_two_pointers/
├── 03_sliding_window/
├── 04_subarray/
├── 05_array/
├── 06_matrix/
├── 07_linked_list/
├── 08_binary_tree/
├── 09_graph/
├── 10_backtracking/
├── 11_binary_search/
├── 12_stack/
├── 13_heap/
├── 14_greedy/
├── 15_dynamic_programming/
└── 16_tricks/
```

题型目录以 Hot 100 官方分类为主要参考。

如果一道题同时属于多个题型，只放入最主要的 Pattern 对应目录，不复制文件。

## 4. Problem File Convention

每道题对应一个 Python 文件。

文件名格式：

```text
<leetcode_id>_<snake_case_problem_name>.py
```

例如：

```text
001_two_sum.py
049_group_anagrams.py
128_longest_consecutive_sequence.py
```

LeetCode ID 使用三位补零格式。

## 5. Problem File Content

每个文件只包含两部分：

1. 简短复习笔记
2. 最终 Solution

示例：

```python
"""
Pattern: Hash Map

Core:
遍历 nums 时检查 target - num 是否已经出现。

Time: O(n)
Space: O(n)

Mistake:
- 必须先查询再插入，否则可能使用同一个元素两次。
"""


class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        seen = {}

        for i, num in enumerate(nums):
            need = target - num

            if need in seen:
                return [seen[need], i]

            seen[num] = i
```

文件顶部笔记应尽量控制在能够快速复习的长度。

不复制完整题目描述。

不写长篇教程。

## 6. README

`README.md` 是整个 Hot 100 的进度入口。

需要包含：

* 所有 Hot 100 题目
* 按题型分类
* 当前完成状态
* 是否需要复习

推荐状态：

```text
✅ Independent
独立完成。

🟡 Hint
需要提示后完成。

🔴 Solution
查看答案后完成。
```

示例：

```markdown
## Hash

| Problem | Status | Review |
|---|---|---|
| 1. Two Sum | ✅ | |
| 49. Group Anagrams | 🟡 | |
| 128. Longest Consecutive Sequence | 🔴 | Yes |
```

`Status` 表示本轮完成方式。

`Review` 用于标记需要再次练习的题。

## 7. notes/patterns.md

用于记录跨题复用的算法 Pattern。

重点回答：

**看到什么特征时，应该想到什么算法？**

示例：

```markdown
# Patterns

## Hash Map

看到：

- 判断元素是否出现过
- 查找另一个对应元素
- 频率统计
- value 与 index 的映射

优先考虑：

- dict
- set

---

## Sliding Window

看到：

- 连续子数组
- 连续子串
- 最长 / 最短区间
- 区间需要持续满足某种条件

优先考虑：

- left
- right
- window state
```

只记录已经通过实际题目理解过的 Pattern。

不要提前从网上复制大量内容。

## 8. notes/mistakes.md

该文件只记录自己真正犯过的错误。

这是仓库中优先级最高的复习资料之一。

示例：

~~~~markdown
# Mistakes

## Hash

### Two Sum

先插入当前元素再检查补数时，可能错误地使用同一个元素两次。

---

## Binary Search

经常混淆：

```python
while left <= right:
```

与：

```python
while left < right:
```

需要先明确搜索区间是：

* `[left, right]`
* `[left, right)`
~~~~

不要记录从未犯过的理论错误。

## 9. notes/review.md

用于记录二刷及后续复习。

推荐格式：

```markdown
# Review

## 2026-09-20

### Failed

- 128 Longest Consecutive Sequence
- 76 Minimum Window Substring

### Weak

- 3 Longest Substring Without Repeating Characters

### Solid

- 1 Two Sum
- 49 Group Anagrams
```

目标是快速看到：

* 哪些题完全不会
* 哪些题思路不稳定
* 哪些题已经形成条件反射

## 10. templates/

模板只能在一个算法 Pattern 已经多次出现后创建。

例如做过多道滑动窗口题以后，再整理：

```python
left = 0

for right in range(len(nums)):
    # add nums[right]

    while window_invalid:
        # remove nums[left]
        left += 1

    # update answer
```

模板的作用是总结规律，而不是提前背答案。

禁止：

* 第一轮开始前批量复制模板
* 保存大量没有实际使用过的代码模板

## 11. Solving Workflow

每道题遵循以下流程：

```text
Read Problem
    ↓
Identify Pattern
    ↓
Attempt Solution
    ↓
Run / Debug
    ↓
Submit
    ↓
Record Status
    ↓
Write Short Note
    ↓
Record Mistake if Necessary
```

第一次做题时：

* 先自己分析
* 没有思路可以看提示
* 仍无法解决则查看标准答案
* 理解答案后关闭参考资料重新实现一次

重点不是第一次是否独立 AC，而是是否真正理解。

## 12. Review Workflow

### First Pass

目标：

* 接触所有 Hot 100 常见 Pattern
* 能理解标准答案
* 熟悉 Python 常见算法写法

允许频繁查看答案。

### Second Pass

目标：

* 尽量不看题解
* 根据题目特征识别 Pattern
* 独立完成主要代码

重点关注：

* `🔴 Solution`
* `🟡 Hint`
* `Review = Yes`

### Third Pass / Interview Review

随机抽题。

要求：

1. 先口述算法思路
2. 给出时间复杂度
3. 给出空间复杂度
4. 再开始写代码

目标不是记住某一道题，而是形成：

```text
Problem Feature
        ↓
Pattern Recognition
        ↓
Algorithm Template
        ↓
Implementation
```

## 13. Git Convention

推荐每完成一组有意义的修改后提交。

示例：

```text
solve: add two sum
solve: finish hash problems
review: update sliding window notes
notes: add binary search mistakes
template: add sliding window pattern
```

不要求一题一个 commit。

避免无意义提交，例如：

```text
update
fix
test
123
```

## 14. Design Principles

### Keep Notes Short

每题笔记的目标是：

几秒钟内重新想起核心思路。

不是重新阅读一篇教程。

### Record Personal Mistakes

网上已有大量优秀题解。

本仓库最有价值的信息是：

自己曾经为什么做错。

### Learn Patterns, Not Answers

最终目标不是记住：

LeetCode 3 怎么做。

而是看到：

最长连续子串 + 不允许重复

能够想到：

Sliding Window。

### Templates Must Be Earned

模板来自多道题后的归纳。

不是刷题开始前需要背诵的内容。

## 15. Completion Criteria

Hot 100 第一轮完成：

* 100 道题全部完成
* 每题都有最终可运行代码
* 每题都有状态记录
* 重要错误进入 `mistakes.md`
* 已明显重复出现的算法进入 `patterns.md`

Hot 100 第二轮完成：

* 大部分 Easy / Medium 可以独立完成
* 常见 Pattern 能够快速识别
* 不再依赖记忆具体题解
* 能解释主要解法的时间和空间复杂度

仓库最终应该成为：

**一份属于自己的 Hot 100 代码库、错题本和算法 Pattern 手册。**
