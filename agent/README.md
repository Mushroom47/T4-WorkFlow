# Track 4 最小 Development 候选

该候选采用冻结官方 stdlib baseline 的词项重叠检索、EPS 规则预测和固定区间。运行只读取指定 `task.json` 与 `corpus/`，不读取本项目参考答案、历史 lookup、私有原件或赛后来源，也不使用网络、额外神经模型或训练数据。它用于核对常规 Development 路线的输入输出契约，是最低合规 baseline；回退预测和区间未校准，预测能力有限，不保证高分，当前没有官方成绩。

入口同时接受比赛传入的前导 `analyze` 和本地省略该词的调用方式：

```sh
python3 agent/analyze.py analyze \
  --task datasets/agenthon-t4-reference/inputs/units/t4-EXAMPLE-eps-beat/task.json \
  --corpus datasets/agenthon-t4-reference/inputs/units/t4-EXAMPLE-eps-beat/corpus \
  --out /tmp/t4-candidate/answer.json
python3 -m unittest discover -s tests -p 'test_agent*.py' -v
```

候选按 `corpus/manifest.json` 的 `entity_ids` / `shared` 及 SHA-256 限定引用，只把日期不晚于 cutoff 的文档送入检索和 reader。当前版本仅支持官方公开单位使用的 `corpus_ref: "corpus/"`。索引不存在、没有该实体的合格文档或无法检索时，使用该实体自己的 task 行片段作事实引用；这类 claim 陈述输入事实，并不证明回退预测正确。原文摘录至多 160 个字符，引用采用官方全局字符偏移。label 从任务词表取得，全部实体必须输出，预测和区间必须是有限数值，区间 level 为 0.9。输出路径必须在输入树之外。

以下构建命令以 `agent/` 为上下文，显式 COPY 只包含候选代码和许可证；Dockerfile 不含 `VOLUME`，不装 toolkit 或模型。Python 3.13 基础镜像固定为多架构 digest `sha256:bf44cdfcb76cd3b41e879bc058fc37ec5872002ccfde7fcb765e218cde0cd79c`，通过 `--platform linux/amd64` 选择目标平台：

```sh
docker build --platform linux/amd64 -f agent/Dockerfile \
  -t t4-stdlib-development:local agent
docker run --rm --platform linux/amd64 --network none \
  -v "$(pwd)/datasets/agenthon-t4-reference/inputs/units/t4-EXAMPLE-eps-beat:/input:ro" \
  -v /tmp/t4-candidate:/output \
  t4-stdlib-development:local analyze \
  --task /input/task.json --corpus /input/corpus --out /output/answer.json
```

实际Linux CI已完成全部11题/78实体的65534非root、断网、只读运行，并回读容器输出做官方公开schema/alignment/确定性引用检查；命令和限制见 [18号报告](../development-docs/agenthon-t4/18-官方答复闭环与评测候选.md)。可通过 `python3 tools/run_candidate_preflight.py --image t4-stdlib-development:local --output /tmp/t4-new-preflight` 复现，该全新输出目录只将每题目录开放给sandbox UID。概率题输出中性0.5/[0,1]，41项候选测试通过。来源和无学习产物声明见 [ARTIFACT_PROVENANCE.md](ARTIFACT_PROVENANCE.md)。

正式提交还需要实际团队账号、团队证明、已发布镜像digest与平台metadata，以及适用提交路线。schema、官方确定性引用规则、judge tokenizer token上限、NLI faithfulness和官方比赛评测是不同检查；本地结构检查不等于Production或官方outcome对齐。

源码来源与修改边界见 [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md)。
