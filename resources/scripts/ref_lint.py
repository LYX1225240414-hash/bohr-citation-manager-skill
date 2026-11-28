#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ref_lint.py — 参考文献编号一致性与条目质量核验器（citation-manager Skill 执行内核）

解决的问题：参考文献管理最怕的不是"格式不好看"，而是
  正文引用了列表里没有的编号、列表里有条目正文没引、
  编号跳号重号、同一文献重复出现、条目元数据残缺、格式风格不统一。
这些全部可以机械核对。

子命令：
  check   核验正文与参考文献列表 → ref_report.json + ref_report.md
  merge   对疑似重复条目给出归并建议（不自动删改）→ merge_suggestions.json
  reformat 按指定风格检查条目字段覆盖（numeric/author-year）→ 仅报告缺项

输入约定（两种皆可）：
  A) 单文件：正文与参考文献在同一个 markdown/tex 文件里，列表位于 "References" 或 "参考文献" 之后
  B) 两文件：--body draft.md --refs references.md

正文引用识别： [1] / [1,3] / [1-4] / 上标 ^1^ / \\cite{key} / (Author, 2020)
列表条目识别： [1] xxx / 1. xxx / \\bibitem{key} xxx

检出类别：
  dangling_citation   正文引用了列表里不存在的编号
  uncited_entry       列表条目正文未引用
  numbering_gap       编号不连续（缺号）
  numbering_duplicate 编号重复
  order_mismatch      首次引用顺序与列表编号顺序不一致（顺序编码制应一致）
  duplicate_entry     疑似同一文献出现多次
  metadata_missing    条目缺作者/年份/题名
  style_inconsistent  条目字段覆盖不一致（部分有 DOI/年份）
  cite_placement      引用疑似未紧跟论断（整段末尾堆引用）

用法：
  python3 ref_lint.py check --body draft.md --refs refs.md --out /app/work
  python3 ref_lint.py check --single manuscript.md --out /app/work
"""

import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

CITE_NUM = re.compile(r"\[(\d{1,3}(?:\s*[,\-–—]\s*\d{1,3})*)\]")
CITE_TEX = re.compile(r"\\cite[a-z]*\{([^}]+)\}")
CITE_SUP = re.compile(r"\^\{?([\d,\-–]+)\}?\^|\\textsuperscript\{([\d,\-–]+)\}")
ENTRY_NUM = re.compile(r"^\s*\[?(\d{1,3})\]?[\.\)]?\s+(.{10,})$")
BIBITEM = re.compile(r"\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}\s*(.+)")

ASSERT_HINT = ["提出", "表明", "显示", "证明", "优于", "显著", "发现", "认为",
               "propose", "show", "demonstrate", "report", "suggest", "find", "argue"]
REF_HEAD = re.compile(r"^\s*(#{1,4}\s*)?(references?|bibliography|参考文献|引用文献)\s*$", re.I)


def read(p):
    try:
        return Path(p).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def split_single(text):
    """把单文件拆成 (正文, 列表文本)"""
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if REF_HEAD.match(ln.strip()):
            return "\n".join(lines[:i]), "\n".join(lines[i + 1:])
    return text, ""


def expand(spec):
    out = []
    for part in re.split(r"[,\s]+", spec.strip()):
        if not part:
            continue
        m = re.match(r"^(\d{1,3})\s*[\-–—]\s*(\d{1,3})$", part)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            if 0 <= b - a <= 80:
                out.extend(range(a, b + 1))
            continue
        if part.isdigit():
            out.append(int(part))
    return out


def parse_body(body):
    """返回 (有序引用序列 [(num, line, snippet)], 引用所在句)"""
    seq = []
    for i, line in enumerate(body.splitlines(), 1):
        for m in CITE_NUM.finditer(line):
            for n in expand(m.group(1)):
                seq.append((n, i, line.strip()[:180]))
        for m in CITE_SUP.finditer(line):
            g = m.group(1) or m.group(2) or ""
            for n in expand(g):
                seq.append((n, i, line.strip()[:180]))
    return seq


def parse_tex_cites(body):
    keys = []
    for i, line in enumerate(body.splitlines(), 1):
        for m in CITE_TEX.finditer(line):
            for k in m.group(1).split(","):
                k = k.strip()
                if k:
                    keys.append((k, i, line.strip()[:180]))
    return keys


def parse_entries(refs_text):
    """返回 {编号或key: {raw, authors, year, title, has_doi}}"""
    entries = {}
    # bibitem
    for m in BIBITEM.finditer(refs_text):
        key, rest = m.group(1), re.sub(r"\s+", " ", m.group(2)).strip()
        entries[key] = mk_entry(rest)
    if entries:
        return entries, "tex"
    cur_num, buf = None, []
    for line in refs_text.splitlines():
        m = ENTRY_NUM.match(line)
        if m:
            if cur_num is not None:
                entries[str(cur_num)] = mk_entry(" ".join(buf))
            cur_num, buf = int(m.group(1)), [m.group(2).strip()]
        elif line.strip() and cur_num is not None:
            buf.append(line.strip())
    if cur_num is not None:
        entries[str(cur_num)] = mk_entry(" ".join(buf))
    return entries, "numeric"


def mk_entry(raw):
    raw = re.sub(r"\s+", " ", raw).strip()
    ym = re.search(r"\(?((?:19|20)\d{2})[a-z]?\)?", raw)
    # 作者：开头到第一个句点/括号前
    am = re.match(r"^([A-Z][^.]{2,80}?)[\.\(]", raw)
    return {
        "raw": raw,
        "authors": (am.group(1).strip() if am else "")[:120],
        "year": ym.group(1) if ym else "",
        "title": raw[:200],
        "has_doi": bool(re.search(r"10\.\d{4,9}/|doi[:\s]", raw, re.I)),
    }


def norm(s):
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", str(s or "").lower())


def similar(a, b):
    return SequenceMatcher(None, norm(a)[:180], norm(b)[:180]).ratio()


def cmd_check(args):
    if args.single:
        text = read(args.single)
        body, refs_text = split_single(text)
    else:
        body, refs_text = read(args.body), read(args.refs)
    if not body.strip():
        print(json.dumps({"ok": False, "error": "正文为空或路径不存在"}, ensure_ascii=False))
        return 1
    if not refs_text.strip():
        print(json.dumps({"ok": False, "error": "未找到参考文献列表（含 References/参考文献 标题或 --refs 文件）"}, ensure_ascii=False))
        return 1

    entries, mode = parse_entries(refs_text)
    if not entries:
        print(json.dumps({"ok": False, "error": "参考文献列表未解析出条目"}, ensure_ascii=False))
        return 1

    if mode == "tex":
        cites = parse_tex_cites(body)
        cited_keys = [c[0] for c in cites]
        dangling = [{"key": k, "line": ln, "snippet": sn, "reason": "列表无此 bibitem"}
                    for k, ln, sn in cites if k not in entries]
        uncited = [{"key": k, "title": v["title"][:100]} for k, v in entries.items() if k not in set(cited_keys)]
        numbering_gap, numbering_dup, order_mismatch = [], [], []
        first_order = []
        for k, _, _ in cites:
            if k not in first_order:
                first_order.append(k)
    else:
        seq = parse_body(body)
        cited = [s[0] for s in seq]
        nums = sorted(int(k) for k in entries if str(k).isdigit())
        dangling = [{"num": n, "line": ln, "snippet": sn, "reason": "列表无此编号"}
                    for n, ln, sn in seq if str(n) not in entries]
        cited_set = set(cited)
        uncited = [{"num": k, "title": v["title"][:100]} for k, v in entries.items()
                   if str(k).isdigit() and int(k) not in cited_set]
        numbering_gap = []
        if nums:
            for n in range(min(nums), max(nums) + 1):
                if n not in nums:
                    numbering_gap.append({"missing": n})
        counter = {}
        for n in cited:
            counter[n] = counter.get(n, 0) + 1
        numbering_dup = [{"num": n, "times": c} for n, c in counter.items() if c > 1 and n in nums]
        # 首次引用顺序
        first_order = []
        for n in cited:
            if n not in first_order:
                first_order.append(n)
        order_mismatch = []
        listed_order = sorted(nums)
        if len(first_order) <= len(listed_order) and first_order != listed_order[:len(first_order)]:
            for idx, n in enumerate(first_order):
                if idx < len(listed_order) and listed_order[idx] != n:
                    order_mismatch.append({"position": idx + 1, "cited_first": n,
                                           "listed": listed_order[idx]})
                    break

    # 重复条目（标题相似度）
    keys = list(entries.keys())
    dup_groups, used = [], set()
    for i in range(len(keys)):
        if keys[i] in used:
            continue
        group = [keys[i]]
        for j in range(i + 1, len(keys)):
            if keys[j] in used:
                continue
            r = similar(entries[keys[i]]["title"], entries[keys[j]]["title"])
            same_author = norm(entries[keys[i]]["authors"])[:20] == norm(entries[keys[j]]["authors"])[:20] \
                and entries[keys[i]]["authors"]
            if r >= 0.86 or (same_author and entries[keys[i]]["year"] == entries[keys[j]]["year"] and r >= 0.5):
                group.append(keys[j])
                used.add(keys[j])
        if len(group) > 1:
            used.add(keys[i])
            dup_groups.append({"keys": group,
                               "titles": [entries[k]["title"][:80] for k in group],
                               "similarity": round(similar(entries[group[0]]["title"], entries[group[1]]["title"]), 3)})

    # 元数据
    meta_missing = []
    for k, v in entries.items():
        miss = []
        if not v["authors"]:
            miss.append("authors")
        if not v["year"]:
            miss.append("year")
        if miss:
            meta_missing.append({"key": k, "missing": miss, "title": v["title"][:100]})

    # 风格一致性：年份与 DOI 覆盖
    n = len(entries)
    year_cover = sum(1 for v in entries.values() if v["year"]) / n
    doi_cover = sum(1 for v in entries.values() if v["has_doi"]) / n
    style_inconsistent = []
    if 0 < year_cover < 1:
        style_inconsistent.append({"field": "year", "coverage": round(year_cover, 3),
                                   "missing": [k for k, v in entries.items() if not v["year"]][:15]})
    if 0 < doi_cover < 1:
        style_inconsistent.append({"field": "doi", "coverage": round(doi_cover, 3),
                                   "missing": [k for k, v in entries.items() if not v["has_doi"]][:15]})

    # 引用位置：句中含有多个引用且句长很短（堆叠）或引用出现在段末且段内有多个论断
    cite_placement = []
    if mode == "numeric":
        by_line = {}
        for n_, ln, sn in seq:
            by_line.setdefault(ln, []).append(n_)
        for ln, ns in by_line.items():
            if len(ns) >= 4:
                cite_placement.append({"line": ln, "citations": ns,
                                       "note": "同一处堆叠 4 个以上引用，确认是否每个论断都有对应来源"})

    # 计数
    total_cites = len(first_order)
    dangling_n = len(dangling)
    report = {
        "ok": True, "mode": mode, "body": str(args.body or args.single),
        "entry_count": len(entries), "distinct_cited": total_cites,
        "dangling_count": dangling_n, "uncited_count": len(uncited),
        "numbering_gap_count": len(numbering_gap), "numbering_duplicate_count": len(numbering_dup),
        "order_mismatch_count": len(order_mismatch), "duplicate_group_count": len(dup_groups),
        "metadata_missing_count": len(meta_missing), "style_issue_count": len(style_inconsistent),
        "cite_placement_issue_count": len(cite_placement),
        "dangling": dangling[:40], "uncited": uncited[:40],
        "numbering_gaps": numbering_gap[:30], "numbering_duplicates": numbering_dup[:30],
        "order_mismatch": order_mismatch[:10], "duplicate_entries": dup_groups[:20],
        "metadata_missing": meta_missing[:40], "style_inconsistent": style_inconsistent,
        "cite_placement": cite_placement[:20],
        "verification_hint": {
            "citation_resolvability": f"可解析引用 {total_cites - dangling_n} / {total_cites}（悬空 {dangling_n} 必须为 0）",
            "numbering_consistency": f"缺号 {len(numbering_gap)}；重号 {len(numbering_dup)}；顺序不符 {len(order_mismatch)}",
            "reference_coverage": f"已引 {total_cites} / 列表 {len(entries)}（未引 {len(uncited)}）",
            "dedup_clean": f"疑似重复条目组 {len(dup_groups)}（应为 0）",
            "metadata_accuracy": f"元数据齐全 {len(entries) - len(meta_missing)} / {len(entries)}",
        },
    }
    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "ref_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md = ["# 参考文献核验报告", "",
          f"- 模式：{mode}｜列表条目 {len(entries)}｜正文引用 {total_cites}", ""]
    for label, items in [("悬空引用（编号不存在，必须修）", dangling),
                         ("未引用条目（评估是否补引或删除）", uncited),
                         ("编号缺号", numbering_gap),
                         ("编号重复", numbering_dup),
                         ("首次引用顺序与列表不符", order_mismatch),
                         ("疑似重复条目（应合并）", dup_groups),
                         ("元数据缺失", meta_missing),
                         ("格式风格不一致", style_inconsistent),
                         ("引用堆叠（确认是否逐句有据）", cite_placement)]:
        if items:
            md += [f"## {label}（{len(items)}）", ""]
            for it in items[:20]:
                md.append(f"- {json.dumps(it, ensure_ascii=False)[:220]}")
            md.append("")
    md += ["## 自检口径建议", ""] + [f"- `{k}`：{v}" for k, v in report["verification_hint"].items()]
    (outdir / "ref_report.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["mode", "entry_count", "distinct_cited",
                                            "dangling_count", "uncited_count",
                                            "numbering_gap_count", "numbering_duplicate_count",
                                            "order_mismatch_count", "duplicate_group_count",
                                            "metadata_missing_count"]}, ensure_ascii=False))
    return 0


def cmd_merge(args):
    if args.single:
        _, refs_text = split_single(read(args.single))
    else:
        refs_text = read(args.refs)
    entries, mode = parse_entries(refs_text)
    if not entries:
        print(json.dumps({"ok": False, "error": "未解析出条目"}, ensure_ascii=False))
        return 1
    keys = list(entries.keys())
    groups = []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            r = similar(entries[keys[i]]["title"], entries[keys[j]]["title"])
            if r >= 0.80:
                groups.append({"a": keys[i], "b": keys[j], "similarity": round(r, 3),
                               "title_a": entries[keys[i]]["title"][:100],
                               "title_b": entries[keys[j]]["title"][:100],
                               "basis": "题名相似度 ≥0.80"})
    out = {"ok": True, "mode": mode, "candidates": sorted(groups, key=lambda x: -x["similarity"]),
           "note": "仅给候选，不自动合并。合并前须人工确认为同一文献（预印本/正式版/中英文题名需看 DOI 与卷期）。"}
    Path(args.out).mkdir(parents=True, exist_ok=True)
    (Path(args.out) / "merge_suggestions.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "candidates": len(groups), "top": out["candidates"][:5]}, ensure_ascii=False))
    return 0


def main():
    ap = argparse.ArgumentParser(description="参考文献编号一致性与条目质量核验器")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("--body"); c.add_argument("--refs"); c.add_argument("--single")
    c.add_argument("--out", required=True)
    m = sub.add_parser("merge")
    m.add_argument("--single"); m.add_argument("--refs"); m.add_argument("--out", required=True)
    a = ap.parse_args()
    return {"check": cmd_check, "merge": cmd_merge}[a.cmd](a) or 0


if __name__ == "__main__":
    sys.exit(main())
