# 最小调用示例（示意）

仅展示字段结构与流程，非正式案例答案。真实评测由平台使用固定案例运行。

## 输入示例

```text
case_id: example-001
task: 为稿件补引用并按 GB/T 7714—2015 统一文后列表，合并重复条目
材料：稿件 manuscript.txt、文献库 refs.bib（实际运行时从 /input/case.json 给出的路径读取）
```

## 调用方式

1. 加载本目录为 Skill，按 `SKILL.md` 第 1–6 步执行。
2. 先读 `/input/case.json` 与 `/input/task.md`，再读实际稿件与文献库文件。
3. 工作文件写在 `/app/work`；尽早把 `status: partial` 骨架写到 `/app/output/result.json`。
4. 完成后写 `/app/output/result.json`、`/app/output/manuscript_edited.md`、`/app/output/reference_list.md`。

## 示意输出

见 `../resources/output_example.json`。其中所有值均为占位示例，不代表任何真实稿件或文献的整理结果。
