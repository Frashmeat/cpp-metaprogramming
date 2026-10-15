# 常量求值、NTTP 与反射

在编译期值计算、字符串处理、强制校验、非类型模板参数或 C++26 反射任务中读取。实现参考为 [fmt 与 Glaze](sources.md)。

## 技巧、使用方式、场景、目的与收益

| 技巧 | 使用方式 | 场景 | 目的 | 收益 |
|---|---|---|---|---|
| constexpr 计算 | 用普通函数、循环和可用标准容器计算；需要静态结果时放入常量表达式上下文 | 固定映射、查找表、尺寸或单位换算 | 使值算法可参与常量求值 | 可复用运行期/编译期逻辑，按需提前产生结果 |
| consteval 立即函数 | 在接口边界要求相应调用常量求值 | 固定格式、静态配置、已知字符串校验 | 强制提前检查已知输入 | 某些错误不会推迟到程序运行时才发现 |
| 非类型模板参数 NTTP | 将合法的值作为模板参数，让它参与类型或实现选择 | 固定尺寸、静态字符串、静态策略 | 让值决定类型身份或代码结构 | 可表达尺寸等静态关系，并生成对应实现 |
| static_assert | 对静态条件形成成功断言或编译诊断 | 配置关系、类型不变量、编译期测试 | 拒绝违反静态契约的程序 | 提前发现错误，并提供相关说明 |
| 常量求值路径选择 | 用普通 if + is_constant_evaluated，或 C++23 if consteval 区分路径 | 同一算法需适配两个求值环境 | 在各环境中使用合法且合适的实现 | 可以共享接口，同时利用不同执行环境的能力 |
| 元数据驱动 | 显式登记字段名、成员指针、属性并统一消费 | 序列化、配置映射、RPC、命令行参数 | 为重复操作提供一致的结构描述 | 一份声明可驱动多个操作，减少信息不同步 |
| 静态反射 | 用已确认可用的反射能力查询结构并参与生成 | 字段遍历、类型适配、自动元数据 | 从程序声明取得可用结构信息 | 在能力范围内减少手工登记与维护 |
| X-macros 等预处理生成 | 用同一条目表按约定展开枚举、名称表或分发声明 | 受限工具链、C/C++ 共享定义、已有宏体系 | 保持多份声明同步 | 减少条目重复维护；诊断与作用域可读性可能变差 |

constinit 作为相关初始化机制在下表辨别，不把它当作编译期计算或元代码生成工具。元数据、宏生成和反射是否需要，与“函数能否 constexpr”是不同决策。

## 选择执行阶段

| 机制 | 可保证的事情 | 不能据此保证 |
|---|---|---|
| constexpr 函数 | 满足条件的调用可以参与常量求值 | 所有调用都在编译期执行 |
| constexpr 变量 / static_assert | 初始化或条件必须满足相应常量表达式要求 | 任意内部操作都合法 |
| consteval 函数 | 按立即函数规则要求相应调用常量求值 | 普通运行期参数能成为常量表达式 |
| constinit 变量 | 满足静态初始化要求 | 对象不可修改或可当作 constexpr 值 |
| std::is_constant_evaluated() | 查询当前是否处于清单常量求值 | 提供立即函数上下文，或检测预处理条件/编译器优化 |
| C++23 if consteval | 区分常量求值路径，在正向分支提供立即函数上下文 | 可以绕过常量求值限制 |

不要写 `if constexpr (std::is_constant_evaluated())` 来选择普通运行期路径；该条件自身处于常量求值上下文。仅区分求值路径可使用普通 if；需要立即函数上下文时，普通 `if (std::is_constant_evaluated())` 不能替代 C++23 的 `if consteval`。

## 受约束的编译期值解析

完整 C++20 例子：接口明确要求一个编译期十进制数字，因此选择 consteval。无效分支的 throw 令该立即调用无法成为常量表达式：

```cpp
consteval unsigned decimal_digit(char value) {
    if (value < '0' || value > '9') {
        throw "expected a decimal digit";
    }
    return static_cast<unsigned>(value - '0');
}

static_assert(decimal_digit('0') == 0);
static_assert(decimal_digit('9') == 9);
```

应另建失败翻译单元检查 `constexpr auto bad = decimal_digit('x');`，以及普通运行期 char 实参；不要把它们放进上述成功例子。若项目禁用异常，选择适合该项目和目标标准的编译期失败手段，并验证诊断，不直接复制 throw。

如果需求也接收运行期值，则采用共享 constexpr 算法或明确的运行期接口，而非强迫用户将动态输入变成模板参数。fmt 的编译期格式检查与显式运行期入口可作为设计参照。

## 路径查询不等于立即函数上下文

以下是应单独编译并确认失败的 C++20 反例：即使条件查询为真，普通 if 也不会建立立即函数上下文；此处形参 n 不能作为该立即调用所需的常量表达式。

```cpp
#include <type_traits>
consteval int immediate(int n) { return n * 2; }
constexpr int compute(int n) {
    if (std::is_constant_evaluated()) {
        return immediate(n); // 预期编译失败
    }
    return n + 1;
}
```

C++23 可使用 if consteval，其正向分支允许在立即函数上下文中将形参传给 consteval 辅助函数；完整的常量求值仍必须合法：

```cpp
consteval int immediate(int n) { return n * 2; }
constexpr int compute(int n) {
    if consteval {
        return immediate(n);
    } else {
        return n + 1;
    }
}
static_assert(compute(3) == 6);
int ordinary_call(int n) { return compute(n); } // 运行期返回 n + 1
```

C++20 若需要共享计算，可将底层算法写为 constexpr，使普通 if 的两条路径各自合法；只有需要强制静态调用的入口才用 consteval 包装。这个替代方案允许底层算法在运行期调用，不保留“辅助函数本身必须立即求值”的限制：

```cpp
#include <type_traits>
constexpr int doubled(int n) { return n * 2; }
consteval int checked_double(int n) { return doubled(n); }
constexpr int compute(int n) {
    if (std::is_constant_evaluated()) {
        return doubled(n);
    }
    return n + 1;
}
static_assert(checked_double(3) == 6);
static_assert(compute(3) == 6);
int ordinary_call(int n) { return compute(n); }
```

## constexpr 的实际边界

- `static_assert(parameter > 0)` 不能直接将普通 constexpr 函数形参变成模板期常量；根据接口需要区分参数值检查和类型/NTTP 约束。
- 注意溢出、越界、生命周期与未定义行为；优化器能折叠某段代码，不等于该代码满足语言层面的常量表达式要求。
- 常量求值过程中可用的动态分配，不代表分配得到的内存能任意逃逸成为持久 constexpr 对象。尤其检查返回容器、string_view、指针和引用的所有权与生命周期。
- constexpr 算法应避免无意义的指数递归；但模板递归改成循环后的编译成本仍须在相关场景测量。
- C++23 的 if consteval、constexpr 标准库能力及编译器实现状态分别核实，不仅看 `-std=`。

## 非类型模板参数

- 在值确实决定类型、重载或代码结构时使用 NTTP。普通计算不必为每个输入值生成一个实例。
- C++20 类类型 NTTP 要满足 structural type 等规则；`std::string` 不能直接作为通用字符串 NTTP 的替代。需要字符串模板参数时，可采用项目已有的 fixed-string 载体并核对值相等语义。
- 检查指针/引用 NTTP 的对象来源、存储期和标准限制；不要假定任何 constexpr 指针都可作为模板实参。
- 参数值数量很多时，评估实例化数量、代码体积和接口复杂度。

## C++26 反射的使用条件

先区分任务需要哪一层能力：已登记的字段列表、聚合对象成员访问、名称提取、标准静态反射，或由反射结果生成声明。它们不是等价能力。

使用前确认：

1. 项目允许使用的标准、编译器和标准库版本。
2. 所需反射功能在该工具链中的具体实现状态，必要时核对官方文档/提案及特性宏。
3. 所需头文件、编译选项和最小能力探针确实可编译。
4. 如果还使用 expansion statements 等配套能力，分别验证，不能从支持反射推导出支持全部相邻特性。

`-std=c++26` 或 `-std=c++2c` 本身不是反射可用性的证据。工具链未支持时如实说明，按任务需要保留现有元数据方案；不自动下载实验编译器或建立复杂回退层。

Glaze 的 C++23 库实现和可选 C++26 后端可用于比较边界。不得把其宏名、编译器名单或历史开关当作所有项目永久适用的标准要求。反射生成代码仍需检查成员可访问性、生命周期、序列化语义和诊断质量。

## 元数据与预处理的边界

- 登记字段时明确名称、顺序、可读写性和定制优先级；字段相同不代表编码、解码和校验具有完全相同的权限或语义。
- 元数据已足够支持功能时，新增反射后端需要明确收益。静态反射也不能替代运行期值校验。
- X-macros 适合已有、有限的声明同步需求；检查宏展开后的作用域、名称冲突和调试体验。标准容器或 constexpr 表能满足需求时，不默认转为预处理生成。
- 宏名列表、反射结果和字段元数据不应各自维护相同事实。较大功能的共同表示与边界见 [技巧组合](technique-composition.md)。
