"""Validate installed documentation examples and focused C++ semantics."""
from pathlib import Path
import json
import re
import shutil
import subprocess
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".validation" / "examples"
WORK.mkdir(parents=True, exist_ok=True)
COMPILER = shutil.which("clang++")
assert COMPILER, "clang++ unavailable"
results = []


def check(name, source, standard, expect_error=None, run=False):
    path = WORK / f"{name}-{standard}.cpp"
    path.write_text(source, encoding="utf-8")
    command = [COMPILER, f"-std={standard}", "-Wall", "-Wextra", "-Wpedantic", "-Werror"]
    if run:
        exe = WORK / f"{name}-{standard}.exe"
        command += [str(path), "-o", str(exe)]
    else:
        command += ["-fsyntax-only", str(path)]
    proc = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=45)
    diagnostics = proc.stdout + proc.stderr
    (WORK / f"{name}-{standard}.log").write_text(diagnostics, encoding="utf-8")
    if expect_error:
        passed = proc.returncode != 0 and re.search(expect_error, diagnostics, re.I) is not None
        # A missing header or driver failure is never a successful compile-fail check.
        passed = passed and not re.search(r"file not found|unable to execute command", diagnostics, re.I)
    else:
        passed = proc.returncode == 0
    runtime_code = None
    if passed and run:
        runtime = subprocess.run([str(exe)], capture_output=True, text=True, timeout=10)
        runtime_code = runtime.returncode
        passed = runtime_code == 0
    results.append({"name": name, "standard": standard, "command": command,
                    "expected_error": expect_error, "compile_exit": proc.returncode,
                    "runtime_exit": runtime_code, "passed": passed,
                    "diagnostics": diagnostics})
    print(f"{'PASS' if passed else 'FAIL'} {name} ({standard})")


# Check the actual installed files, not a separately maintained copy of examples.
for path in [ROOT / "SKILL.md", *list((ROOT / "references").rglob("*")), *list((ROOT / "agents").rglob("*"))]:
    if not path.is_file():
        continue
    content = path.read_text(encoding="utf-8")
    assert "\ufffd" not in content, f"replacement character in {path}"
    assert "TODO" not in content, f"unfinished scaffold in {path}"
    if path.suffix == ".md":
        for target in re.findall(r"\]\(([^)]+)\)", content):
            if not target.startswith(("http://", "https://", "#")):
                assert (path.parent / target.split("#")[0]).is_file(), (path, target)

meta = yaml.safe_load((ROOT / "agents/openai.yaml").read_text(encoding="utf-8"))
assert meta["interface"]["display_name"] == "C++ 元编程"
assert 25 <= len(meta["interface"]["short_description"]) <= 64
assert "$cpp-metaprogramming" in meta["interface"]["default_prompt"]
assert meta.get("policy", {}).get("allow_implicit_invocation", True)
print("PASS UTF-8, local reference links, UI metadata, implicit invocation")

examples = {}
for name in ("type-computation", "concepts-and-diagnostics", "constant-evaluation-and-reflection"):
    content = (ROOT / "references" / f"{name}.md").read_text(encoding="utf-8")
    examples[name] = re.findall(r"```cpp\n(.*?)```", content, re.S)

for index, code in enumerate(examples["type-computation"]):
    for standard in ("c++17", "c++20", "c++23"):
        check(f"document-type-{index + 1}", code, standard)

check("document-constraints", examples["concepts-and-diagnostics"][0], "c++20")
check("document-constraints", examples["concepts-and-diagnostics"][0], "c++23")
for standard in ("c++17", "c++20", "c++23"):
    check("document-detection", examples["concepts-and-diagnostics"][1], standard)
for standard in ("c++20", "c++23"):
    check("document-consteval", examples["constant-evaluation-and-reflection"][0], standard)

check("eager-conditional-rejected", r'''
#include <type_traits>
template<class T> using element = std::conditional_t<std::is_class_v<T>, typename T::value_type, void>;
using result = element<int>;
''', "c++17", expect_error=r"cannot be used prior to '::'|has no members|not a class")

check("duplicated-constraints-ambiguous", r'''
#include <concepts>
template<class T> concept Readable = requires(const T& v) { v.read(); };
template<class T> concept Strong = requires(const T& v) { v.read(); } && requires(T& v) { v.reset(); };
template<Readable T> void pick(const T&);
template<Strong T> void pick(const T&);
struct Reader { void read() const; void reset(); };
void test() { pick(Reader{}); }
''', "c++20", expect_error=r"call to 'pick' is ambiguous")

constraint_example = examples["concepts-and-diagnostics"][0]
check("const-reader-rejected-at-constraint", constraint_example + r'''
void test() { select(MutableOnly{}); }
''', "c++20", expect_error=r"does not satisfy 'ConstReadable'|constraints not satisfied")

check("weak-constraint-body-failure", r'''
template<class T> concept Readable = requires(T& v) { v.read(); };
template<Readable T> int consume(const T& v) { return v.read(); }
struct MutableOnly { int read(); };
int test() { return consume(MutableOnly{}); }
''', "c++20", expect_error=r"not marked const|discards qualifiers")

consteval_example = examples["constant-evaluation-and-reflection"][0]
check("invalid-digit-rejected", consteval_example + "\nconstexpr auto bad = decimal_digit('x');\n",
      "c++20", expect_error=r"call to consteval function.*decimal_digit.*not a constant expression")
check("runtime-immediate-call-rejected", consteval_example + "\nunsigned test(char input) { return decimal_digit(input); }\n",
      "c++23", expect_error=r"call to consteval function.*decimal_digit.*not a constant expression")

check("fold-empty-and-order", r'''
#include <type_traits>
#include <utility>
template<class... Ts> constexpr int sum(Ts... values) { return (0 + ... + values); }
static_assert(sum() == 0);
static_assert(sum(2, 3, 4) == 9);
template<class... Ts> constexpr int ordered(Ts... values) {
    int result = 0;
    ((result = result * 10 + values), ...);
    return result;
}
static_assert(ordered() == 0);
static_assert(ordered(1, 2, 3) == 123);
''', "c++17")

check("constant-runtime-phase", r'''
consteval int immediate(int n) { return n * 2; }
constexpr int phase(int n) {
    if consteval { return immediate(n); }
    else { return n + 1; }
}
static_assert(phase(3) == 6);
int main(int argc, char**) { return phase(argc) == argc + 1 ? 0 : 1; }
''', "c++23", run=True)

# Capability observation only: a failure is a limitation, not a passed feature test.
probe = WORK / "reflection-probe.cpp"
probe.write_text("#include <meta>\nconstexpr auto type_info = ^^int;\nstatic_assert(std::meta::is_type(type_info));\n", encoding="utf-8")
probe_command = [COMPILER, "-std=c++2c", "-fsyntax-only", str(probe)]
probe_run = subprocess.run(probe_command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=45)
reflection = {"command": probe_command, "exit_code": probe_run.returncode,
              "supported_in_tested_configuration": probe_run.returncode == 0,
              "diagnostics": probe_run.stdout + probe_run.stderr}
print("REFLECTION " + ("available" if probe_run.returncode == 0 else "unavailable in tested configuration"))

version = subprocess.run([COMPILER, "--version"], capture_output=True, text=True).stdout
report = {"compiler_version": version, "checks": results, "reflection_probe": reflection,
          "passed": sum(x["passed"] for x in results), "total": len(results),
          "scope": "Structure, installed examples and focused semantic cases; no independent agent behavioral evaluation or cross-compiler claim."}
(WORK / "results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
assert all(x["passed"] for x in results), "Some semantic checks failed; inspect results.json and logs."
print(f"PASS {len(results)}/{len(results)} semantic checks")
