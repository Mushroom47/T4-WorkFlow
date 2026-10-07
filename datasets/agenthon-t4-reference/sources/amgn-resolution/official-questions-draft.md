# 官方问题草案（尚未发送）

以下仅询问公开任务合同和发布政策，不包含重建 EPS、方向标签、官方私有 outcome 或 naive。由根任务决定发帖位置并执行沟通。

## AMGN 日期口径

主办方您好。我们在只读核对公开 unit `t4-eps-yoy-2023Q2-mixed` 时发现 AMGN 的日期字段与公开披露日期不一致，想确认任务合同，不请求任何私有真值或标签。

当前公开 `task.json` 的 `resolution_date` 为 `2023-08-02`，AMGN 的 `expected_report_date` 为 `2023-08-01`；但发行人 2023 年 7 月 31 日的预告安排在 8 月 3 日收市后发布季度结果，实际公告日期是 8 月 3 日，相应 SEC 10-Q 于 8 月 4 日申报。完整 prompt 与 `label_assertions` 要求 June-2023 单季度 GAAP diluted EPS，相对于 cutoff 之后披露，并没有明写结果须在 resolution 当日之前公开。

请问该 unit 的 `resolution_date` 是结果首次公开的硬截止，还是行政/预期日期，目标仍取 prompt 指定季度随后实际首次披露的单季度 GAAP diluted EPS？如属于公开 metadata 错误，是否会更新该日期；若日期是硬截止，公开规则对这种晚于 resolution 才披露的实体应如何处理？只需说明规则或修订公开输入，无需提供任何数值、方向、内部评分结果或私有 outcome。

我们已阅读 [#23 关于 prompt/target/entity 定义数值语义的答复](https://github.com/Agenthon-2026/track4-analysis-public/issues/23#issuecomment-5985154828) 与 [#25 关于本题 interval 数值目标为 diluted EPS 的答复](https://github.com/Agenthon-2026/track4-analysis-public/issues/25#issuecomment-6029255707)。这次仅核对公开任务的日期语义，不把公告日期问题推定为私有 outcome 错误。

## 独立参考研究的公开发布范围

另想补充确认一个与 [#26 的固定回放诊断问题](https://github.com/Agenthon-2026/track4-analysis-public/issues/26) 不同的发布政策问题。我们拟公开自写的复算代码、来源目录、方法和不确定性记录，并研究是否可附上仅由公开历史来源独立计算的、已公开 practice units 的事实参考数值。该资料会明确标注为参与者研究结果，不是组织者 outcome，不含私有/held-out 材料、naive、平台反推结果或官方内部日志；不会将参考文件作为参赛镜像的 task→答案查表或外部推理证据。许可不明的第三方全文和原始网页正文将排除，以依法取得的来源链接、哈希及本地取数复现步骤代替。

请问比赛规则是否有专门限制公开发布这类独立研究的历史事实参考值？如果有，请指出适用条款及允许公开的边界。我们理解 [#24](https://github.com/Agenthon-2026/track4-analysis-public/issues/24#issuecomment-6029140058) 明确允许首次发布的 practice 历史值用于 constants/design choices，且需来源、取回日期与 in-sample disclosure；该回复本身没有明确说明公开发布研究参考数据的范围。网站 Licensing Policy §8 允许参与者独立公开自身作品，§3 则要求按资源的实际 license 处理，因此这次只请求澄清比赛特有的发布限制，不请求第三方版权授权或私有答案。
