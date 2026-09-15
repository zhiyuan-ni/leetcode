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
