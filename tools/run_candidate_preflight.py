#!/usr/bin/env python3
"""在真实断网只读容器中运行公开练习；参考比较只在宿主执行。"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.reference_suite import ReferenceSuite


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--dataset", type=Path, default=ROOT / "datasets/agenthon-t4-reference")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    dataset, output = args.dataset.resolve(), args.output.resolve()
    if output == dataset or dataset in output.parents or output in dataset.parents:
        parser.error("输出目录必须在数据集树之外")
    if args.image.startswith("-"):
        parser.error("image必须是镜像引用")
    output.mkdir(parents=True, exist_ok=True)
    suite = ReferenceSuite(dataset)
    suite.audit()
    image = json.loads(subprocess.check_output(["docker", "image", "inspect", args.image], text=True))[0]
    config = image["Config"]
    if image["Os"] != "linux" or image["Architecture"] != "amd64":
        raise RuntimeError("镜像必须为linux/amd64")
    if config.get("Volumes") or config.get("Labels", {}).get("qfbench2.interface_version") != "2.0":
        raise RuntimeError("镜像含VOLUME或缺interface_version=2.0")
    # Use the documented sandbox UID, rather than the runner UID whose host
    # threads are also charged against RLIMIT_NPROC by the kernel.
    runtime_user = "65534:65534"
    runtime = ["docker", "run", "--rm", "--platform", "linux/amd64", "--user", runtime_user, "--network", "none",
               "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
               "--pids-limit", "256", "--ulimit", "nproc=256:256", "--ulimit", "nofile=1024:1024",
               "--memory", "1g", "--memory-swap", "1g", "--cpus", "2",
               "--tmpfs", "/tmp:rw,nosuid,nodev,noexec,size=64m"]
    probe = "import pathlib,json;print(json.dumps([str(p.relative_to('/app')) for p in pathlib.Path('/app').rglob('*') if p.is_file()]))"
    paths = json.loads(subprocess.check_output(runtime + ["--entrypoint", "python", args.image, "-c", probe], text=True))
    forbidden = {"reference.jsonl", "reference.csv", "outcome.json", "naive_answer.json", "task.json", "answer.json"}
    if any(Path(p).name in forbidden or any(x in Path(p).parts for x in ("datasets", ".local", "private-evidence", "__pycache__")) for p in paths):
        raise RuntimeError("镜像包含参考答案、冻结输入或私有材料")
    results = []
    for task_id, entry in suite.units.items():
        unit = (dataset / "inputs" / entry["task_path"]).parent.resolve()
        answer_dir = output / "answers" / task_id
        answer_dir.mkdir(parents=True, exist_ok=True)
        # This fresh directory contains no inputs or secrets; it is the only
        # writable host mount, so the sandbox UID must be able to create output.
        answer_dir.chmod(0o777)
        answer_path = answer_dir / "answer.json"
        if answer_path.exists():
            raise RuntimeError(f"输出已有答案，拒绝把旧文件当本次结果：{task_id}")
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in unit.rglob("*") if p.is_file()}
        started = time.perf_counter()
        command = runtime + ["--mount", f"type=bind,src={unit},dst=/input,readonly",
                             "--mount", f"type=bind,src={answer_dir},dst=/output", args.image,
                             "analyze", "--task", "/input/task.json", "--corpus", "/input/corpus",
                             "--out", "/output/answer.json"]
        run = subprocess.run(command, capture_output=True, text=True, timeout=600)
        if run.returncode:
            raise RuntimeError(f"容器运行失败：{task_id} exit={run.returncode} {run.stderr[-1200:]}")
        after = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in unit.rglob("*") if p.is_file()}
        if before != after:
            raise RuntimeError(f"输入字节变化：{task_id}")
        answer = json.loads(answer_path.read_text())
        validation, comparison = suite.validate(answer), suite.compare(answer)
        results.append({"task_id": task_id, "exit_code": run.returncode,
                        "wall_seconds": time.perf_counter() - started,
                        "answer_sha256": hashlib.sha256(answer_path.read_bytes()).hexdigest(),
                        "input_bytes_unchanged": True, "validation": validation,
                        "local_reference_comparison": comparison})
    report = {"checked_at": datetime.now(timezone.utc).isoformat(), "image_id": image["Id"],
              "image_id_kind": "本地image config digest，不能冒充registry manifest digest",
              "platform": "linux/amd64", "network": "none", "rootfs": "read-only",
              "runtime_user": runtime_user,
              "runtime_flags": runtime[2:],
              "volumes": config.get("Volumes"), "interface_version": "2.0",
              "image_app_files": paths, "forbidden_reference_files": [],
              "task_count": len(results), "entity_count": sum(r["validation"]["entity_count"] for r in results),
              "default_reference_included_count": sum(r["local_reference_comparison"]["included_count"] for r in results),
              "reference_sha256": hashlib.sha256((dataset / "reference.jsonl").read_bytes()).hexdigest(),
              "passed": all(r["validation"]["ok"] for r in results), "results": results,
              "official_score": None, "submission_id": None,
              "notice": "真实容器的本地契约预检和参考比较；非官方数值评分、完整sandbox gate或生产NLI验收。"}
    (output / "container-preflight.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in {"results", "image_app_files"}}, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
