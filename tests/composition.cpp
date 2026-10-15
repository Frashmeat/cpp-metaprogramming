// Focused composition probe: static field schema -> owned runtime named values.
// Not a production serializer or an independent agent behavior evaluation.
#include <array>
#include <concepts>
#include <string>
#include <string_view>
#include <tuple>
#include <type_traits>
#include <utility>
#include <variant>
#include <vector>

template<auto Pointer>
struct field {
    std::string_view name;
    static constexpr auto pointer = Pointer;
};

template<class T> struct schema;
template<class T> concept Registered = requires { schema<T>::fields; };

template<class T, class Field>
concept SupportedMember = requires(const T& object) { object.*Field::pointer; }
    && (std::same_as<std::remove_cvref_t<decltype(std::declval<const T&>().*Field::pointer)>, int>
        || std::same_as<std::remove_cvref_t<decltype(std::declval<const T&>().*Field::pointer)>, std::string>);

template<Registered T>
constexpr bool supported_fields() {
    return std::apply([](const auto&... descriptors) {
        return (SupportedMember<T, std::remove_cvref_t<decltype(descriptors)>> && ...);
    }, schema<T>::fields);
}

template<Registered T>
constexpr bool valid_names() {
    const auto names = std::apply([](const auto&... descriptors) {
        return std::array<std::string_view, sizeof...(descriptors)>{descriptors.name...};
    }, schema<T>::fields);
    for (std::size_t i = 0; i < names.size(); ++i) {
        if (names[i].empty()) return false;
        for (std::size_t j = i + 1; j < names.size(); ++j) {
            if (names[i] == names[j]) return false;
        }
    }
    return true;
}

template<class T>
concept Projectable = Registered<T> && (supported_fields<T>()) && (valid_names<T>());

using Value = std::variant<int, std::string>;
using Row = std::pair<std::string, Value>;

template<Projectable T>
std::vector<Row> project(const T& object) {
    std::vector<Row> output;
    std::apply([&](const auto&... descriptors) {
        (output.emplace_back(std::string(descriptors.name), Value{object.*descriptors.pointer}), ...);
    }, schema<T>::fields);
    return output;
}

struct Record { int id; std::string name; };
template<> struct schema<Record> {
    static constexpr auto fields = std::tuple{
        field<&Record::id>{"id"}, field<&Record::name>{"name"}};
};
struct Empty {};
template<> struct schema<Empty> { static constexpr auto fields = std::tuple{}; };
struct Duplicate { int left; int right; };
template<> struct schema<Duplicate> {
    static constexpr auto fields = std::tuple{
        field<&Duplicate::left>{"same"}, field<&Duplicate::right>{"same"}};
};
struct Unsupported { double value; };
template<> struct schema<Unsupported> {
    static constexpr auto fields = std::tuple{field<&Unsupported::value>{"value"}};
};
struct WrongOwner {};
template<> struct schema<WrongOwner> {
    static constexpr auto fields = std::tuple{field<&Record::id>{"id"}};
};

static_assert(Projectable<Record>);
static_assert(Projectable<Empty>);
static_assert(!Projectable<Duplicate>);
static_assert(!Projectable<Unsupported>);
static_assert(!Projectable<WrongOwner>);
static_assert(!Projectable<int>);

#if defined(REJECT_DUPLICATE)
void rejected() { (void)project(Duplicate{}); }
#elif defined(REJECT_UNSUPPORTED)
void rejected() { (void)project(Unsupported{}); }
#elif defined(REJECT_WRONG_OWNER)
void rejected() { (void)project(WrongOwner{}); }
#elif defined(REJECT_UNREGISTERED)
void rejected() { (void)project(42); }
#endif

int main(int argc, char**) {
    std::vector<Row> actual;
    {
        Record input{argc, "dynamic value"};
        actual = project(std::as_const(input));
        input.name = "changed after projection";
    }
    // Independent output expectation, not computed through schema iteration.
    const std::vector<Row> expected{
        {"id", Value{argc}}, {"name", Value{std::string{"dynamic value"}}}};
    if (actual != expected) return 1;
    if (!project(Empty{}).empty()) return 2;
    return 0;
}
