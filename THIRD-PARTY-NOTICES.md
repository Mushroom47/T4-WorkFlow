# 公开发布的来源与许可

顶层 MIT 仅适用于本项目原创代码与原创说明，不为第三方材料重新授予权利。公开历史参考值是独立重建的事实与计算，不是主办方 outcome，不能据此声称获知私有评测答案。

官方来源：Agenthon-2026/track4-analysis-public，固定 commit `1c744e1d6725340643a533f436517d72b53ca0e1`；共享 answer schema 来自 Agenthon2026-public v2.5.1。复制的输入保留目录内 LICENSE、DATA-LICENSE 与 THIRD-PARTY-NOTICES，逐文件 manifest 许可优先。task/card 有 CC-BY-4.0，corpus 包括公共领域政府数据及有单独声明的 SEC 公开备案整理；不要把整个目录概括为 MIT。文件原始字节与 attribution/locator 保持不变。

CFTC、Treasury、BLS、BEA 和美联储等政府统计来源见各 sources 下载记录。本项目仅保留原有政府来源与自行抽取/计算的事实；引用 FRED/ALFRED 时保留底层系列来源，第三方系列并不因在 FRED 出现就变成公共领域。本集所用政府系列按其实际来源记录。

Yahoo、Nasdaq、企业 IR/Q4、SSGA、S&P 和补抓的发行人 SEC 申报全文等未确认再分发许可的原始材料不进入公开 Git 历史。公开版保存 URL、hash、字节数、必要事实定位与原创中文说明，清单见 `datasets/agenthon-t4-reference/public-source-catalog.json`。原件可由使用者依据提供方条款合法取得，再用于本地审计；自动取数只适用于清单中允许的原件，受限网站与包装副本不自动下载。Amgen 网站的使用限制单独记录，不将其全文再分发。

官网规则允许公开参与者自己的作品，同时要求遵守各资源实际许可与第三方权利：[Licensing Policy](https://www.agenthon.net/licensing/)。比赛正式程序的截止日、训练和推理政策仍独立适用，本地研究参考库不等于合法的参赛查表程序。

`qa/reordered-task.json` 是用于字段顺序验证的官方 task 修改副本，继承原 task 的 CC-BY-4.0 归属与 attribution；顶层 MIT 不覆盖该文件。
