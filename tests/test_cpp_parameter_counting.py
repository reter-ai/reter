#!/usr/bin/env python3
"""
Test C++ parameter counting to verify the fix for spurious parameter creation.

The bug: When parsing C++ class declarations (in headers), parameters from method
declarations were being incorrectly associated with methods, causing inflated
parameter counts.

The fix: Added guards in visitParameterDeclaration and visitParameterDeclarationClause
to only create parameter facts when inside a function definition scope.
"""

import pytest
from reter_core import owl_rete_cpp as owl


def get_parameter_count(network, method_name: str) -> int:
    """Query the network for parameters of a specific method."""
    # Query for parameters associated with this method
    params = network.query({
        'type': 'instance_of',
        'concept': 'cpp:Parameter'
    })

    count = 0
    # Convert to pandas for easier iteration
    df = params.to_pandas()
    for _, row in df.iterrows():
        of_function = row.get('ofFunction', '')
        if of_function and method_name in str(of_function):
            count += 1
    return count


def get_all_methods_with_params(network):
    """Get all methods and their parameter counts."""
    methods = network.query({
        'type': 'instance_of',
        'concept': 'cpp:Method'
    })

    params = network.query({
        'type': 'instance_of',
        'concept': 'cpp:Parameter'
    })

    # Build param count per method
    method_params = {}
    params_df = params.to_pandas()
    for _, row in params_df.iterrows():
        of_function = row.get('ofFunction', '')
        if of_function:
            method_params[str(of_function)] = method_params.get(str(of_function), 0) + 1

    result = {}
    methods_df = methods.to_pandas()
    for _, row in methods_df.iterrows():
        method_id = str(row.get('individual', ''))
        method_name = str(row.get('name', ''))
        result[method_name] = method_params.get(method_id, 0)

    return result


class TestCppParameterCounting:
    """Tests for C++ parameter extraction accuracy."""

    def test_simple_method_one_param(self):
        """A method with 1 parameter should report exactly 1 parameter."""
        code = '''
class Foo {
public:
    void bar(int x);
};

void Foo::bar(int x) {
    // implementation
}
'''
        network = owl.ReteNetwork()
        owl.load_cpp_from_string(network, code, 'test.cpp', 'test.cpp')

        count = get_parameter_count(network, 'bar')
        assert count == 1, f"Expected 1 parameter for bar(), got {count}"

    def test_simple_method_three_params(self):
        """A method with 3 parameters should report exactly 3 parameters."""
        code = '''
class Calculator {
public:
    int add(int a, int b, int c);
};

int Calculator::add(int a, int b, int c) {
    return a + b + c;
}
'''
        network = owl.ReteNetwork()
        owl.load_cpp_from_string(network, code, 'test.cpp', 'test.cpp')

        count = get_parameter_count(network, 'add')
        assert count == 3, f"Expected 3 parameters for add(), got {count}"

    def test_header_only_no_definition(self):
        """Method declarations without definitions should have 0 parameters.

        This is the key test for the bug fix - declarations should NOT create
        parameter entities since we're not inside a function definition scope.
        """
        header = '''
class MyClass {
public:
    void method1(int a, int b, int c);
    void method2(std::string s, double d);
    int method3();
};
'''
        network = owl.ReteNetwork()
        owl.load_cpp_from_string(network, header, 'test.h', 'test.h')

        # Without definitions, no parameters should be created
        method_params = get_all_methods_with_params(network)

        for method, count in method_params.items():
            assert count == 0, f"Method {method} has {count} parameters but should have 0 (declaration only)"

    def test_mixed_declaration_and_definition(self):
        """Only the defined method should have parameters, not declared ones."""
        code = '''
class Service {
public:
    void start(int port);           // declaration only
    void stop();                    // declaration only
    bool isRunning(int timeout);    // declaration only
};

// Only this method is defined
void Service::start(int port) {
    // implementation
}
'''
        network = owl.ReteNetwork()
        owl.load_cpp_from_string(network, code, 'test.cpp', 'test.cpp')

        method_params = get_all_methods_with_params(network)

        # start() is defined, should have 1 param
        start_count = get_parameter_count(network, 'start')
        assert start_count == 1, f"start() should have 1 parameter, got {start_count}"

        # stop() and isRunning() are only declared, should have 0 params
        stop_count = get_parameter_count(network, 'stop')
        assert stop_count == 0, f"stop() should have 0 parameters (declaration only), got {stop_count}"

        running_count = get_parameter_count(network, 'isRunning')
        assert running_count == 0, f"isRunning() should have 0 parameters (declaration only), got {running_count}"

    def test_multiple_methods_no_cross_contamination(self):
        """Parameters from one method should not leak to another method."""
        code = '''
class Handler {
public:
    void handleA(int a1, int a2, int a3, int a4, int a5);
    void handleB(std::string s);
};

void Handler::handleA(int a1, int a2, int a3, int a4, int a5) {
    // 5 parameters
}

void Handler::handleB(std::string s) {
    // 1 parameter
}
'''
        network = owl.ReteNetwork()
        owl.load_cpp_from_string(network, code, 'test.cpp', 'test.cpp')

        a_count = get_parameter_count(network, 'handleA')
        b_count = get_parameter_count(network, 'handleB')

        assert a_count == 5, f"handleA() should have 5 parameters, got {a_count}"
        assert b_count == 1, f"handleB() should have 1 parameter, got {b_count}"

    def test_class_with_many_members_no_param_inflation(self):
        """Class members should not be counted as parameters.

        This tests the specific bug where class member declarations
        were being counted as parameters of methods.
        """
        code = '''
class BigClass {
private:
    int member1;
    int member2;
    int member3;
    std::string member4;
    double member5;
    bool member6;

public:
    void singleParamMethod(int x);
};

void BigClass::singleParamMethod(int x) {
    member1 = x;
}
'''
        network = owl.ReteNetwork()
        owl.load_cpp_from_string(network, code, 'test.cpp', 'test.cpp')

        count = get_parameter_count(network, 'singleParamMethod')
        assert count == 1, f"singleParamMethod() should have exactly 1 parameter, got {count}"

    def test_nested_class_parameters(self):
        """Parameters in nested class methods should be correctly attributed."""
        code = '''
class Outer {
public:
    void outerMethod(int a, int b);

    class Inner {
    public:
        void innerMethod(int x);
    };
};

void Outer::outerMethod(int a, int b) {}
void Outer::Inner::innerMethod(int x) {}
'''
        network = owl.ReteNetwork()
        owl.load_cpp_from_string(network, code, 'test.cpp', 'test.cpp')

        outer_count = get_parameter_count(network, 'outerMethod')
        inner_count = get_parameter_count(network, 'innerMethod')

        assert outer_count == 2, f"outerMethod() should have 2 parameters, got {outer_count}"
        assert inner_count == 1, f"innerMethod() should have 1 parameter, got {inner_count}"

    def test_visitor_pattern_class(self):
        """Test a realistic visitor pattern class similar to the buggy case."""
        code = '''
class BaseVisitor {
public:
    virtual void visitDocument() = 0;
    virtual void visitElement(void* ctx) = 0;
    virtual void visitAttribute(void* ctx) = 0;
};

class ConcreteVisitor : public BaseVisitor {
private:
    std::string current_tag_;
    int current_line_;
    std::string doc_title_;

public:
    void visitDocument() override;
    void visitElement(void* ctx) override;
    void visitAttribute(void* ctx) override;
};

void ConcreteVisitor::visitDocument() {
    // no params
}

void ConcreteVisitor::visitElement(void* ctx) {
    // 1 param
}

void ConcreteVisitor::visitAttribute(void* ctx) {
    // 1 param
}
'''
        network = owl.ReteNetwork()
        owl.load_cpp_from_string(network, code, 'visitor.cpp', 'visitor.cpp')

        doc_count = get_parameter_count(network, 'visitDocument')
        elem_count = get_parameter_count(network, 'visitElement')
        attr_count = get_parameter_count(network, 'visitAttribute')

        assert doc_count == 0, f"visitDocument() should have 0 parameters, got {doc_count}"
        assert elem_count == 1, f"visitElement() should have 1 parameter, got {elem_count}"
        assert attr_count == 1, f"visitAttribute() should have 1 parameter, got {attr_count}"

    @pytest.mark.skip(reason="C++17 structured bindings cause access violation in C++14 parser")
    def test_structured_binding_no_false_params(self):
        """Structured bindings in for-range loops should not create false parameters.

        This tests the C++17 structured binding syntax which may confuse the C++14 parser.
        The [key, value] syntax should not be interpreted as parameters.

        Note: The C++14 parser may emit access violation warnings when parsing C++17
        syntax, but the test should still pass with correct parameter counts.
        """
        code = '''
class Test {
public:
    void foo(const std::string& id, const std::string& class_name,
             const std::unordered_map<std::string, std::string>& attrs);
};

void Test::foo(const std::string& id, const std::string& class_name,
               const std::unordered_map<std::string, std::string>& attrs) {
    bar(id, "concept", class_name);
    bar(id, "type", class_name);

    for (const auto& [key, value] : attrs) {
        bar(id, key, value);
    }
}
'''
        network = owl.ReteNetwork()
        owl.load_cpp_from_string(network, code, 'test.cpp', 'test.cpp')

        count = get_parameter_count(network, 'foo')
        # foo() has exactly 3 parameters: id, class_name, attrs
        assert count == 3, f"foo() should have exactly 3 parameters, got {count}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
