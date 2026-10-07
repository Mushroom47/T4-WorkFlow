# T4-WorkFlow 开发文档索引

建立日期：2026-10-07。当前目标是参加 Agenthon 2026 第四赛道，并把官方规则、接口和评测要求转换为后续开发可直接使用的基线。

## 当前目录与职责

初始化前通过文件系统级检查确认：本工作区为空，没有 `development-docs/`、`architecture-overview/`、`使用手册/` 或 `deployment-configs/`，也没有 Git 元数据。本轮只创建 `development-docs/`；其余目录尚无维护需求。

- `development-docs/`：保存任务目标、规则事实源、Phase、验证证据、决策和 Linear 映射。
- `architecture-overview/`：以后在实际代码架构确定时保存长期架构事实；本轮没有建立。
- `使用手册/`：以后保存经过执行验证的操作手册；本轮命令参考留在任务文档，并标明尚未执行。
- `deployment-configs/`：用于真实环境配置归档；本轮没有部署或配置快照。

## 当前任务

| 任务 | 本地入口 | Linear | 状态 |
| --- | --- | --- | --- |
| Agenthon 2026 T4 参赛准备 | [任务入口](agenthon-t4/00-README.md) | Project P-CHE-132（内部协作记录） | Phase 1/2已完成；Phase 3本轮本地验收；Phase 4/5仍缺官方有效成绩 |

新任务使用清晰稳定的英文目录名。规则知识与实际代码验收分开；旧记录需要重新核对，不能自动成为新方案的设计限制。

后续工作先读 [开发与 Linear 同步约定](01-二次开发工作流与Linear同步.md)，再进入任务入口、Phase、进度和问题记录。
