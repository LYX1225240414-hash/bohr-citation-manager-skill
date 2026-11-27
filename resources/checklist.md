# 引用管理自检清单（带计数，写入 verification）

## A. 输入与规则
- [ ] 已打开稿件、文献库的实际文件并记录 `sources`，未从标签/文件名推断内容
- [ ] 目标格式、引用样式、禁止改动项已写入规则表，并在第 2–5 步重读
- [ ] 需支撑论断句已逐句编号；计数：需支撑句 ___ / 已配引用句 ___

## B. 挂得对（placement_precision）
- [ ] 每条引用落在需要来源支撑的论断句上，而非段末/图注附近
- [ ] 一句多引、多句一引分别记录，且 `match_basis` 说明文献为何支撑该论断
- [ ] 抽查：按 `anchor` 找到 `evidence` 短引 ___ / ___ 条；失败项已修正或降 confidence

## C. 编得顺（numbering_continuity）
- [ ] 正文编号 ↔ 文后列表一一对应，无跳号、重复号、孤儿引用
- [ ] 交叉引用、图表注、附录引用已随插入/删除/调序同步更新
- [ ] 计数：编号连续检查 ___ / ___ 个号；异常 ___ 处（已记入 change_log）

## D. 收得净（dedupe_correctness）
- [ ] 归一化键按 DOI > 题名 > 作者+年份+venue 建立
- [ ] 中英文题名、预印本/正式版、期刊/会议版、不同导出字段差异已合并
- [ ] 同名作者不同文献未误合并，歧义项写入 uncertainties；合并 ___ 组，误合并 ___ 处

## E. 对得上（format_completeness / source_validity / claim_ref_match）
- [ ] 目标规范字段齐全：作者/年/题名/来源/卷期页/DOI/类型标识；计数完整 ___ / ___ 条
- [ ] `verified` 只有 true/false/unchecked 三态，无法核验未写成“已核实”
- [ ] 逐句判定论断与所引文献主题、结论是否匹配；匹配 ___ / ___ 条

## F. 完整性与诚实性（coverage / no_new_facts）
- [ ] 六类动作（insert/renumber/dedupe/format/verify/…）覆盖任务要求，全部章节与引用点已处理
- [ ] 未新增材料外事实、数字、DOI；引用标记与原文数值、单位、限定词一致
- [ ] `status` 与实际一致，未完成范围写明；uncertainties / change_log 非空时逐条可读

## 判定
- 全部通过 → `status: success`
- 任一计数失败且已标注人工接管位置 → `status: partial`
- 材料缺失不可执行 → `status: unable`
