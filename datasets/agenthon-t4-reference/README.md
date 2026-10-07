# Agenthon T4 公开历史参考集

本目录保存十个公开 Development 练习题及一个 EXAMPLE 的 78 个实体参考结果。它是独立重建的本地研究资料，没有主办方私有 outcome 或 naive answers；官方评分尚未取得。

当前参考版本 **0.2.0**，77 verified / 1 provisional / 0 unresolved。四个信用负例为有明确范围的 bounded_verified；AMGN历史EPS事实已确认，task日期歧义单列并默认排除。完整变更与测试见[暂定项收敛与公开发布](../../development-docs/agenthon-t4/17-暂定项收敛与公开发布.md)。核心数值和标签未改变，首次发布和官方私有outcome不因本地验收而自动确认。

## 文件与使用顺序

| 路径 | 内容 |
| --- | --- |
| `inputs/source-manifest.json` | 固定官方版本、11题输入哈希、78实体顺序、逐文件 SHA-256 |
| `inputs/units/` | 原始 task、card、manifest、corpus；输入和结果分别存放 |
| `inputs/schemas/` | 固定 v2.5.1 官方 answer schema 与对应 LICENSE |
| `research/*.json`、`research/*.md` | 四组逐项研究记录、方法和限制 |
| `sources/` | 许可明确的原件、原创派生事实和精确取数元数据；local_only原件见public-source-catalog，不在公开库 |
| `reference.jsonl` | 合并的逐实体机器可读参考记录，已生成并登记输入指纹 |
| `reference.csv` | 便于阅读的核心字段导出；完整证据保留在 JSONL |
| `build-report.json` | 行数、质量状态和参考集 hash；官方成绩字段保持 null 直到实际取得 |
| `qa/` | 独立公式审计、可复现 notebook 和本地验证报告 |

先阅读 `research/` 的方法与限制，再使用参考值。`verified` 是公开资料复核状态，不能解释为已与主办方私有真值一致；`provisional` 默认排除；`unresolved` 不填猜测值。对于已知仍缺首次发布历史修订链的序列，单独备注，不用于正式拟合/校准。

## 输入冻结与构建

已冻结的文件可直接离线使用。需要重新构建时，先准备官方两个 Git 仓库，命令会直接读取固定 commit 的 blob，不使用检出目录里的未提交改动：

```bash
python3 tools/build_reference_data.py freeze \
  --source /tmp/agenthon-t4-research-20261007 \
  --toolkit-source /tmp/agenthon-toolkit-research-20261007
python3 tools/build_reference_data.py cot
python3 tools/build_reference_data.py combine
```

`cot` 使用已保存的 CFTC 原始资料，`combine` 要求四组研究文件和完整 78 键覆盖。工具只处理本地数据，不调用模型、不上传比赛答案。

## 质量与评分边界

GAAP/adjusted EPS、持续经营/总利润、reference month/vintage、总回报/价格回报和比例/百分点必须按 task 定义核对。CPI 比率保留已发表指数的计算精度，同时登记官方一位小数；它不表示获知 BLS 内部未舍入数值。信用事件的实际标签不等于真实预测概率，区间没有历史唯一标准。

本地 fixture 的点值来自参考集，测试区间与事实引用用于结构验证。fixture 自测为零误差属于预期的管线一致性检查，不能称为预测能力或官方分数。官方许可及评分记录见 [评测沟通](../../development-docs/agenthon-t4/14-官方诊断评测沟通.md)，完整计划见 [历史参考集验收](../../development-docs/agenthon-t4/13-历史参考集与验收方案.md)。

## 来源与许可

复制的官方输入保留 [LICENSE](inputs/LICENSE)、[DATA-LICENSE](inputs/DATA-LICENSE.md) 和 [THIRD-PARTY-NOTICES](inputs/THIRD-PARTY-NOTICES.md)。逐文件 manifest 许可优先，不能把这些原始来源概括为本项目重新授权。外部结果来源的权利归其提供方；223份许可未确认原件/完整提取仅本地保留。顶层MIT不覆盖第三方材料，详见顶层THIRD-PARTY-NOTICES。

当前合并状态为77 verified / 1 provisional / 0 unresolved；78键完整覆盖。四独立质量字段见JSONL的quality和CSV末四列。使用及测试命令见 [本地验收报告](../../development-docs/agenthon-t4/15-本地验收与评测待办.md)。

公开派生自检无需缓存；全原件审计命令为 `python3 tools/audit_reference_data.py --private-sources .local/private-evidence --self-check`。原件合法取得后放入cache/sources/...相对布局并核对catalog的hash。缺原件时工具明确失败，不把元数据当原件。research四组文件为0.1.1基线，resolution-overrides.json是0.2.0更新，reference.jsonl为当前权威合并入口。
