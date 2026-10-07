# 产物来源与使用范围

更新日期：2026-10-07。当前产物是私有本地历史参考集、实验 fixture 和验证工具；尚无用于正式比赛的候选镜像，没有官方成绩。

## 固定输入与研究产物

T4 输入来自 `Agenthon-2026/track4-analysis-public` 的固定 commit `1c744e1d6725340643a533f436517d72b53ca0e1`，11 个公开 unit / 78 个实体。answer schema 来自 `Agenthon-2026/Agenthon2026-public` 的 v2.5.1 commit `50fb2dc2b39c70f4cf81fcd269943782eddfaed0`。逐文件 hash、源许可、任务指纹与复制日期见 `datasets/agenthon-t4-reference/inputs/source-manifest.json`。

研究结果由 SEC/公司公开申报与公告、BLS/ALFRED/Census/BEA 历史发布、美国财政部和 CFTC 数据、公开金融行情数据重建。逐值公式、来源、定位、日期和限制保存在 `research/*.json` 及合并 `reference.jsonl`；抓取日期和证据 hash 保存在 `sources/` 对应元数据。只有实际保存及核查过的资料才计入数据覆盖，不把下载失败当成功。

## 公开练习题的样本内用途

本项目明确命名使用的十个 practice units：`t4-auction-btc-202411-us7`、`t4-cotpos-202411-us10`、`t4-cpicomp-202410-us11`、`t4-credit-event-2023`、`t4-eps-growth-2024Q3-banks`、`t4-eps-yoy-2023Q2-mixed`、`t4-fomc-curve-20220728`、`t4-fomc-curve-20240918`、`t4-macrorev-20240930-us6`、`t4-postearn-20240201-megacap`。另外使用 `t4-EXAMPLE-eps-beat` 做本地格式实验。

这些历史结果在各自 task cutoff 之后公开；基于它们的本地比较和固定回放属于样本内实验，不表示历史时点可作出的预测。主办方 [#24 的澄清](https://github.com/Agenthon-2026/track4-analysis-public/issues/24#issuecomment-6029140058) 允许 practice 首次发布结果用于 constants/design choices，并要求记录 source/retrieval date 和此 in-sample exception。该许可尚不能推导为 task→答案固定回放的提交许可；已通过 [#26](https://github.com/Agenthon-2026/track4-analysis-public/issues/26) 单独问询。

当前尚未将这些参考结果用于任何 Final 参数拟合、选择或校准。宏观资料明确使用指定历史 vintage；财报采用首次季度发布/申报口径。COT 年度文件与 API、财政部年度 yield、历史行情回溯的首次发布修订链可能未知，需依记录逐项核实，不能把公开历史系列自动当作首次版本。如果后续准备正式候选，将补充实际用到的 artifacts、首次值证明、拟合/选择数据窗口和方法。

参考版0.1.1另外实际保存收益率24端点的相邻ALFRED历史vintage、80份信用相关SEC正文及8份submissions、AMGN预告/实际公告和行情补证。ALFRED可见日期不等于Treasury全球首发时点；第三方IR行情上游独立性和完整公司行动链仍未知。四个信用正例直接核查原8-K，四个no_event仍暂定。补证hash核对保存字节，脱敏HTML的下载原始hash仅为未保留字节的摘要，中文网页备注单独标记。来源与边界见development-docs/agenthon-t4/16-证据补强与版本核查.md；没有据此宣称全部满足正式拟合首发要求。

## 当前模型与提交状态

构建参考集和本地验证工具未调用 House 或其他生成模型 API；没有保存个人模型凭证，没有构建/推送比赛镜像或上传 submission ZIP。模型、镜像 digest、运行资源、submission ID 及官方评分在实际发生后分别登记。开发工具的存在不表示其固定回放行为获准正式提交。
