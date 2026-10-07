#!/usr/bin/env python3
"""检查本任务文档完整性；不运行参赛程序或调用外部服务。"""

import ast
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse


TASK = Path(__file__).resolve().parents[1]
DOCS = TASK.parent
REPORT = TASK / "evidence/qa-report.json"
MANIFEST = TASK / "evidence/source-manifest.json"
EXPECTED = [
    "00-README.md", "01-参赛规则与时间表.md", "02-运行环境与模型限制.md",
    "03-输入输出与引用契约.md", "04-评分机制与失败条件.md",
    "05-数据模型许可与训练政策.md", "06-本地验证与提交操作.md",
    "07-模块与Phase计划.md", "08-硬性要求检查清单.md", "09-开发进度记录.md",
    "10-问题与决策.md", "11-Linear映射.md", "12-官方来源与版本基线.md",
]
errors = []
counts = {"markdown_files": 0, "local_links": 0, "json_examples": 0,
          "python_examples": 0, "github_source_links": 0, "source_hashes": 0}
texts = {}

for name in EXPECTED:
    if not (TASK / name).is_file():
        errors.append(f"缺少任务文档：{name}")

for path in sorted(DOCS.rglob("*.md")):
    text = path.read_text(encoding="utf-8")
    texts[path] = text
    counts["markdown_files"] += 1
    if not text.startswith("# "):
        errors.append(f"缺少顶层标题：{path.name}")
    if not text.endswith("\n"):
        errors.append(f"缺少末尾换行：{path.name}")
    if text.count("```") % 2:
        errors.append(f"代码围栏未配对：{path.name}")
    for number, line in enumerate(text.splitlines(), 1):
        if line.rstrip() != line:
            errors.append(f"尾部空白：{path.name}:{number}")
    for target in re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", text):
        target = target.strip("<>")
        if urlparse(target).scheme or target.startswith("#"):
            continue
        counts["local_links"] += 1
        local = path.parent / unquote(target.split("#")[0])
        if not local.exists() and local.resolve() != REPORT.resolve():
            errors.append(f"本地链接不存在：{path.name} -> {target}")
    for language, code in re.findall(r"```([^\n]*)\n(.*?)\n```", text, re.S):
        try:
            if language.strip() == "json":
                json.loads(code)
                counts["json_examples"] += 1
            elif language.strip() == "python":
                ast.parse(code)
                counts["python_examples"] += 1
            elif language.strip() in {"bash", "sh"}:
                for py in re.findall(r"python(?:3(?:\.\d+)?)?\s+-\s+<<'PY'\n(.*?)\nPY", code, re.S):
                    ast.parse(py)
                    counts["python_examples"] += 1
        except (ValueError, SyntaxError) as exc:
            errors.append(f"示例语法：{path.name}: {exc}")

manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
repo_by_name = {r["name"]: r for r in manifest["repositories"]}
for record in manifest["files"]:
    repository = repo_by_name[record["repository"]]
    try:
        result = subprocess.run(
            ["git", "-C", repository["research_checkout"], "show",
             f'{record["revision"]}:{record["path"]}'],
            capture_output=True, check=True,
        )
        digest = hashlib.sha256(result.stdout).hexdigest()
        counts["source_hashes"] += 1
        if digest != record["sha256"]:
            errors.append(f'来源哈希变动：{record["repository"]}/{record["path"]}')
    except (OSError, subprocess.CalledProcessError) as exc:
        errors.append(f'来源检出不可读：{record["repository"]}/{record["path"]}: {exc}')

github_urls = set()
for text in texts.values():
    github_urls.update(re.findall(r"https://github\.com/Agenthon-2026/[^\s)<>]+", text))
for url in sorted(github_urls):
    pieces = urlparse(url).path.strip("/").split("/")
    if len(pieces) < 5 or pieces[2] not in {"blob", "tree"}:
        continue
    name, revision, relative = pieces[1], pieces[3], unquote("/".join(pieces[4:]))
    repository = repo_by_name.get(name)
    if repository is None:
        errors.append(f"未登记来源仓库：{url}")
        continue
    revision = "origin/main" if revision == "main" and name == "Agenthon2026-public" else revision
    result = subprocess.run(
        ["git", "-C", repository["research_checkout"], "cat-file", "-e", f"{revision}:{relative}"],
        capture_output=True,
    )
    counts["github_source_links"] += 1
    if result.returncode:
        errors.append(f"GitHub来源路径不存在：{url}")

hong_kong = timezone(timedelta(hours=8))
aoe = timezone(timedelta(hours=-12))
date_checks = {
    "registration_development_close": (
        datetime(2026, 10, 12, 23, 59, tzinfo=aoe), "2026-10-13 19:59"),
    "last_development_start": (
        datetime(2026, 10, 12, 20, 0, tzinfo=timezone.utc), "2026-10-13 04:00"),
    "final_close": (
        datetime(2026, 10, 25, 23, 59, tzinfo=aoe), "2026-10-26 19:59"),
}
converted = {}
for key, (original, expected) in date_checks.items():
    converted[key] = original.astimezone(hong_kong).strftime("%Y-%m-%d %H:%M")
    if converted[key] != expected:
        errors.append(f"时区换算错误：{key}")

# 独立核对文档公式中的数值例子，不执行官方 scorer。
formula_examples = {
    "one_entity_false_claim_factor": 1 - 1 / (1 + min(19, 3)),
    "seven_entities_false_claim_factor": 1 - 1 / (1 + min(19, 21)),
    "anchored_classification_example": 0.5 + 0.5 * (0.80 - 0.60) / (1 - 0.60),
    "interval_inside": 12 - 8,
    "interval_missed_by_one": (12 - 8) + 20 * 1,
    "final_maximum": -0.27 + 1.27 + 0.25,
}
expected_formulas = [0.75, 0.95, 0.75, 4, 24, 1.25]
for (key, actual), expected in zip(formula_examples.items(), expected_formulas):
    if abs(actual - expected) > 1e-12:
        errors.append(f"公式例子错误：{key}")

report = {
    "date": "2026-10-07", "timezone": "Asia/Hong_Kong",
    "scope": "仅文档/来源/示例语法静态检查；非参赛程序或官方评测",
    "status": "passed" if not errors else "failed", "counts": counts,
    "time_conversions": converted, "formula_examples": formula_examples,
    "errors": errors,
    "not_executed": ["依赖安装", "Agent运行", "容器构建或运行", "House请求",
                     "NLI模型检查", "官方打包/上传", "准确率或Final得分验证"],
}
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
sys.exit(0 if not errors else 1)
