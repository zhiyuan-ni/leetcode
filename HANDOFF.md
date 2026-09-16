# Handoff

给接手这个仓库的新 session。仓库规范见 [SPEC.md](SPEC.md)，这里只写规范之外、但下一次需要知道的信息。

## 当前进度

| 分类 | 进度 |
|---|---|
| 01_hash | 3 / 3 完成，全部 🟡 |
| 其余 15 类 | 未开始，均为空壳文件 |

- 已完成：1 Two Sum、49 Group Anagrams、128 Longest Consecutive Sequence。
- 下一题：[283. Move Zeroes](02_two_pointers/283_move_zeroes.py)。
- `notes/patterns.md` 已写 Hash 一节；`notes/mistakes.md` 有三题记录；`notes/review.md` 仍为空（还没开始二刷）。
- `templates/` 五个文件都是占位说明，按 SPEC 要等 Pattern 多次出现后再写，不要提前填。

## 用户希望的协作方式

**不要直接给答案。** 用户在自己做题，Claude 的角色是出测试、看代码、做复盘。

1. 新题开始时：讲清题意，提出引导问题，不给思路。
2. 用户说「给个提示」时，一次只给一层：先方向，再数据结构，最后才是完整解法。
3. 用户贴代码或说「看一下」时：先跑测试，再指出问题。指出问题要给出**具体反例**和**实测数据**，不要只说「可能会慢」。
4. 复杂度问题要用实际测量佐证（本地 benchmark），不要只给理论分析。
5. 用户问「LeetCode 上某写法为什么更快」时：先本地对比，再解释。多数情况是测量噪声或针对数据分布的常数优化，不是复杂度差异。
6. 改文件前先问，用户会说「你来改好并记录」才动手。用户常说「先不要提交」。

## 每题完成后的记录流程

用户确认后，一次改这几处：

1. **题目文件**：填顶部笔记（Pattern / Core / Time / Space / Mistake），保留的多解按 SPEC 命名（`SolutionBruteForce` + `Solution`）。
2. **README.md**：填 Status。状态由用户决定，不要替他判断。
3. **notes/mistakes.md**：只记他**真正犯过**的错。提前问到、没写错的内容标成「易错点」，和真实错误分开。
4. **notes/patterns.md**：同一 Pattern 做过多题后再总结。

## 测试块写法

SPEC 允许题目文件带测试块，已形成的习惯：

- 用 `assert` + 失败信息（打印输入、期望、实际），通过时打印 `ok`。
- 结果顺序不固定的题（如 49），比较前先 normalize。
- 自动发现文件里所有 `Solution*` 类并逐个测试，这样加暴力解不用改测试代码。
- 题目有复杂度要求时加性能用例，并针对**已经踩过的坑**构造数据。128 的三条：一整段、全不相邻、段首重复。
- 性能用例规模要让错误写法**快速失败**。128 的「全不相邻」用 2 万而不是 10 万，因为 O(n²) 写法在 10 万时要 2 分半才失败。

## 用户的高频问题（复盘时留意）

- **遮蔽内置名字**：已出现 `dict`、`str`、`sum`、`next` 四次。
- **`enumerate` 的计数起点**：切片后、内层循环重新计数导致下标错。
- **循环里用线性操作**（如 `min()`）导致复杂度退化。
- **遍历原数组而不是去重后的集合**。

## 环境与工具

- 仓库：https://github.com/zhiyuan-ni/leetcode ，分支 `main`，直接提交推送，不走 PR。
- 提交信息用 SPEC 第 13 节的前缀：`solve:` / `notes:` / `review:` / `template:` / `docs:` / `chore:`。规范改动和做题记录分开提交。
- 本地 Python 是 3.9（`list[int]` 注解可用）。链表 / 二叉树题的空壳文件已加 `from __future__ import annotations`，这样注释掉 Node 定义也能本地运行。
- macOS 没有 `timeout` 命令。跑可能死循环的测试要自己控制规模。
- **题目清单已核对过**：与 leetcode.cn 官方「热题 100」学习计划逐题比对，题号、标题、分类、组内顺序全部一致；函数签名与 leetcode.com 官方 Python3 模板一致。**不要再重新核对。**
- leetcode.cn 和 leetcode.com 的网页与 GraphQL 接口都会挡 curl / WebFetch（403）。需要抓取时用内置浏览器打开页面，再在页面里调用 `/graphql/`。
