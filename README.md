# T4-WorkFlow

Agenthon 2026 第四赛道 T4 Explainability 的规则资料与本地实验准备项目。

## 当前状态

- 已完成官方公开规则、输入输出契约、评分机制、运行环境、数据与模型政策的研究和中文文档整理。
- 已建立参赛要求检查清单和 Linear 阶段规划。
- 用户已确认整体方案并启用 goal 持续执行。公开11题/78实体输入已冻结；参考集0.2.0：77 verified/1 provisional；事实维度74 verified/4 bounded_verified，114项测试与11题本地结构链通过。
- 已向官方发出 [诊断评测问询 #26](https://github.com/Agenthon-2026/track4-analysis-public/issues/26)；真实官方分数尚未取得。

## 文档入口

| 入口 | 内容 |
| --- | --- |
| [暂定项收敛与公开发布](development-docs/agenthon-t4/17-暂定项收敛与公开发布.md) | 最新质量、字段、复现命令、许可隔离和未完成项 |
| [项目文档索引](development-docs/00-README.md) | 本地文档组织与任务入口 |
| [本地验收与评测待办](development-docs/agenthon-t4/15-本地验收与评测待办.md) | 首版数据、工具验证与官网评分待办 |
| [证据补强与版本核查](development-docs/agenthon-t4/16-证据补强与版本核查.md) | 0.1.1新增原件、历史vintage、审校修复与验证 |
| [历史参考集与验收方案](development-docs/agenthon-t4/13-历史参考集与验收方案.md) | 已确认范围、数据口径、产物及验收边界 |
| [官方诊断评测沟通](development-docs/agenthon-t4/14-官方诊断评测沟通.md) | 已发送问询、官方答复和待取得的真实成绩 |
| [第四赛道资料](development-docs/agenthon-t4/00-README.md) | 完整规则与技术文档索引 |
| [硬性要求检查清单](development-docs/agenthon-t4/08-硬性要求检查清单.md) | 40 项候选验收要求 |
| [开发进度记录](development-docs/agenthon-t4/09-开发进度记录.md) | 已完成事项、验证证据与后续阶段 |
| [官方来源与版本基线](development-docs/agenthon-t4/12-官方来源与版本基线.md) | 固定提交、官方链接与来源哈希 |

## 资料验证

```bash
python3 development-docs/agenthon-t4/evidence/check_documents.py
```

该命令验证文档格式、链接、示例语法、来源版本、时间换算和评分公式例子。来源哈希检查需要先取得文档中记录的官方固定研究检出；临时检出路径见 `evidence/source-manifest.json`。它不运行参赛 Agent，也不代表官方评测成绩。

## 官方与协作入口

- [比赛官网](https://www.agenthon.net/)
- [第四赛道官方公开仓库](https://github.com/Agenthon-2026/track4-analysis-public)
- Linear 项目：Agenthon 2026 T4 参赛准备（内部协作记录）

本仓库公开原创代码、可分享派生事实和许可明确的输入。223份许可未确认原件仅在本地证据缓存，详见顶层 THIRD-PARTY-NOTICES。维护记录默认使用中文。

## 使用参考数据

同事优先取 `datasets/agenthon-t4-reference/reference.jsonl`、`reference.csv`、该目录 README 与最新收敛报告；JSONL有完整quality、acceptance_scope及来源，CSV便于浏览。四条信用bounded_verified须随覆盖限制使用；AMGN季度事实已确认，但日期合同待官方#27，默认比较排除。

```bash
python3 -m unittest discover -s tests -q
python3 tools/reference_suite.py audit
python3 datasets/agenthon-t4-reference/sources/postearn-resolution/verify.py
```

全原件审计需使用者按提供方条款取得原件并通过 `public-source-catalog.json` 校验。本地缓存不随仓库分享；公开派生自检不称原件审计。官方实际评分仍未取得。
