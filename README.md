# T4-WorkFlow

Agenthon 2026 第四赛道 T4 Explainability 的规则资料与本地实验准备项目。

## 当前状态

- 已完成官方公开规则、输入输出契约、评分机制、运行环境、数据与模型政策的研究和中文文档整理。
- 已建立参赛要求检查清单和 Linear 阶段规划。
- 已公开发布到 [Mushroom47/T4-WorkFlow](https://github.com/Mushroom47/T4-WorkFlow)，旧历史保留私有备份；当前dataset清单510文件，223条local_only隔离路径不公开。0.2.0匿名发布验收记录保留为历史证据。
- 用户已确认整体方案并启用 goal 持续执行。公开11题/78实体输入已冻结；参考集0.2.1：78 verified/0 provisional；事实维度74 verified/4 bounded_verified。本机158项测试通过，公开环境157项可独立运行，1项原件集成测试需合法本地缓存。
- 常规候选完成真实linux/amd64容器构建及11题/78实体的非root、断网、只读输入运行，下载输出的官方公开确定性合同检查通过；[CI证据](https://github.com/Mushroom47/T4-WorkFlow/actions/runs/37664798590)。这些结果不等于官网分数。
- 已向官方发出 [诊断评测问询 #26](https://github.com/Agenthon-2026/track4-analysis-public/issues/26)；真实官方分数尚未取得。

## 文档入口

| 入口 | 内容 |
| --- | --- |
| [官方答复闭环与评测候选](development-docs/agenthon-t4/18-官方答复闭环与评测候选.md) | 最新0.2.1、78条默认纳入、合规候选与真实评测剩余依赖 |
| [暂定项收敛与公开发布](development-docs/agenthon-t4/17-暂定项收敛与公开发布.md) | 0.2.0历史公开快照、字段、许可隔离和验收 |
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

同事优先取 `datasets/agenthon-t4-reference/reference.jsonl`、`reference.csv`、该目录 README 与最新收敛报告；JSONL有完整quality、acceptance_scope及来源，CSV便于浏览。四条信用bounded_verified须随覆盖限制使用；AMGN季度事实与日期合同已确认，默认比较纳入；首次发布与私有outcome仍不自动确认。

```bash
python3 -m unittest discover -s tests -q
python3 tools/reference_suite.py audit
python3 datasets/agenthon-t4-reference/sources/postearn-resolution/verify.py
```

全原件审计需使用者按提供方条款取得原件并通过 `public-source-catalog.json` 校验。本地缓存不随仓库分享；公开派生自检不称原件审计。官方实际评分仍未取得。

常规Development候选已在 `agent/` 准备，运行时只读本次task/corpus，不携带参考结果。真实Linux容器预检由仓库CI执行，实际结果见18号报告；官网分数仍未取得。
