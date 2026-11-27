# 字段字典与判定规则

## 输出字段
- `case_id`：从 `/input/case.json` 原样回填；缺失填 `N/A`。
- `status`：`success` / `partial` / `unable` / `refused`。
- `manuscript`：完整可编辑稿件，保留原段落编号与更新后的引用标记。
- `citation_actions[]`：`action_id`、`type`（insert/renumber/dedupe/format/verify）、`before`、`after`、`reason`、`anchor`、`evidence`。
- `reference_list[]`：`ref_id`、`authors`、`year`、`title`、`venue`、`doi`、`type`、`normalized_key`、`source`、`verified`。
- `citation_map[]`：`citation_id`、`claim`、`ref_id`、`position`、`match_basis`、`evidence`、`confidence`。
- `verification`：每个键含 `result`（pass/fail/na）与 `evidence`（带计数或抽查短引）。
- `uncertainties` / `sources` / `change_log`：均为数组，逐条写明位置与原因。

## 锚点格式
`p<页>:<段>`、` <章节>:<段>`、`fig<号>`、`tab<号>`、`eq<号>`、`ref:<ref_id>`。
每条 `citation_map` 必须能在其 `anchor` 位置找到 `evidence` 短引，找不到即判 fail 并回修。

## citation_actions.type 用法
| type | 触发情形 | before/after 示例 |
|---|---|---|
| insert | 论断句缺来源支撑 | 无标记 → `[3]` 插在论断句末 |
| renumber | 插入/删除/调序/合并章节后编号变化 | `[5]` → `[4]`（附交叉引用同步） |
| dedupe | 同一文献多种写法 | 两条 RN/RIS 记录 → 一条 `ref_id`，注明合并依据 |
| format | 字段补齐或格式转换 | CNKI 导出 → GB/T 7714—2015 `[J]` 条目 |
| verify | DOI/主题/结论核验 | `verified: unchecked` → `true/false` |

## 归一化键（normalized_key）
优先级：DOI（小写、去前缀）> 题名归一化（小写、去标点/空白/中英文题名互译需人工确认）> 作者首位 + 年份 + venue 归一化。
仅 DOI 一致可直接合并；题名一致但作者年份冲突时写入 `uncertainties`，不得静默合并。

## confidence
- `high`：有直接原文短引与可回查锚点，文献主题/结论明确匹配。
- `medium`：有锚点但需结合上下文判断，或元数据轻微缺失。
- `low`：材料不足、推断或存在冲突；必须同步写入 `uncertainties`。
