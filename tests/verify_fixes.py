"""Validate the installed examples changed by the review fixes."""
from pathlib import Path
import json
import re
import shutil
import subprocess

root = Path(__file__).resolve().parents[1]
work = root / '.validation' / 'fixes'
work.mkdir(parents=True, exist_ok=True)
compiler = shutil.which('clang++')
assert compiler
results = []

def blocks(name):
    return re.findall(r'```cpp\n(.*?)```', (root / 'references' / name).read_text(encoding='utf-8'), re.S)

def check(name, source, standard, reject=False, run=False):
    path = work / (name + '.cpp')
    path.write_text(source, encoding='utf-8')
    exe = work / (name + '.exe')
    command = [compiler, '-std=' + standard, '-Wall', '-Wextra', '-Wpedantic', '-Werror']
    command += [str(path), '-o', str(exe)] if run else ['-fsyntax-only', str(path)]
    process = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=45)
    diagnostics = process.stdout + process.stderr
    passed = process.returncode == 0
    if reject:
        passed = process.returncode != 0 and bool(re.search(r'call to consteval function.*immediate.*not a constant expression', diagnostics))
        passed = passed and 'file not found' not in diagnostics
    runtime_exit = None
    if passed and run:
        runtime = subprocess.run([str(exe)], capture_output=True, text=True, timeout=10)
        runtime_exit = runtime.returncode
        passed = runtime_exit == 0
    results.append(dict(name=name, standard=standard, command=command, passed=passed,
                        compile_exit=process.returncode, runtime_exit=runtime_exit, diagnostics=diagnostics))
    print(('PASS ' if passed else 'FAIL ') + name)

concept, trait = blocks('concepts-and-diagnostics.md')
concept += '''
struct VolatileReader { int read() const volatile; };
struct WrongResult { long read() const; };
static_assert(ConstReadable<volatile VolatileReader&>);
static_assert(!ConstReadable<const MutableOnly&>);
static_assert(!ConstReadable<WrongResult&>);
static_assert(!ConstReadable<void>);
static_assert(!ConstReadable<int&>);
static_assert(ResettableReadable<Rich&>);
static_assert(!ResettableReadable<const Rich&>);
'''
trait += '''
struct VolatileReader { int read() const volatile; };
struct WrongResult { long read() const; };
static_assert(const_readable<volatile VolatileReader&>::value);
static_assert(!const_readable<const MutableReader&>::value);
static_assert(!const_readable<WrongResult&>::value);
static_assert(!const_readable<void>::value);
static_assert(!const_readable<int&>::value);
'''
for standard in ('c++20', 'c++23'):
    check('concept-' + standard, concept, standard)
for standard in ('c++17', 'c++20', 'c++23'):
    check('trait-' + standard, trait, standard)

digit, invalid, immediate_branch, shared_helper = blocks('constant-evaluation-and-reflection.md')
check('ordinary-if-rejected', invalid, 'c++20', reject=True)
runtime_test = '''
int main(int argc, char**) {
    return ordinary_call(argc) == argc + 1 && compute(argc) == argc + 1 ? 0 : 1;
}
'''
check('if-consteval-runtime', immediate_branch + runtime_test, 'c++23', run=True)
for standard in ('c++20', 'c++23'):
    check('shared-helper-runtime-' + standard, shared_helper + runtime_test, standard, run=True)

links = 0
for path in [root / 'SKILL.md', *list((root / 'references').rglob('*.md'))]:
    content = path.read_text(encoding='utf-8')
    assert '\ufffd' not in content
    for target in re.findall(r'\]\(([^)]+)\)', content):
        if not target.startswith(('http://', 'https://', '#')):
            assert (path.parent / target.split('#')[0]).is_file(), (path, target)
            links += 1
report = dict(compiler_version=subprocess.run([compiler, '--version'], capture_output=True, text=True).stdout,
              checks=results, valid_local_links=links)
(work / 'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
assert all(item['passed'] for item in results)
print(f'PASS {len(results)}/{len(results)} focused checks; {links} local links valid')
