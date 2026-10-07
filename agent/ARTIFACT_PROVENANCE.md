# Development候选产物来源

更新日期：2026-10-08。本文件说明当前stdlib候选的实际来源，供正式提交前核对。没有真实团队证明、已发布镜像digest或平台提交记录；本文件不是封签descriptor。

## 代码与基础环境

官方baseline来自 `Agenthon-2026/track4-analysis-public` 的固定commit `1c744e1d6725340643a533f436517d72b53ca0e1`，六个复制模块的路径、字节SHA256和MIT许可见 [upstream-manifest.json](upstream-manifest.json)、[LICENSE.upstream](LICENSE.upstream) 及 [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md)。输入防线、CLI、任务表适配和概率约束由本项目新增。

基础环境为官方Python 3.13 slim，Dockerfile固定多架构manifest digest `sha256:bf44cdfcb76cd3b41e879bc058fc37ec5872002ccfde7fcb765e218cde0cd79c`，实际选择linux/amd64。这是基础镜像来源，不是参赛产物的registry digest。构建上下文为agent/；只复制Dockerfile明列代码与许可，不安装包、下载模型或训练。

## 实际学习产物与数据

当前没有额外语言模型、embedding/reranker、神经预测器、学习参数、adapter、训练集或拟合/选择/校准产物；没有House请求。当前采用官方词项检索和规则预测，固定区间未校准。概率任务由当次target单位或明确point_forecast题面识别，使用中性0.5与[0,1]区间，二分类平局按当次词表顺序处理；没有按历史标签调参。

运行只读取本次官方task和manifest白名单corpus，逐文件检查SHA、截止日期、实体归属与路径。未注明日期、cutoff后或错实体来源不进入reader；无合格来源时只引用自己的task行。候选中没有本项目reference、私有原件、冻结练习输入、外部推理资料或网络客户端。

公开历史参考集仅供宿主实验、输出后比较和审校，不进入镜像/运行挂载。当前候选未使用practice in-sample exception来拟合常数或读取历史结果；以后若实际采用，须按官方#24逐值登记来源、抓取时间、选择用途与许可，不能沿用本文件的“无产物”声明。

## 验证及正式提交前的证据

实际运行记录、镜像config ID、11题输出hash、候选源码提交、官方公开检查范围和未执行项见 [18号报告](../development-docs/agenthon-t4/18-官方答复闭环与评测候选.md)。本地image config ID不能作为已发布registry manifest digest使用。新增任何实际模型或校准产物后，需同步其精确revision/checksum、数据首次可得日期、许可和descriptor字段。

正式提交还须取得真实Team/指定账号准入，核对适用路线与剩余额度，实际发布或获准交付镜像，生成与其digest绑定的descriptor/team proof。Team Key不写入本文件、镜像、ZIP、日志或公开仓库。有效官方score/submission_id在实际平台返回前保持null。
