# C++ Metaprogramming Skill

面向 C++ 元编程的中文 Codex skill：根据功能契约选择、组合、实现和诊断模板、concepts、constexpr 等技巧。

以 **C++20/23** 为主，必要时兼容 **C++17**；C++26 能力须先确认目标工具链支持。

## 能解决什么问题

- 类型计算、traits、类型列表、参数包和惰性实例化。
- concepts、requires、SFINAE、重载选择和模板诊断。
- constexpr、consteval、NTTP、编译期字符串与求值阶段选择。
- 元数据驱动功能、反射适用性以及较大功能中的多技巧组合。
- 编译成本、代码膨胀及验证方法。

每项技巧按 **技巧 + 使用方式 + 场景 + 目的 + 收益** 说明。判断流程从需求和工具链出发，决定是否需要元编程，再按职责选型、检查组合边界并验证。普通函数或现有实现足够时，可以不增加元编程。

## 安装到 Codex

将本仓库克隆到 Codex 的 skills 目录；若设置了 `CODEX_HOME`，使用其下的 `skills` 目录。

PowerShell：

```powershell
$skillRoot = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME 'skills' } else { Join-Path $HOME '.codex/skills' }
git clone https://github.com/Frashmeat/cpp-metaprogramming.git (Join-Path $skillRoot 'cpp-metaprogramming')
```

macOS / Linux：

```bash
git clone https://github.com/Frashmeat/cpp-metaprogramming.git "${CODEX_HOME:-$HOME/.codex}/skills/cpp-metaprogramming"
```

目标目录已存在时，先确认其内容与来源；不要覆盖已有修改。安装后开启新的 Codex 会话。

## 使用示例

```text
使用 $cpp-metaprogramming，诊断这个 concept 为什么接受了不支持 const 读取的引用类型。
```

```text
使用 $cpp-metaprogramming，为 C++20 的字段映射功能设计元数据、约束和参数包展开的组合，说明各技巧的使用方式、场景、目的、收益以及验证方法。
```

```text
使用 $cpp-metaprogramming，判断这段 constexpr 算法是否应该改成 consteval，并检查运行期入口与 C++17 兼容需求。
```

skill 支持自动匹配，也可显式调用。它沿用任务类型：解释和审查不会自动变成实施任务；不会因使用模板就要求展开完整设计流程。

## 内容导航

- [SKILL.md](SKILL.md)：入口、选型与核心边界。
- [功能级判断流程](references/decision-workflow.md)：从契约到实现与反馈。
- [技巧组合](references/technique-composition.md)：较大功能的职责划分与组合案例。
- [类型计算](references/type-computation.md)、[约束与诊断](references/concepts-and-diagnostics.md)、[常量求值与反射](references/constant-evaluation-and-reflection.md)：25 项技巧及示例。
- [验证与成本](references/verification-and-cost.md)：正反例、完整路径及性能证据。
- [参考来源](references/sources.md)：Boost.MP11、mp-units、fmt、stdexec、Boost.Hana、Glaze 及已有 skills 的参考范围。

## 运行验证

需要 Python 3、PyYAML 和 PATH 中的 `clang++`。测试的负向诊断匹配针对 Clang 编写，不声称兼容所有编译器。

```bash
python -m pip install -r tests/requirements.txt
python -X utf8 tests/verify.py
python -X utf8 tests/verify_composition.py
python -X utf8 tests/verify_fixes.py
```

输出写入忽略版本控制的 `.validation/`，包括实际编译命令、诊断和 JSON 结果。

发布前验证环境为 Windows LLVM-MinGW / Clang 22.1.7：文档与语言语义 21 项、组合原型 6 项、修复边界 9 项，共 36 项执行通过，覆盖各示例适用的 C++17/20/23 标准。部分检查在不同标准下验证相同契约。

C++26 反射探针在该环境因缺少 `<meta>` 不可用；不计作通过。未验证 GCC/MSVC、性能收益或 Agent 在任意大型任务中的决策效果。组合测试验证字段投影与输出所有权，并非完整序列化器。

## 许可证

原创指令、文档及示例以 [MIT](LICENSE) 发布。参考项目保留各自许可证；上游链接仅用于说明依据，未将上游完整实现纳入本仓库。
