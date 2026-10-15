# 参考来源与取舍

这些链接用于追溯实现依据和按需深入，不要求每次加载或联网。调查日期为 2026-10-14；仓库源码链接固定到当时读取的 commit，不能据此推断当前主分支的能力。

本 skill 的指令与小例子为重新编写；未复制上游完整实现、许可证受限内容或工作流。后续若直接复制或实质改编上游内容，需检查具体文件许可并保留要求的声明。仅有公开仓库不代表可任意再许可。

## 现成 skills：保留主题，重写指导

- [cpp-templates](https://github.com/mohitmishra786/low-level-dev-skills/blob/bdc58472fa9f309ed1b3f7d985a0d8e9bd8f4608/skills/compilers/cpp-templates/SKILL.md)，MIT：参考模板诊断、约束和编译成本主题；纠正模板深度与诊断深度、短路与 subsumption 的混淆。
- [cpp-pro](https://github.com/jeffallan/claude-skills/tree/main/skills/cpp-pro)，MIT，动态链接：参考按主题组织资料；不继承通用 C++ 职责和每次强制运行 sanitizer 的规则。
- [alexandrescu-modern-cpp-design](https://github.com/copyleftdev/sk1llz/blob/master/languages/cpp/alexandrescu/SKILL.md)，Apache-2.0，动态链接：参考类型驱动设计主题；不采用“所有可做的计算都移到编译期”的普遍要求。
- Han 的 cpp-templates-metaprogramming 使用 FSL-1.1-ALv2，且抽查发现示例缺陷；未选作派生底稿。

## 核心仓库

### Boost.MP11 — Boost Software License 1.0

快照 `0daffd6401724ddf473fd39d28f68e138d9a1303`。

- [utility.hpp](https://github.com/boostorg/mp11/blob/0daffd6401724ddf473fd39d28f68e138d9a1303/include/boost/mp11/utility.hpp)：条件元函数与惰性求值。
- [mp_defer.hpp](https://github.com/boostorg/mp11/blob/0daffd6401724ddf473fd39d28f68e138d9a1303/include/boost/mp11/detail/mp_defer.hpp)：有效性检测与延迟实例化。
- [mp_eval_if_sf.cpp](https://github.com/boostorg/mp11/blob/0daffd6401724ddf473fd39d28f68e138d9a1303/test/mp_eval_if_sf.cpp)：合法/非法替换与不同参数数量。

借鉴类型算法组合和替换边界，不搬入历史编译器 workaround。

### mp-units — MIT

快照 `f48e47a040ae7aed50250275c3825c0a8cbe140f`。

- [quantity_concepts.h](https://github.com/mpusz/mp-units/blob/f48e47a040ae7aed50250275c3825c0a8cbe140f/src/core/include/mp-units/framework/quantity_concepts.h)：领域约束与命名 concept 组合。
- [concepts_test.cpp](https://github.com/mpusz/mp-units/blob/f48e47a040ae7aed50250275c3825c0a8cbe140f/test/static/concepts_test.cpp)：正反静态断言。
- [ci-compile-time.yml](https://github.com/mpusz/mp-units/blob/f48e47a040ae7aed50250275c3825c0a8cbe140f/.github/workflows/ci-compile-time.yml)：固定工具链与基准输入的编译成本比较。

借鉴约束设计和测量方法，不将其领域模型或完整 CI 门禁推广到普通项目。

### fmt — MIT，具体复用核对仓库 LICENSE 与文件声明

快照 `b4ffa39b9994c961418406f47358791d89a5aa48`。

- [core.h](https://github.com/fmtlib/fmt/blob/b4ffa39b9994c961418406f47358791d89a5aa48/include/fmt/core.h)：`fstring`、格式检查器和运行期入口。此快照的 base.h 是兼容包含入口。
- [compile.h](https://github.com/fmtlib/fmt/blob/b4ffa39b9994c961418406f47358791d89a5aa48/include/fmt/compile.h)：可选编译期解析与特化。
- [compile-error-test](https://github.com/fmtlib/fmt/blob/b4ffa39b9994c961418406f47358791d89a5aa48/test/compile-error-test/CMakeLists.txt)：成功对照与预期编译失败。

借鉴检查阶段和执行阶段的区分，不预设编译期解析总比运行期方案合适。

## 专项仓库

### NVIDIA/stdexec — Apache-2.0 WITH LLVM-exception

快照 `5fc945fac81ae9b5b4ef190d20d0d74b705bee2a`。

- [__meta.hpp](https://github.com/NVIDIA/stdexec/blob/5fc945fac81ae9b5b4ef190d20d0d74b705bee2a/include/stdexec/__detail/__meta.hpp)：类型错误传播及元函数调用。
- [__completion_signatures.hpp](https://github.com/NVIDIA/stdexec/blob/5fc945fac81ae9b5b4ef190d20d0d74b705bee2a/include/stdexec/__detail/__completion_signatures.hpp)：类型集合变换和按需实例化。

仅在复杂类型流水线中借鉴诊断策略，不照搬框架和保留标识符命名。该快照 README 声明实验性和 API 演进。

### Boost.Hana — Boost Software License 1.0

快照 `bc49ee25638e59d977edff5737b4e6bf12c1e5ea`。

- [transform.hpp](https://github.com/boostorg/hana/blob/bc49ee25638e59d977edff5737b4e6bf12c1e5ea/include/boost/hana/transform.hpp)：异构序列操作。
- [eval_if.hpp](https://github.com/boostorg/hana/blob/bc49ee25638e59d977edff5737b4e6bf12c1e5ea/include/boost/hana/eval_if.hpp)：常量条件与运行期条件的分支求值。

借鉴类型/对象混合计算；其历史 concepts/tag dispatch 与 C++20 concepts 不是同一种机制。

### Glaze — MIT

快照 `e194d23e33c0739a7214161af27e47bc9a6a4e30`。

- [meta.hpp](https://github.com/stephenberry/glaze/blob/e194d23e33c0739a7214161af27e47bc9a6a4e30/include/glaze/core/meta.hpp)：元数据与可选反射分支。
- [json_reflection_test.cpp](https://github.com/stephenberry/glaze/blob/e194d23e33c0739a7214161af27e47bc9a6a4e30/tests/json_reflection_test/json_reflection_test.cpp)：自定义元数据与默认反射的类型分类。
- [README](https://github.com/stephenberry/glaze/blob/e194d23e33c0739a7214161af27e47bc9a6a4e30/README.md)：该快照要求 C++23，可选 C++26 P2996 后端。

借鉴反射与元数据边界。实际工具链支持以任务当时的探针和官方资料为准，不固定历史编译器名单。
