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
