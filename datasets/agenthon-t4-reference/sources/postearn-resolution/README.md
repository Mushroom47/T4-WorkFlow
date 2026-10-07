# postearn 三条参考结果的有限窗口验收

本目录独立核查 `postearn_20240201_a`（`t4-postearn-20240201-megacap`）的 AAPL、AMZN、META 参考结果。结论是：**三条均达到本地公开历史事实复核标准，可由主代理将顶层 `status` 升为 `verified`；数值及标签保持不变。** 证据整理没有修改共享 `reference.jsonl`、研究文档、Git 或 Linear。后续按主代理明确分配，已将主审计工具的 postearn 分支接入本目录实际原件验收，并新增独立负例测试。

质量维度统一为：

```json
{
  "fact_status": "verified",
  "task_alignment": "aligned",
  "first_publication_status": "unconfirmed",
  "official_outcome_status": "unconfirmed"
}
```

`task_alignment` 指数据来源、证券、时间窗口、收益定义及标签阈值与公开题面一致。它不表示与主办方私有 outcome、anchor 或官方得分对齐。当前历史数值复核和当日首发版本的可追溯性分别记录；没有因为首发链未知而把已能复核的公开历史事实一并判为未核验。

## 1. 官方口径和日期

固定官方仓库为 [Agenthon-2026/track4-analysis-public](https://github.com/Agenthon-2026/track4-analysis-public/tree/1c744e1d6725340643a533f436517d72b53ca0e1)。本地 `card.toml` 的 `[provenance].data_source` 指定 `Yahoo Finance (daily closes for outcome resolution)`；`task.json` 定义公司从 **2024-02-01 收盘至 2024-02-02 收盘** 的 total return，减去 SPY 同窗口收益，单位为百分比。

这两个日期的价格是评价时用的历史结果。预测输入的 frozen corpus 截止于 2024-01-31；不得把本目录的窗口结果混入 frozen 预测证据。`card.toml` 的 2026 年练习题公开日期也不是 2024 年价格的首次发布时间。

Yahoo 四份已保存响应分别确认 `symbol=AAPL/AMZN/META/SPY`、`currency=USD`、三个 `EQUITY` 和一个 `ETF`，历史数据按 `America/New_York` 转换为两日日期，SPY 的 `fullExchangeName=NYSEArca`。历史 `timestamp` 是日线标签，不在这里解释为 16:00 收盘时钟。响应里的当前交易状态字段不能当成 2024 年交易状态。

## 2. Close 和 total return

[Yahoo 官方历史页面](https://finance.yahoo.com/quote/AMZN/history/?p=AMZN)说明 `Close` 已按拆股调整，`Adj Close` 还处理股息和资本利得分配。不能把 `close` 泛称为完全未调整的历史名义价格；本次使用的是官方指定来源的日线 `close` 字段。[字段核对记录](yahoo-field-semantics.json)是自主中文释义，不是原始网页 HTTP 字节。

本地检查采用以下有限范围：指定 Yahoo 请求覆盖目标两日，四个标的均无 `dividends`、`splits`、`capitalGains` 事件；再核对对应现金分配来源，并检查同源 `adjclose/close` 两日因子没有实质阶跃。它不是对所有交易所、所有年代公司行动的完整性证明。证据组合支持在本题窗口内使用 `close` 比值作为 total return 的本地历史估计；不需要额外加上窗口外的股息或重复计算已在 `close` 中处理的拆股。窗口后的共同调整比例会在两日比值中抵消。

| 标的 | 目标窗口的核查证据 | 有限结论 |
| --- | --- | --- |
| AAPL | 原始 Nasdaq 分红表两目标日匹配 0；对应股息除息日 2024-02-09、宣布日 2/1、登记日 2/12、支付日 2/15；Apple 发行人页列示最近拆股为 2020 年；Yahoo 窗口事件为空 | 2/1 宣布股息不构成 2/2 持有窗口的现金收益；来源未记录窗口分配或拆股 |
| META | 原始 Nasdaq 表两目标日匹配 0；首次对应股息除息日 2024-02-21、登记日 2/22、支付日 3/26；Yahoo 窗口事件为空 | 首次股息不在目标持有窗口；来源未记录窗口分配或拆股 |
| AMZN | [发行人 FAQ](https://ir.aboutamazon.com/faqs/default.aspx)当前索引正文声明普通股从未现金分红，列示最近拆股 effective 日期为 2022-06-03；[2023 Form 10-K](https://www.sec.gov/Archives/edgar/data/1018724/000101872424000008/amzn-20231231.htm) Note 1 记载 2022 年拆股及年报每股数的追溯调整；Yahoo 窗口事件为空 | 补齐发行人一手陈述，未记录目标窗口现金分红或拆股。FAQ 原始全文没有本地归档，保存的是索引正文的短事实记录 |
| SPY | 直接解析 [SSGA 原始 XLSX](https://www.ssga.com/library-content/products/fund-data/etfs/us/spdr-etf-historical-distributions.xlsx) 的 `dividend` 工作表，全部 136 条 SPY 记录、CUSIP `78462F103`；两目标日 EX-DATE 匹配 0；相邻分配除息为 2023-12-15 和 2024-03-15；Yahoo 窗口事件为空 | 表内无窗口分红或资本分配。2024-01-31 支付对应先前 12 月除息，也在持有窗口开始前，不能再加一次 |

AMZN 的当前 FAQ 和 SEC 文档分别提供发行人/发行人提交的一手内容；FAQ 的本次 `web.run open` 只有标题和导航，完整相关事实由主站搜索索引正文取得。此限制在 [amazon-primary-facts.json](amazon-primary-facts.json)中保留，不把中文记录称为原始 HTTP 归档。SEC 文件的拆股表述与 FAQ 的 effective 日期用途不同，不混同为首次拆股后市场交易日期。

SPY 市场日线 `close` 没有替换为 NAV、INAV 或基金报价中点；Apple 代理的 SPY 行情没有响应证券元数据，也只作为价格美分旁证。Q4 与 Yahoo 底层数据是否独立仍未知，不作为本地验收的强制条件。

## 3. 数值、精度和分类

| 标的 | 2024-02-01 close (USD) | 2024-02-02 close (USD) | 公司收益 (%) | 异常收益 (%) | 标签 |
| --- | ---: | ---: | ---: | ---: | --- |
| AAPL | 186.86 | 185.85 | -0.5405116129722787 | -1.5932507789575607 | `negative_reaction` |
| AMZN | 159.28 | 171.81 | 7.866649924660974 | 6.813910758675692 | `positive_reaction` |
| META | 394.78 | 474.99 | 20.31764527078373 | 19.264906104798445 | `positive_reaction` |
| SPY | 489.20 | 494.35 | 1.052739165985282 | 基准 | 不作为分类实体 |

采用以下公式，没有用 1/31 背景价格，也没有改成公司/SPY 价格比收益或回归模型：

```text
return_percent = 100 * (close_20240202 / close_20240201 - 1)
abnormal_return_percent = company_return_percent - SPY_return_percent
positive_reaction: abnormal_return_percent > 1
negative_reaction: abnormal_return_percent < -1
flat: -1 <= abnormal_return_percent <= 1
```

Yahoo 元数据的 `priceHint=2`、Q4 展示渠道两日价格和现有参考共同支持按美分规范化。脚本先通过 `Decimal` 转为两位小数，再用 `Fraction` 精确计算百分比，最终转浮点用于 JSON。三个结果分别为有理数 `-36410525/22852978`、`16591825/2434993`、`930140375/48281594`，其最终浮点值与共享参考一致。这里的十余位小数是计算精度，不能解释为市场价格具有相同测量精度。

另行保留原始浮点 `close` 直接计算结果，以及当前 `adjclose` 直接计算结果。两种口径与美分结果的最大差异均小于 `0.00002` 个百分点，分类保持一致；该容差仅用于本次精度一致性检查，不替代正式评分器的尺度。当前 `adjclose` 会反映后来历史调整，因此它不是独立第二来源，也不是 2024 年首发 total-return 版本。

## 4. 已执行的验证和复现

执行环境为本机 `python3`，只用 Python 标准库，要求 Python 3.11 或以上。未安装新依赖，未调用比赛 Agent、NLI、Judge、Docker 或平台提交。

```bash
# 回读本地已保存原件、直接解析工作簿并只读比较共享参考。
python3 datasets/agenthon-t4-reference/sources/postearn-resolution/verify.py \
  --source-root datasets/agenthon-t4-reference \
  --reference datasets/agenthon-t4-reference/reference.jsonl \
  --report datasets/agenthon-t4-reference/sources/postearn-resolution/verification-originals.json

# 在不附完整上游原件的公开资料包中，复算小型派生事实。
python3 datasets/agenthon-t4-reference/sources/postearn-resolution/verify.py \
  --report datasets/agenthon-t4-reference/sources/postearn-resolution/verification-derived.json
```

首条命令生成的 [verification-originals.json](verification-originals.json)：`passed=true`、`check_count=157`、`failed_count=0`，读到 18 个既有证据文件。第二条命令的 [verification-derived.json](verification-derived.json)：64 项检查通过。后者复现派生事实和公式，不宣称重新验证了未随公开包分发的原件。

`checks` 是结构化检查数组，每项有 `check`、`pass`、`actual`、`expected`。检查数量包含字段和文件完整性检查，不代表 157 个彼此独立的数据源。AMZN 当前发行人 FAQ 的语义由本次主代理/子代理读取审核，不把自动字段检查描述为网页真伪的证明。

主工具 `tools/audit_reference_data.py` 的 postearn 分支每次运行 `verify.py --source-root <effective_dataset> --full-report`，核对本轮实际原件检查，再直接用 Yahoo 原件复算，并验证参考行的 `quality` 和题面 1 个百分点阈值。它不接受旧 `verification-originals.json` 的 `passed=true` 作为当前原件证明。

```bash
python3 -m unittest discover -s tests -p test_postearn_resolution.py -v
```

新增 8 项测试全部通过，包括错误日期、错误价格、窗口内除息、错误分类阈值、正负 1% 边界、错误事实状态和伪造旧报告。负例使用生成的小型夹具；价格与除息负例同步刷新原件 hash，确认实际拒绝来自语义或计算。它们不联网，也不依赖公开仓库之外的私有原件。

## 5. 原件许可和公开范围

[publication-boundary.json](publication-boundary.json) 的 `public_source_policy` 对每个上游证据写明再分发判定。18 个本地证据中，官方 `card.toml`、`task.json` 按 card 的 CC-BY-4.0 声明记录，公开时保留来源和许可；另外 16 个 Yahoo 原件/包装文件、Nasdaq JSON、Apple/Q4 行情、Apple HTML 和 SSGA XLSX 没有确认开放再分发许可，默认 `publish_original=false`。

本目录没有新增完整上游网页、行情响应或 XLSX 的副本。公开候选仅包含自主编写的脚本、中文报告、有限事实/派生数值、来源 URL、hash、bytes、定位和质量说明。短事实记录的 hash 对应本地中文记录；外部文件的 hash 对应已保存的原件或此前明确标注的脱敏副本，两者不能互换。公开访问、SEC 托管或本仓库许可证都不会自动授予上游全文再分发权；本目录没有声称完成法律许可确认。

新验收范围足以替代旧补证报告中较高的升级门槛：全球首发价格修订链、任意第二行情源的底层独立性和主办方私有 outcome 均单独记录，不能用来否定已经完成的有限窗口事实核验。旧补证记录作为历史过程保留，本次结论与范围以本目录为准。
