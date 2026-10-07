# 第三方源码说明

`baseline_agent/` 的六个 Python 文件来自 [官方 Track 4 仓库](https://github.com/Agenthon-2026/track4-analysis-public/tree/1c744e1d6725340643a533f436517d72b53ca0e1/baselines/baseline_agent)，保留原字节，使用 MIT 许可；完整版权和免责条款见 [LICENSE.upstream](LICENSE.upstream)。各文件 SHA-256、长度和固定 commit 记录在 [upstream-manifest.json](upstream-manifest.json)。

`contracts/task_table.py` 的 task 行 JSON 渲染方式改编自该 commit 的 `qfbench2_track_analysis/corpus.py:task_table_text`，保留 `ensure_ascii=False`、`, ` / `: ` 分隔符、原始行顺序、换行连接和全局字符偏移规则。输入拒绝和错误报告由 `candidate.py` 负责。

`analyze.py`、`candidate.py`、容器配置和候选测试是本项目新增文件。未复制 toolkit 评分实现或神经模型。本候选由本项目准备，官方上游源码的复用不代表主办方已经批准候选或确认比赛成绩。
