"""Compile and run a scoped composition probe, with contract rejection cases."""
from pathlib import Path
import json
import re
import shutil
import subprocess

work = Path(__file__).resolve().parents[1] / ".validation" / "composition"
work.mkdir(parents=True, exist_ok=True)
compiler = shutil.which("clang++")
assert compiler
source = Path(__file__).parent / "composition.cpp"
records = []

for standard, negative in [("c++20", None), ("c++23", None)] + [
    ("c++20", name) for name in ("DUPLICATE", "UNSUPPORTED", "WRONG_OWNER", "UNREGISTERED")
]:
    name = f"composition-{standard}-{negative or 'positive'}"
    command = [compiler, f"-std={standard}", "-Wall", "-Wextra", "-Wpedantic", "-Werror", str(source)]
    exe = work / f"{name}.exe"
    if negative:
        command += [f"-DREJECT_{negative}", "-fsyntax-only"]
    else:
        command += ["-o", str(exe)]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=45)
    diagnostics = result.stdout + result.stderr
    (work / f"{name}.log").write_text(diagnostics, encoding="utf-8")
    runtime_exits = []
    if negative:
        passed = result.returncode != 0 and re.search(r"does not satisfy 'Projectable'|constraints not satisfied", diagnostics) is not None
        passed = passed and not re.search(r"file not found|unable to execute command", diagnostics)
    else:
        passed = result.returncode == 0
        if passed:
            # Different runtime argc values demonstrate data is not a template input.
            for args in ([], ["a", "b"]):
                run = subprocess.run([str(exe), *args], capture_output=True, timeout=10)
                runtime_exits.append(run.returncode)
            passed = all(code == 0 for code in runtime_exits)
    records.append({"name": name, "command": command, "compile_exit": result.returncode,
                    "runtime_exits": runtime_exits, "passed": bool(passed), "diagnostics": diagnostics})
    print(f"{'PASS' if passed else 'FAIL'} {name}")

report = {"checks": records, "passed": sum(row["passed"] for row in records), "total": len(records),
          "scope": "Metadata, concepts, constraint short circuit, member access, pack expansion, static config checks and owned runtime output; not a full serializer or independent agent evaluation."}
(work / "composition-results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
assert all(row["passed"] for row in records), "Inspect composition logs for failure causes"
