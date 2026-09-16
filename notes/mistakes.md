# Mistakes

<!--
只记录自己真正犯过的错误，按题型分组。
格式：

## <题型>

### <题目>

<为什么做错>

---
-->

## Hash

### 1. Two Sum

暴力解写内层循环时，两次都栽在 `enumerate` 的计数起点上：

- `for j, y in enumerate(nums)`：内层每轮从 0 开始，`j` 可能等于 `i`，同一个元素被用了两次。前面写的 `j = i + 1` 会被 `for` 立刻覆盖，不起作用。
- `for j, y in enumerate(nums[i+1:])`：切片是新列表，`j` 从 0 计数，原数组下标应为 `i + 1 + j`，却返回了 `i + j`。

教训：`enumerate` 给的是当前遍历对象里的位置，不一定是原数组下标。需要控制起点时用 `range(i + 1, n)`，或 `enumerate(..., start=...)`。

---

### 49. Group Anagrams

**选 key**

- 用字符编码之和作 key：`"ad"` 和 `"bc"` 都是 197，不同组被分到一起。key 必须满足「同组一定相同、不同组一定不同」，求和只满足前一半。
- `sorted(s)` 返回 list，直接作 key 报 `unhashable type: 'list'`。要转成 `"".join(sorted(s))` 或 `tuple(sorted(s))`。

**dict / list 的返回值**

- `d.get(key, []).append(s)`：默认值只是返回一个临时列表，不会存进字典，字典始终为空。要用 `d.setdefault(key, []).append(s)` 或 `defaultdict(list)`。
- `d[key] = d[key].append(s)`：`list.append` 原地修改、返回 `None`，这样会把值覆盖成 `None`。
- `return d.values` 少了括号，返回的是方法本身；而且 `.values()` 是视图，要 `list(...)`。

**写法习惯**

- 条件里用 `&` 代替 `and`：`&` 是按位与、不短路，右边的 `sorted` 总会被执行。
- `n = len(s)` 放到定义 `s` 的循环前面，导致 `NameError`。
- 又用了 `str`、`dict`、`sum` 作变量名（Two Sum 里用过 `dict`），遮蔽内置名字。

**易错点：`for ... else` 里的 `break`**

暴力解把 `ff` 标志位换成 `for ... else` 后，`break` 不能删：`else` 只在循环没被 `break` 时执行，删掉后每个串都会额外新开一组，`["eat", "tea", "ate"]` 会得到 `[['eat', 'tea', 'ate'], ['tea', 'ate'], ['ate']]`。标志位写法里 `break` 只是提前结束，删掉结果仍然正确。

---

### 128. Longest Consecutive Sequence

**复杂度**

- 用 `min(set)` 找每段的起点：`min()` 是线性扫描，每段调用一次。输入全是互不相邻的数时段数等于 n，退化成 O(n²)，实测 4 万个数要 23s。判断段首应该用 `num - 1 not in s`，O(1)。
- 外层遍历 `nums` 而不是去重后的 `set`：重复的段首会让同一段被反复数。`[1] * 50000 + list(range(1, 50001))` 这种输入直接退化成 O(n²)。

**边界**

- `cur_len` 从 0 开始计数，结果比实际长度少 1。段首本身要算一个。

**易错点：剪枝不是普通的提前返回**

LeetCode 上的快解里有 `if max_length > len(s) // 2 + 1: return max_length`。它成立的前提是各段互不重叠，剩下的元素不够组成更长的段。这类提前返回必须能证明「后续不可能更优」，否则就是 bug；它省的是计算量，和用 `return` 代替 `else` 那种写法层面的提前返回不是一回事。

---
