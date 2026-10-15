# 约束设计与模板诊断

在 concepts、requires、SFINAE、重载歧义和深层模板错误任务中读取。主要依据为 [mp-units、MP11 与 stdexec](sources.md)。

## 技巧、使用方式、场景、目的与收益

| 技巧 | 使用方式 | 场景 | 目的 | 收益 |
|---|---|---|---|---|
| Concepts 与 requires | 将实际需要的表达式/类型关系写成可组合的命名约束 | 泛型算法、字段访问、自定义类型接口 | 表达接口可用条件 | 不合适的类型能在接口边界被拒绝，调用条件更清楚 |
| SFINAE 与检测惯用法 | 在直接替换上下文检测操作，以 enable_if 等影响候选集合 | C++17 接口维护或已有检测体系 | 在既定标准下提供条件可用接口 | 保持兼容，减少为支持新类型而手写的重载 |
| if constexpr | 在已选中的模板内部按静态条件分支 | 类型分类、条件调用、参数包递归终止 | 避免实例化不适用的依赖分支 | 相关实现可集中表达，减少额外辅助结构 |
| 重载与 tag dispatch | 用约束、参数类型或能力标签选择独立实现 | 不同迭代器能力、存储类别、可扩展算法 | 划分实现边界和选择规则 | 各实现可独立组织；合理设计时便于扩展与诊断 |
| 元错误传播 | 在复杂类型流水线中显式携带失败原因，在边界形成诊断 | 多层元函数、异步结果类型组合 | 避免深层错误丢失语义上下文 | 复杂失败更容易解释；简单函数不承担额外框架成本 |

前两项解决候选接口是否可用，if constexpr 解决选中实现内部的分支；不能仅因都涉及条件判断就互换。边界上的收益需用真实允许/拒绝用例确认，不能保证所有编译器诊断都会更短。

## if constexpr 与实现分派

- 分支条件必须满足相应常量表达式要求。丢弃分支不等于忽略语法、所有非依赖名称检查或无条件形成的返回类型。
- 多种实现属于一个局部算法时可考虑 if constexpr；需要独立扩展点时比较受约束重载或现有 tag dispatch。tag dispatch 本身不保证可避免所有运行期开销。
- 调整重载需保留原有可见性、ADL 和用户定制行为；增加 catch-all 重载不是约束错误的通用补丁。

## 让检查与实际操作一致

写约束前找到函数体真正使用的表达式：对象是否 const、是左值还是右值、结果是精确类型还是允许转换、是否确实要求 noexcept。不要增加实现不需要的默认构造或复制条件。

requires 的局部参数即便声明为 `T&& x`，表达式 `x` 仍是左值；若接口确实转发，检查表达式也应使用相应的 `std::forward<T>(x)`。

下面的检查约定为“对 T 的被引用类型添加 const 后，以左值读取”，因此先去除引用，再添加 const；保留原有 volatile。直接写 `const T&` 时，若 T 已是引用，const 不会施加到被引用对象上。该处理只适用于这个契约，实际转发接口仍应按真实 cv/ref 和值类别检查。

完整的 C++20 例子同时覆盖对象、引用及 const/volatile 差异：

```cpp
#include <concepts>
#include <type_traits>

template<class T>
concept ConstReadable = requires(const std::remove_reference_t<T>& object) {
    { object.read() } -> std::same_as<int>;
};

template<class T>
concept ResettableReadable = ConstReadable<T> && requires(T& object) {
    object.reset();
};

template<ConstReadable T> constexpr int select(const T&) { return 1; }
template<ResettableReadable T> constexpr int select(const T&) { return 2; }

struct Plain { int read() const; };
struct Rich { int read() const; void reset(); };
struct MutableOnly { int read(); };

static_assert(ConstReadable<Plain>);
static_assert(ConstReadable<Plain&>);
static_assert(ConstReadable<const Plain&>);
static_assert(ConstReadable<Plain&&>);
static_assert(!ConstReadable<volatile Plain&>);
static_assert(!ConstReadable<MutableOnly>);
static_assert(!ConstReadable<MutableOnly&>);
static_assert(!ConstReadable<MutableOnly&&>);
static_assert(select(Plain{}) == 1);
static_assert(select(Rich{}) == 2);
```

该例的重载层次复用了命名 concept。函数没有调用 read/reset，因而仅声明这些成员即可。

## 区分短路、语义蕴含和 subsumption

- 约束合取按规则短路，前置约束可保护后续依赖表达式；这不等于 subsumption。
- Subsumption 影响约束声明的排序。逻辑上相同或更强的表达式，不一定具有规则要求的相同原子约束身份。
- 两次分别写 `requires(T x) { x.read(); }`，不能仅因文本一样就假定能建立重载偏序。优先复用命名 concept，必要时构造最小重载测试。
- C++26 的折叠展开约束与之前标准的排序规则有差异；包含参数包的重载必须在项目实际标准下验证。
- requires 只能证明它检查的表达式/类型要求。排序关系、相等性保持、迭代器语义等性质还可能需要其他依据。

## SFINAE 与 C++17

维护 C++17 接口时，可用检测惯用法、enable_if 和 tag dispatch；不自动将整个项目升级至 C++20。改成 concepts 时验证歧义、可见性、候选集合及原有重载行为，不能只替换语法。

下面的 C++17 检测与前述 const 可读语义一致：

```cpp
#include <type_traits>
#include <utility>

template<class T, class = void> struct const_readable : std::false_type {};
template<class T>
struct const_readable<T, std::void_t<decltype(
    std::declval<const std::remove_reference_t<T>&>().read())>>
    : std::is_same<decltype(
          std::declval<const std::remove_reference_t<T>&>().read()), int> {};

struct ConstReader { int read() const; };
struct MutableReader { int read(); };
static_assert(const_readable<ConstReader>::value);
static_assert(const_readable<ConstReader&>::value);
static_assert(const_readable<const ConstReader&>::value);
static_assert(const_readable<ConstReader&&>::value);
static_assert(!const_readable<volatile ConstReader&>::value);
static_assert(!const_readable<MutableReader>::value);
static_assert(!const_readable<MutableReader&>::value);
static_assert(!const_readable<MutableReader&&>::value);
static_assert(!const_readable<int>::value);
```

## 诊断路径

1. 保留编译器版本、实际标准、出错调用和相关重载，复现首个有意义的失败。
2. 根据诊断内容定位：名称查找/ADL、模板推导、替换、约束满足、偏序，还是函数体实例化。不同编译器输出顺序不同，不机械要求从最上或最下读取。
3. 展开实际的 T、cv/ref 和被检查表达式；把约束与实现逐项对应。
4. 减小无关代码，同时保留导致问题的依赖关系、重载可见性和编译选项。
5. 以正向和负向用例确认修复；不要用增加模板深度、删除约束或宽泛 catch-all 重载遮盖根因。

GCC/Clang 的 `-ftemplate-backtrace-limit` 控制诊断回溯数量；`-ftemplate-depth` 限制实例化深度，会影响能否编译。GCC 的 `-fconcepts-diagnostics-depth` 可用于深入约束诊断，先确认工具链支持；不要将它当作跨编译器通用选项。

复杂库可以参考 stdexec 的错误类型传播，在接口边界呈现深层失败原因。普通模板函数先用清晰约束和恰当 static_assert，避免额外建立错误传播框架。
