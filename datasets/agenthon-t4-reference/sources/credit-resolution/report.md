四个历史发行人（BBY、M、ODFL、WBA）在本次明示的有限公开核查范围内均可接受 `no_event`，推荐顶层 `status=verified`，同时必须保留 `quality.fact_status=bounded_verified`。这表示公开资料核查已达到本目录的有限验收标准；官方私有 outcome 的一致性仍为 `unknown`。信用记录的 `reference_value` 全部为 `null`，不能把历史事件指示标签写成实际概率 0。

可合并接口为 [resolution-checks.json](resolution-checks.json)、[evidence-manifest.json](evidence-manifest.json)、[publication-boundary.json](publication-boundary.json)。前者逐 issuer 提供 `acceptance_scope`、事实、候选处置和残余边界；清单提供实际存留原响应的 URL、路径、发布时间依据、获取时间、SHA256 和字节数。检查均在本地原件实际回读后生成。此轮只写本独占目录，没有修改研究标准集、fixture、QA、共享工具、Git 或 Linear。

**有限验收与覆盖边界**

观察窗为 2023-04-01 至 2024-03-31，起止均含。主体固定为题面历史母公司 CIK；母公司担保债务的发行/借款子公司纳入信用传导核查。其他非担保子公司、已出售企业、同名品牌公司不自动成为母公司事件。题面未明示全集团子公司归属，因此 `broader_all_subsidiary_scope_verified=false`。

三类目标分别检查：实际 Chapter 7/11 申请、付款违约、评级机构认定 distressed exchange。合同的本金到期日、利息/费用宽限期、交叉违约金额门槛、确认/披露日期分别记录。合同存在某项触发条件不代表事件已发生；正常现金清偿、普通评级降级和窗口外交易经原文处置。

验收依据是完整窗口 SEC 申报名册及主文件、窗口后首个季度的尾部资料、存续债务与实际偿付、债务合同/担保资料，以及 S&P 公开年度违约名单的交叉核查。未解决的具体反向事件候选将导致暂定；公开全国法院付费索引和所有评级机构私人台账的穷尽查询不属于这份有限公开标准。公开 SEC 披露偏向重大事项，不能保证从未发生任何未披露的短时支付迟延；这项资料覆盖限制不能被偷换成题面 payment default 的金额定义。

| Issuer | 题面母公司 CIK | 全窗主文件 | 尾部季度主文件 | 已核对的具体债务证据 | 推荐状态 |
|---|---|---:|---:|---|---|
| BBY | 0000764478 | 15 | 1 | 两组票据本金 500/650 百万美元原条件存续；新循环授信与期末无借款；实际付息 | verified / bounded_verified |
| M | 0000794367 | 14 | 1 | 母公司担保 MRH 债务；票据名义本金 3,007 百万美元前后相同；除 ABL 外无年度重大融资 | verified / bounded_verified |
| ODFL | 0000878927 | 21 | 1 | 2023-05-04 首期本金 2,000 万美元实际支付；剩余 8,000 万；2024-03-31 全债务契约合规 | verified / bounded_verified |
| WBA | 0001618921 | 20 | 1 | 2023-11-17 到期 8.5 亿美元票据全额清偿；两旧循环授信全部义务清偿；尾部实付利息和存续债务 | verified / bounded_verified |

全窗分母为 70 份主文件，尾部 4 份，共 74 份既有正文；另引用既有 4 份 SEC submissions 原响应。因此清单中的既有 archive 引用为 78 个源。本轮新增下载成功 31 个原响应，6 项访问失败。31 项独立检查全部通过，其中包含文件完整性、申报名册、法律主体映射、具体正文定位和评级名单范围检查。这些数量是资料/检查的分母，不能称作 78 条数值 outcome 的复算。

**BBY 的具体处置**

[2024-03-15 年度原申报](https://www.sec.gov/Archives/edgar/data/764478/000076447824000010/bby-20240203x10k.htm) Note 8 列示 2028 年与 2030 年票据；财年现金流附表列实际付息 5,100 万美元。Debt and Capital 披露 2024-03-13 的 S&P BBB+/Moody's A3、均 Stable。此实付金额是完整财年数，不能冒充精确观察窗合计。

[2024-06-07 尾部季度原申报](https://www.sec.gov/Archives/edgar/data/764478/000076447824000022/bby-20240504x10q.htm) Note 6 显示两组票据本金仍分别 5 亿/6.5 亿美元，到期 2028/2030、票息 4.45%/1.95%，循环授信期末无借款。2023-04-12 更换五年循环授信属于普通融资，已与原[Exhibit 10.1](https://www.sec.gov/Archives/edgar/data/764478/000076447823000012/bby-20230412xex10_1.htm)结合核对。该借款协议的利息/费用宽限为 3 个工作日，票据[基础契约](https://www.sec.gov/Archives/edgar/data/764478/000104746911001822/a2202436zex-4_1.htm) Section 501 的利息宽限为 30 日；它们是判断条件，没有被误判为发生事实。

关键离线检查编号：`bby-notes`、`bby-paid-interest`、`bby-borrowing`、`bby-contract`、`bby-note-grace`。每项提供原件路径、hash、可见正文正则与偏移。

**M 的 CIK、债务主体与时间处置**

[SEC 债务子公司注册原响应](https://data.sec.gov/submissions/CIK0001026179.json)将 MRH 映射至 0001026179；题面与母公司原响应均为 Macy's, Inc. / 0000794367。两个 CIK 是同时存在的母子公司，不是 ticker 母公司按时间更替。原响应记录 MRH 旧名 Inc，现为 LLC；[2022 联合注册](https://www.sec.gov/Archives/edgar/data/1026179/000110465922065287/tm2216233-1_s3asr.htm)核对两法律名称（准确 URL/hash 以清单中的 `M-2022-joint-issuer-registration` 为准）。

[2024-03-22 年度原申报](https://www.sec.gov/Archives/edgar/data/794367/000162828024012734/m-20240203.htm) Note 6 确认母公司完整无条件担保 MRH 的债务，票据本金合计 30.07 亿美元、到期 2025–2043；年度付息为 1.57 亿美元。2023 年度除 ABL 借还之外没有其他重大债务融资。2022 年 tender/新票据融资在观察窗外；财报中既有 exchanged debentures 的名称不能解释为 2023 新发生交换。

[2024-05-30 尾部季度原申报](https://www.sec.gov/Archives/edgar/data/794367/000162828024025853/m-20240504.htm) Note 4 表明这 13 周内除资本租赁外没有借款/偿债，Note 6 的名义本金在 May 4、February 3 与前年 April 29 均为 30.07 亿美元。2020 年 Inc→LLC/州别法律转换和 2023-03-22 的银行授信修订均在窗口前。S&P 2024 研究第 34 页的 Macy's 历史违约例子属于 1981–2024 的历史统计，不能替代当年度 Table 8。

关键离线检查编号：`m-parent-subsidiary-cik`、`m-issuer-guarantee`、`m-transactions`、`m-tail-transactions`、`m-tail-notional`、`m-conversion`。ABL 合同的付款宽限查核用 `m-abl-grace`：本金到期即构成合同违约，利息/费用为 3 个工作日。全文合同仅本地保存，不发布完整附属公司名单。

**ODFL 的本金偿付与窗口终点**

[2024-02-26 年度原申报](https://www.sec.gov/Archives/edgar/data/878927/000095017024020176/odfl-20231231.htm) Note 2 的私人票据约定 3.1% 票息及 2027 年最终到期，明确 2023-05-04 首期 2,000 万美元本金已经支付，余款 8,000 万美元按后续四期支付。2023 年实际利息付出为 348.4 万美元，原报表单位为千美元。

[2024-05-07、报告期 2024-03-31 的原 10-Q](https://www.sec.gov/Archives/edgar/data/878927/000095017024054284/odfl-20240331.htm)直接覆盖窗口终点，General Debt Provisions 披露该季度全部债务契约合规。Note/Credit Agreement 的 2023-03-22 修订在观察窗外；[票据协议修订原附件](https://www.sec.gov/Archives/edgar/data/878927/000095017023009357/odfl-ex4_17.htm)7A 的利息触发条件为超过到期 5 日、本金到期不付则触发。

财报提及的破产风险谈的是客户，不是 ODFL 自身申请 Chapter 7/11。S&P 未匹配到 ODFL 只能作为额外一致性检查；不能因私人票据发行人未出现在公开评级名单，就声称评级台账穷尽了该公司。

关键离线检查编号：`odfl-principal-payment`、`odfl-covenant-end`、`odfl-paid-interest`、`odfl-note-grace`。

**WBA 的到期票据与降级**

[2024-03-28、报告期 2024-02-29 的原 10-Q](https://www.sec.gov/Archives/edgar/data/1618921/000161892124000035/wba-20240229.htm) Note 7 确认 2023-11-17 已全额偿还 8.5 亿美元的 2023 到期票据；上半年实际付息约 3.01 亿美元。[2023 年度原申报](https://www.sec.gov/Archives/edgar/data/1618921/000161892123000062/wba-20230831.htm)同时处置了 2023-08-09 终止的两组旧循环授信：全部义务已清偿；2021 分期贷款的前两组在财年内全额清偿。

窗口内 S&P/ Moody's 的评级降低属于普通降级。2024-03-27 评级表仍为 BBB-/Ba2，公开年度违约名单未匹配其法律名称。[2024-06-27 尾部 10-Q](https://www.sec.gov/Archives/edgar/data/1618921/000161892124000065/wba-20240531.htm)继续提供付息、存续借款与契约资料。母公司担保的 Walgreen Co. 既有债务纳入传导范围；所有其他集团实体没有自动被合并。

[2023 Exhibit 10.1](https://www.sec.gov/Archives/edgar/data/1618921/000119312523207773/d542330dex101.htm)及[Exhibit 10.2](https://www.sec.gov/Archives/edgar/data/1618921/000119312523207773/d542330dex102.htm)Section 7.02 区分本金到期不付和利息/费用 5 个工作日宽限；Section 7.04 对 Major Subsidiary 的交叉违约还有金额及宽限门槛。合同条款不是信用事件，也不把其门槛强加给题面。关键检查：`wba-note-paid`、`wba-obligations-satisfied`、`wba-paid-interest`、`wba-ratings`、`wba-contract1-grace`、`wba-contract2-grace`。

**评级与法院资料的有限范围**

S&P 原作者的 [2023 年度研究（Maalot 官方关联站）](https://www.maalot.co.il/Publications/TS20240709142640.PDF)封面日期 2024-03-28，Table 8 为第 24–31 页；[2024 年度研究](https://www.maalot.co.il/Publications/FTS20250331162126.pdf)封面日期 2025-03-27，Table 8 为第 24–30 页。所有完整相关页已离线提取并核对首张表的渲染，正文标题明确覆盖公开评级发行人。对四公司及融资主体的名字进行空白归一化匹配均为 0；用各表中可匹配的非目标发行人作正向控制，避免扫描失效造成假负向。2024 全年表只用于排查 2024Q1，目标公司全年均未匹配，所以无须将窗口外事件算入结果。这两份研究是事后公开核查资料，不能进入参赛预测的 cutoff 前证据。

普通 requests 首次获取 S&P 两年研究失败，采用匿名公开浏览器请求头后成功下载；实际获取时间与字节 hash 均保存，没有伪造首发内容。S&P 2023Q2 component scores 虽 web 可见，但本地下载仍 403，清单将其记为失败，不计入独立回读证据。

四个 RECAP 精确窗口查询均返回 403；不是零结果，法院匹配数量为未知。查询 URL 与失败时间保留，沒有调用收费 fetch API。[PACER 官方说明](https://pacer.uscourts.gov/help/faqs/what-pacer-case-locator)介绍全国联邦案件索引；[US Courts](https://www.uscourts.gov/court-records/find-a-case-pacer)明确访问需账号。RECAP 是贡献汇集的公开档案，不能冒充完整全国案卷。没有取得法院全国排除证明，也没有取得 Moody's/Fitch 全窗所有事件私人台账。

真正残余问题为：官方是否把所有集团子公司的事件合并；宽限内迟付、合同 default 与评级事件的时间认定是否采用同一口径；是否需要未公开重大性以下付款事项。这些问题保存在每行 `acceptance_scope.limitations` 与全局 `limitations`，不是默默删除。没有发现需纠正标签的实际反向事件。若后续发现属于本窗口和本 issuer 的原始事件材料，应立即降回暂定并修正标签；若官方明确使用更广全集团口径，必须按该范围重新验收。

**公开发布边界**

`local-raw/**` 与 `local-derived/**` 为仅本地审校内容。两个 S&P 全文 PDF、完整 Table 8 的提取文本和截图、issuer 财报/债务合同全文均无此项目的公开全文转载授权。本次没有复制全量名单进入建议公共文件。root 将统一移动缓存到仓库外 `.local/private-evidence` 并调整来源路径后再公开。公开层保留 URL、hash、字节数、范围、四主体相关事实、自写中文方法及必要短定位；`publication-boundary.json` 是机器可读的隔离清单。
