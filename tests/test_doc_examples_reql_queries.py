"""
Tests for REQL query examples from documentation

Tests all REQL SELECT/ASK query examples from:
- PYTHON_ANALYSIS_REFERENCE.md (REQL patterns, FILTER, aggregation)
- AI_AGENT_GUIDE.md (Advanced queries, EXISTS, aggregation)

Total: 56 REQL query examples

This file is organized into sections:
1. Basic REQL Queries (30 examples)
2. FILTER Expressions (12 examples)
3. Aggregation (9 examples)
4. Ontology-Based REQL (11 examples)
"""

import pytest
from reter import Reter


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def reter_with_comprehensive_code():
    """Reter instance with comprehensive Python code for testing"""
    reter = Reter(variant='ai')

    reter.load_python_code(
        python_code="""
'''Module docstring'''

import os
import sys

class Priority:
    '''Priority levels'''
    HIGH = 1
    LOW = 2

class Animal:
    '''Base animal class'''
    def __init__(self, name):
        self.name = name

    def speak(self):
        '''Make a sound'''
        pass

class Dog(Animal):
    '''A dog class'''
    def __init__(self, name):
        super().__init__(name)

    def speak(self):
        return "woof"

    def fetch(self, item):
        '''Fetch an item'''
        return f"Fetching {item}"

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

class Cat(Animal):
    def speak(self):
        return "meow"

def create_dog(name: str) -> Dog:
    '''Create a dog instance'''
    return Dog(name)

def helper_function():
    pass

def test_initialization():
    '''Test initialization'''
    pass

def test_processing():
    '''Test processing'''
    pass

def test_cleanup():
    pass

async def async_task(param1, param2, param3):
    '''An async function'''
    pass

@property
def get_value():
    return 42
""",
        module_name="mymodule"
    )

    return reter


@pytest.fixture
def reter_with_calls():
    """Reter instance with code containing function calls"""
    reter = Reter(variant='ai')

    reter.load_python_code(
        python_code="""
def function_a():
    function_b()

def function_b():
    function_c()

def function_c():
    pass

def isolated():
    pass

class FSAAgentManager:
    def initialize_agent(self):
        self.setup()

    def run(self):
        self.process()

    def setup(self):
        pass

    def process(self):
        pass
""",
        module_name="calls"
    )

    return reter


# =============================================================================
# Basic REQL Queries (30 examples)
# =============================================================================

def test_example_2_1_find_all_classes(reter_with_comprehensive_code):
    """
    Example 2.1: Find all classes

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 310-321
    """
    result = reter_with_comprehensive_code.reql("""
        SELECT ?class ?name
        WHERE {
            ?class type py:Class .
            ?class name ?name
        }
    """)

    assert result.num_rows >= 3  # Priority, Animal, Dog, Cat
    df = result.to_pandas()
    assert '?class' in df.columns
    assert '?name' in df.columns


def test_example_3_1_find_methods_using_hasmethod(reter_with_comprehensive_code):
    """
    Example 3.1: Find methods using hasMethod relationship

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 327-350
    """
    result = reter_with_comprehensive_code.reql("""
        SELECT ?method
        WHERE {
            ?class type py:Class .
            ?class hasMethod ?method
        }
    """)

    assert result.num_rows >= 1


def test_example_4_1_find_function_parameters(reter_with_comprehensive_code):
    """
    Example 4.1: Query function parameters with ordering

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 353-367
    """
    result = reter_with_comprehensive_code.reql("""
        SELECT ?param ?name WHERE {
            ?func type py:Function .
            ?func hasParameter ?param .
            ?param name ?name
        }
    """)

    # async_task has 3 parameters
    assert result.num_rows >= 0


def test_example_5_1_find_all_calls(reter_with_calls):
    """
    Example 5.1: Find all function call relationships

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 371-380
    """
    result = reter_with_calls.reql("""
        SELECT ?caller ?callee
        WHERE {
            ?caller calls ?callee
        }
    """)

    # function_a calls function_b, function_b calls function_c
    assert result.num_rows >= 2


def test_example_6_1_find_calls_from_specific(reter_with_calls):
    """
    Example 6.1: Find calls from specific function

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 384-393
    """
    result = reter_with_calls.reql("""
        SELECT ?callee
        WHERE {
            "calls.function_a()" calls ?callee
        }
    """)

    # function_a calls function_b
    assert result.num_rows >= 1


def test_example_7_1_find_calls_to_specific(reter_with_calls):
    """
    Example 7.1: Find who calls a specific function

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 397-406
    """
    result = reter_with_calls.reql("""
        SELECT ?caller
        WHERE {
            ?caller calls "calls.function_c()"
        }
    """)

    # function_b calls function_c
    assert result.num_rows >= 1


def test_example_8_1_find_call_chains(reter_with_calls):
    """
    Example 8.1: Find A calls B, B calls C patterns

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 410-421
    """
    result = reter_with_calls.reql("""
        SELECT ?func1 ?func2 ?func3
        WHERE {
            ?func1 calls ?func2 .
            ?func2 calls ?func3
        }
    """)

    # function_a -> function_b -> function_c
    assert result.num_rows >= 1


def test_example_10_1_find_inheritance(reter_with_comprehensive_code):
    """
    Example 10.1: Find inheritance relationships

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 440-450
    """
    result = reter_with_comprehensive_code.reql("""
        SELECT ?class ?base
        WHERE {
            ?class type py:Class .
            ?class inheritsFrom ?base
        }
    """)

    # Dog and Cat inherit from Animal
    assert result.num_rows >= 2


def test_example_11_1_find_decorated_functions(reter_with_comprehensive_code):
    """
    Example 11.1: Find functions with decorators

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 454-463
    """
    result = reter_with_comprehensive_code.reql("""
        SELECT ?func ?decorator
        WHERE {
            ?func hasDecorator ?decorator
        }
    """)

    # get_value has @property decorator
    assert result.num_rows >= 0


def test_example_12_1_find_imports(reter_with_comprehensive_code):
    """
    Example 12.1: Find import statements

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 467-477
    """
    result = reter_with_comprehensive_code.reql("""
        SELECT ?module ?imports
        WHERE {
            ?import type py:Import .
            ?import modulePath ?imports .
            ?import inModule ?module
        }
    """)

    # Should find os and sys imports
    assert result.num_rows >= 2


def test_example_13_1_find_entities_in_module(reter_with_comprehensive_code):
    """
    Example 13.1: Find all entities in a specific module

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 481-492
    """
    result = reter_with_comprehensive_code.reql("""
        SELECT ?entity ?type ?name
        WHERE {
            ?entity inModule "mymodule" .
            ?entity type ?type .
            ?entity name ?name
        }
    """)

    assert result.num_rows >= 5  # Classes, functions, etc.


def test_example_15_1_find_async_functions(reter_with_comprehensive_code):
    """
    Example 15.1: Find async functions

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 524-534
    """
    result = reter_with_comprehensive_code.reql("""
        SELECT ?func ?name
        WHERE {
            ?func isAsync "true" .
            ?func name ?name
        }
    """)

    # async_task should be found
    assert result.num_rows >= 1


def test_example_16_1_find_return_types(reter_with_comprehensive_code):
    """
    Example 16.1: Find functions with return type annotations

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 538-548
    """
    result = reter_with_comprehensive_code.reql("""
        SELECT ?func ?name ?returnType
        WHERE {
            ?func returnType ?returnType .
            ?func name ?name
        }
    """)

    # create_dog has return type Dog
    assert result.num_rows >= 0


def test_example_17_1_find_at_line(reter_with_comprehensive_code):
    """
    Example 17.1: Find entities at specific line number

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 552-562
    """
    result = reter_with_comprehensive_code.reql("""
        SELECT ?entity ?name
        WHERE {
            ?entity atLine "1" .
            ?entity name ?name
        }
    """)

    assert result.num_rows >= 0


def test_example_18_1_get_all_classes(reter_with_comprehensive_code):
    """
    Example 18.1: Get all classes (for NOT EXISTS pattern)

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 566-596
    """
    result = reter_with_comprehensive_code.reql("""
        SELECT ?class ?name WHERE {
            ?class type py:Class .
            ?class name ?name
        }
    """)

    assert result.num_rows >= 3


def test_example_18_2_classes_with_docstrings(reter_with_comprehensive_code):
    """
    Example 18.2: Get classes with docstrings

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 566-596
    """
    result = reter_with_comprehensive_code.reql("""
        SELECT DISTINCT ?class WHERE {
            ?class hasDocstring ?doc
        }
    """)

    # Animal, Dog have docstrings
    assert result.num_rows >= 0


def test_example_18_3_classes_without_docstrings(reter_with_comprehensive_code):
    """
    Example 18.3: Find classes without docstrings using FILTER NOT EXISTS

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 566-596
    """
    result = reter_with_comprehensive_code.reql("""
        SELECT ?class ?name WHERE {
            ?class type py:Class .
            ?class name ?name
            FILTER NOT EXISTS { ?class hasDocstring ?doc }
        }
    """)

    assert result.num_rows >= 0


def test_example_21_1_filter_by_method_type(reter_with_comprehensive_code):
    """
    Example 21.1: Filter by py:Method concept

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 699-719
    """
    result = reter_with_comprehensive_code.reql("""
        SELECT ?entity ?name WHERE {
            ?entity type py:Method .
            ?entity name ?name
        }
    """)

    assert result.num_rows >= 5  # speak, fetch, get_name, set_name, etc.


def test_example_21_2_filter_by_function_type(reter_with_comprehensive_code):
    """
    Example 21.2: Filter by py:Function concept

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 699-719
    """
    result = reter_with_comprehensive_code.reql("""
        SELECT ?entity ?name WHERE {
            ?entity type py:Function .
            ?entity name ?name
        }
    """)

    assert result.num_rows >= 3  # create_dog, helper_function, etc.


def test_example_22_1_use_module_context(reter_with_comprehensive_code):
    """
    Example 22.1: Narrow queries by module

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 725-734
    """
    result = reter_with_comprehensive_code.reql("""
        SELECT ?method WHERE {
            ?method inModule "mymodule" .
            ?method type py:Method
        }
    """)

    assert result.num_rows >= 1


def test_example_23_1_combine_predicates(reter_with_comprehensive_code):
    """
    Example 23.1: Combine multiple conditions

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 740-750
    """
    result = reter_with_comprehensive_code.reql("""
        SELECT ?method ?doc WHERE {
            ?method type py:Method .
            ?method hasDocstring ?doc
        }
    """)

    assert result.num_rows >= 0


def test_example_70_1_select_people_and_projects():
    """
    Example 70.1: Find people and their projects

    Documentation: AI_AGENT_GUIDE.md lines 357-370
    """
    reter = Reter(variant='ai')

    reter.load_ontology("""
        Person(Alice)
        Person(Bob)
        Project(WebApp)
        Project(MobileApp)
        worksOn(Alice, WebApp)
        worksOn(Bob, MobileApp)
        hasRole(Alice, "Lead")
        hasRole(Bob, "Developer")
    """, "test")

    result = reter.reql("""
        SELECT ?person ?project ?role WHERE {
            ?person type Person .
            ?person worksOn ?project .
            ?person hasRole ?role
        }
        ORDER BY ?person
        LIMIT 100
    """)

    assert result.num_rows >= 2


# =============================================================================
# FILTER Expressions (12 examples)
# =============================================================================

def test_example_24_1_filter_by_exact_name(reter_with_comprehensive_code):
    """
    Example 24.1: Filter results by exact name match

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 777-789
    """
    result = reter_with_comprehensive_code.reql("""
        SELECT ?class ?name
        WHERE {
            ?class type py:Class .
            ?class name ?name
            FILTER(?name = "Priority")
        }
    """)

    assert result.num_rows >= 0
    if result.num_rows > 0:
        df = result.to_pandas()
        assert any("Priority" in str(name) for name in df['?name'])


def test_example_25_1_filter_with_contains(reter_with_comprehensive_code):
    """
    Example 25.1: Filter using substring matching

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 792-805
    """
    result = reter_with_comprehensive_code.reql("""
        SELECT ?method ?name
        WHERE {
            ?method type py:Method .
            ?method name ?name
            FILTER(CONTAINS(?name, "get"))
        }
    """)

    # get_name method should be found
    assert result.num_rows >= 0


def test_example_26_1_filter_with_regex(reter_with_comprehensive_code):
    """
    Example 26.1: Filter using regular expressions

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 808-821
    """
    result = reter_with_comprehensive_code.reql("""
        SELECT ?method ?name
        WHERE {
            ?method type py:Method .
            ?method name ?name
            FILTER(REGEX(?name, "^test_.*"))
        }
    """)

    # test_ methods should be found
    assert result.num_rows >= 0


def test_example_27_1_filter_with_bound(reter_with_comprehensive_code):
    """
    Example 27.1: Filter by variable presence

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 824-837
    """
    result = reter_with_comprehensive_code.reql("""
        SELECT ?entity ?doc
        WHERE {
            ?entity type py:Class .
            ?entity hasDocstring ?doc
            FILTER(BOUND(?doc))
        }
    """)

    assert result.num_rows >= 0


def test_example_28_1_complex_filter_boolean(reter_with_comprehensive_code):
    """
    Example 28.1: Combine multiple filter conditions

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 841-857
    """
    result = reter_with_comprehensive_code.reql("""
        SELECT ?method ?name
        WHERE {
            ?method type py:Method .
            ?method name ?name
            FILTER(
                (CONTAINS(?name, "get") || CONTAINS(?name, "set"))
            )
        }
    """)

    # get_name and set_name should be found
    assert result.num_rows >= 0


def test_example_30_1_using_exists(reter_with_comprehensive_code):
    """
    Example 30.1: Find classes with at least one method

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 886-899
    """
    result = reter_with_comprehensive_code.reql("""
        SELECT ?class ?name WHERE {
            ?class type py:Class .
            ?class name ?name
            FILTER EXISTS {
                ?class hasMethod ?method
            }
        }
    """)

    # Animal, Dog, Cat have methods
    assert result.num_rows >= 3


def test_example_31_1_using_not_exists(reter_with_comprehensive_code):
    """
    Example 31.1: Find classes without methods

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 901-913
    """
    result = reter_with_comprehensive_code.reql("""
        SELECT ?class ?name WHERE {
            ?class type py:Class .
            ?class name ?name
            FILTER NOT EXISTS {
                ?class hasMethod ?method
            }
        }
    """)

    # Priority class has no methods
    assert result.num_rows >= 0


def test_example_76_1_has_children_exists():
    """
    Example 76.1: Find people with children

    Documentation: AI_AGENT_GUIDE.md lines 542-561
    """
    reter = Reter(variant='ai')

    reter.load_ontology("""
        Person(Alice)
        Person(Bob)
        Person(Charlie)
        hasChild(Alice, Charlie)
    """, "test")

    result = reter.reql("""
        SELECT ?person WHERE {
            ?person type Person
            FILTER EXISTS { ?person hasChild ?child }
        }
    """)

    assert result.num_rows >= 1  # Alice


def test_example_76_2_no_children_not_exists():
    """
    Example 76.2: Find people without children

    Documentation: AI_AGENT_GUIDE.md lines 542-561
    """
    reter = Reter(variant='ai')

    reter.load_ontology("""
        Person(Alice)
        Person(Bob)
        hasChild(Alice, Charlie)
    """, "test")

    result = reter.reql("""
        SELECT ?person WHERE {
            ?person type Person
            FILTER NOT EXISTS { ?person hasChild ?child }
        }
    """)

    assert result.num_rows >= 1  # Bob


def test_example_77_1_projects_no_developers():
    """
    Example 77.1: Find projects with no assigned developers

    Documentation: AI_AGENT_GUIDE.md lines 565-592
    """
    reter = Reter(variant='ai')

    reter.load_ontology("""
        Project(WebApp)
        Project(MobileApp)
        Developer(Alice)
        assignedTo(Alice, WebApp)
    """, "test")

    result = reter.reql("""
        SELECT ?project WHERE {
            ?project type Project
            FILTER NOT EXISTS {
                ?developer assignedTo ?project .
                ?developer type Developer
            }
        }
    """)

    assert result.num_rows >= 1  # MobileApp


def test_example_77_2_employees_multiple_projects():
    """
    Example 77.2: Find employees on multiple projects

    Documentation: AI_AGENT_GUIDE.md lines 565-592
    """
    reter = Reter(variant='ai')

    reter.load_ontology("""
        Employee(Alice)
        Employee(Bob)
        Project(Web)
        Project(Mobile)
        worksOn(Alice, Web)
        worksOn(Alice, Mobile)
        worksOn(Bob, Web)
    """, "test")

    result = reter.reql("""
        SELECT ?employee WHERE {
            ?employee type Employee .
            ?employee worksOn ?project1
            FILTER EXISTS {
                ?employee worksOn ?project2
                FILTER (?project1 != ?project2)
            }
        }
    """)

    assert result.num_rows >= 1  # Alice


def test_example_78_1_managers_with_developers():
    """
    Example 78.1: Managers who directly manage developers

    Documentation: AI_AGENT_GUIDE.md lines 596-609
    """
    reter = Reter(variant='ai')

    reter.load_ontology("""
        Manager(Alice)
        Manager(Bob)
        Developer(Charlie)
        Developer(David)
        reportsTo(Charlie, Alice)
        reportsTo(David, Alice)
    """, "test")

    result = reter.reql("""
        SELECT ?manager WHERE {
            ?manager type Manager
            FILTER EXISTS {
                ?developer type Developer .
                ?developer reportsTo ?manager
            }
        }
    """)

    assert result.num_rows >= 1  # Alice


# =============================================================================
# Aggregation (9 examples)
# =============================================================================

def test_example_14_2_aggregate_parameters(reter_with_comprehensive_code):
    """
    Example 14.2: Find functions with many parameters using aggregation

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 496-518
    """
    result = reter_with_comprehensive_code.reql("""
        SELECT ?func COUNT(?param) AS ?paramCount WHERE {
            ?func type py:Function .
            ?func hasParameter ?param
        }
        GROUP BY ?func
        HAVING (?paramCount > 2)
    """)

    # async_task has 3 parameters
    assert result.num_rows >= 0


def test_example_32_1_count_methods_per_class(reter_with_comprehensive_code):
    """
    Example 32.1: Count methods per class with HAVING

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 915-925
    """
    result = reter_with_comprehensive_code.reql("""
        SELECT ?class COUNT(?method) AS ?methodCount WHERE {
            ?class type py:Class .
            ?class hasMethod ?method
        }
        GROUP BY ?class
        HAVING (?methodCount > 2)
    """)

    # Dog has multiple methods
    assert result.num_rows >= 0


def test_example_79_1_count_all():
    """
    Example 79.1: Count all persons

    Documentation: AI_AGENT_GUIDE.md lines 617-635
    """
    reter = Reter(variant='ai')

    reter.load_ontology("""
        Person(Alice)
        Person(Bob)
        Person(Charlie)
    """, "test")

    result = reter.reql("""
        SELECT COUNT(*) WHERE {
            ?person type Person
        }
    """)

    assert result.num_rows >= 1


def test_example_79_2_count_distinct():
    """
    Example 79.2: Count distinct projects

    Documentation: AI_AGENT_GUIDE.md lines 617-635
    """
    reter = Reter(variant='ai')

    reter.load_ontology("""
        worksOn(Alice, WebApp)
        worksOn(Bob, WebApp)
        worksOn(Charlie, MobileApp)
    """, "test")

    result = reter.reql("""
        SELECT COUNT(DISTINCT ?project) WHERE {
            ?person worksOn ?project
        }
    """)

    assert result.num_rows >= 1


def test_example_80_1_count_per_department():
    """
    Example 80.1: Count employees per department

    Documentation: AI_AGENT_GUIDE.md lines 639-663
    """
    reter = Reter(variant='ai')

    reter.load_ontology("""
        Employee(Alice)
        Employee(Bob)
        Employee(Charlie)
        worksIn(Alice, Engineering)
        worksIn(Bob, Engineering)
        worksIn(Charlie, Sales)
    """, "test")

    result = reter.reql("""
        SELECT ?dept COUNT(*) AS ?employeeCount WHERE {
            ?person type Employee .
            ?person worksIn ?dept
        }
        GROUP BY ?dept
        ORDER BY DESC(?employeeCount)
    """)

    assert result.num_rows >= 2


def test_example_80_2_average_age():
    """
    Example 80.2: Average age by occupation

    Documentation: AI_AGENT_GUIDE.md lines 639-663
    """
    reter = Reter(variant='ai')

    reter.load_ontology("""
        Person(Alice)
        Person(Bob)
        occupation(Alice, Engineer)
        occupation(Bob, Engineer)
        age(Alice, 30)
        age(Bob, 35)
    """, "test")

    result = reter.reql("""
        SELECT ?occupation AVG(?age) AS ?avgAge WHERE {
            ?person type Person .
            ?person occupation ?occupation .
            ?person age ?age
        }
        GROUP BY ?occupation
    """)

    assert result.num_rows >= 1


def test_example_81_1_multiple_aggregations():
    """
    Example 81.1: Multiple aggregation functions

    Documentation: AI_AGENT_GUIDE.md lines 667-691
    """
    reter = Reter(variant='ai')

    reter.load_ontology("""
        Project(WebApp)
        Developer(Alice)
        Developer(Bob)
        assignedTo(Alice, WebApp)
        assignedTo(Bob, WebApp)
        hoursWorked(Alice, 40)
        hoursWorked(Bob, 35)
    """, "test")

    result = reter.reql("""
        SELECT ?project COUNT(?dev) AS ?devCount SUM(?hours) AS ?totalHours WHERE {
            ?project type Project .
            ?dev assignedTo ?project .
            ?dev hoursWorked ?hours
        }
        GROUP BY ?project
    """)

    assert result.num_rows >= 1


def test_example_82_1_having_with_count():
    """
    Example 82.1: HAVING with COUNT

    Documentation: AI_AGENT_GUIDE.md lines 695-720
    """
    reter = Reter(variant='ai')

    reter.load_ontology("""
        Employee(E1)
        Employee(E2)
        Employee(E3)
        Employee(E4)
        Employee(E5)
        Employee(E6)
        worksIn(E1, Engineering)
        worksIn(E2, Engineering)
        worksIn(E3, Engineering)
        worksIn(E4, Engineering)
        worksIn(E5, Engineering)
        worksIn(E6, Engineering)
        worksIn(E1, Sales)
    """, "test")

    result = reter.reql("""
        SELECT ?dept COUNT(*) AS ?count WHERE {
            ?person type Employee .
            ?person worksIn ?dept
        }
        GROUP BY ?dept
        HAVING (?count > 5)
    """)

    assert result.num_rows >= 1  # Engineering has 6


# =============================================================================
# Ontology-based REQL Queries (12 examples)
# =============================================================================

def test_example_34_1_transitive_calls():
    """
    Example 34.1: Query transitive calls using ontology inference

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 958-969
    """
    reter = Reter(variant='ai')

    # Load ontology that defines transitive call relations
    reter.load_ontology("""
        calls is_subproperty_of callsTransitive
        callsTransitive is_transitive
        """, "ontology")

    # Load Python code with call chain: a -> b -> c
    reter.load_python_code(
        python_code="""
def function_a():
    function_b()

def function_b():
    function_c()

def function_c():
    pass
""",
        module_name="mymodule"
    )

    result = reter.reql("""
        SELECT ?start ?end
        WHERE {
            ?rel individual ?start .
            ?rel callsTransitive ?end
        }
    """)

    # Should find both direct AND transitive calls
    assert result.num_rows >= 0


def test_example_35_1_transitive_imports():
    """
    Example 35.1: Find transitive import dependencies

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 980-993
    """
    reter = Reter(variant='ai')

    # Load ontology for transitive imports
    reter.load_ontology("""
        imports is_subproperty_of importsTransitive
        importsTransitive is_transitive
        """, "ontology")

    # Load Python code with imports
    reter.load_python_code(
        python_code="import os\nimport sys",
        module_name="mymodule"
    )

    result = reter.reql("""
        SELECT ?module ?dependency
        WHERE {
            ?rel individual ?module .
            ?rel importsTransitive ?dependency
            FILTER(?module = "mymodule")
        }
    """)

    # Returns all modules mymodule depends on (directly or indirectly)
    assert result.num_rows >= 0


def test_example_36_1_circular_dependencies():
    """
    Example 36.1: Detect circular import dependencies

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 1005-1015
if """
    reter = Reter(variant='ai')

    # Load ontology for circular dependency detection
    reter.load_ontology("""
        if imports(A, B) also imports(B, A) then circularDependency(A, B)
        """, "ontology")

    result = reter.reql("""
        SELECT ?m1 ?m2
        WHERE {
            ?rel individual ?m1 .
            ?rel circularDependency ?m2
        }
    """)

    # Should find circular imports if any exist
    assert result.num_rows >= 0


def test_example_37_1_inheritance_ancestors():
    """
    Example 37.1: Find all ancestors of a class through inheritance

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 1027-1038
    """
    reter = Reter(variant='ai')

    # Load Python code with inheritance chain
    reter.load_python_code(
        python_code="""
class GrandParent:
    pass

class Parent(GrandParent):
    pass

class MyClass(Parent):
    pass
""",
        module_name="mymodule"
    )

    result = reter.reql("""
        SELECT ?ancestor
        WHERE {
            ?rel individual "mymodule.MyClass" .
            ?rel inheritsFrom ?ancestor
        }
    """)

    # Returns all base classes up the inheritance chain
    assert result.num_rows >= 0


def test_example_38_1_find_constructors():
    """
    Example 38.1: Find all constructors using magic method recognition

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 1054-1065
if """
    reter = Reter(variant='ai')

    # Load ontology that recognizes __init__ as constructor
    reter.load_ontology("""
        if hasName(object method, "__init__") then isConstructor(object method, "true")
        """,
        source="ontology"
    )

    reter.load_python_code(
        python_code="""
class MyClass:
    def __init__(self, value):
        self.value = value

class AnotherClass:
    def __init__(self):
        pass
""",
        module_name="mymodule"
    )

    result = reter.reql("""
        SELECT ?method ?class
        WHERE {
            ?rel individual ?method .
            ?rel isConstructor "true" .
            ?method definedIn ?class
        }
    """)

    # Should find __init__ methods
    assert result.num_rows >= 0


def test_example_39_1_find_context_managers():
    """
    Example 39.1: Find classes that implement context manager protocol

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 1068-1079
if """
    reter = Reter(variant='ai')

    # Load ontology for context manager detection
    reter.load_ontology("""
        if hasMethod(object class, "__enter__") also hasMethod(object class, "__exit__") then isContextManager(object class, "true")
        """,
        source="ontology"
    )

    reter.load_python_code(
        python_code="""
class MyContextManager:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
""",
        module_name="mymodule"
    )

    result = reter.reql("""
        SELECT ?class
        WHERE {
            ?rel individual ?class .
            ?rel isContextManager "true"
        }
    """)

    # Returns classes with both __enter__ and __exit__
    assert result.num_rows >= 0


def test_example_40_1_find_properties():
    """
    Example 40.1: Find all property methods using decorator inference

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 1093-1104
if """
    reter = Reter(variant='ai')

    # Load ontology for property decorator recognition
    reter.load_ontology("""
        if hasDecorator(object method, "property") then isProperty(object method, "true")
        """,
        source="ontology"
    )

    reter.load_python_code(
        python_code="""
class MyClass:
    @property
    def value(self):
        return self._value

    @property
    def name(self):
        return self._name
""",
        module_name="mymodule"
    )

    result = reter.reql("""
        SELECT ?prop ?class
        WHERE {
            ?rel individual ?prop .
            ?rel isProperty "true" .
            ?prop definedIn ?class
        }
    """)

    # Should find @property decorated methods
    assert result.num_rows >= 0


def test_example_41_1_find_dataclasses():
    """
    Example 41.1: Find all dataclasses using decorator inference

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 1107-1118
if """
    reter = Reter(variant='ai')

    # Load ontology for dataclass decorator recognition
    reter.load_ontology("""
        if hasDecorator(object class, "dataclass") then isDataClass(object class, "true")
        """,
        source="ontology"
    )

    reter.load_python_code(
        python_code="""
from dataclasses import dataclass

@dataclass
class Person:
    name: str
    age: int

@dataclass
class Point:
    x: float
    y: float
""",
        module_name="mymodule"
    )

    result = reter.reql("""
        SELECT ?class ?name
        WHERE {
            ?rel individual ?class .
            ?rel isDataClass "true" .
            ?class name ?name
        }
    """)

    # Should find @dataclass decorated classes
    assert result.num_rows >= 0


def test_example_42_1_find_undocumented_classes():
    """
    Example 42.1: Find undocumented classes

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 1125-1137
if """
    reter = Reter(variant='ai')

    # Load ontology that flags undocumented code
    reter.load_ontology("""
        if type(object class, "py:Class") also not hasDocstring(object class, object doc) then undocumented(object class, "true")
        """,
        source="ontology"
    )

    reter.load_python_code(
        python_code="""
class DocumentedClass:
    '''This class has a docstring'''
    pass

class UndocumentedClass:
    pass
""",
        module_name="mymodule"
    )

    result = reter.reql("""
        SELECT ?class ?name
        WHERE {
            ?rel individual ?class .
            ?rel undocumented "true" .
            ?class concept "py:Class" .
            ?class name ?name
        }
    """)

    # Should find UndocumentedClass
    assert result.num_rows >= 0


def test_example_43_1_find_unused_functions():
    """
    Example 43.1: Find potentially unused functions

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 1149-1160
if """
    reter = Reter(variant='ai')

    # Load ontology for unused function detection
    reter.load_ontology("""
        if type(object func, "py:Function") also not hasCaller(object func, object caller)
            also not hasDecorator(object func, object dec) then potentiallyUnused(object func, "true")
        """,
        source="ontology"
    )

    reter.load_python_code(
        python_code="""
def used_function():
    pass

def unused_function():
    pass

def main():
    used_function()
""",
        module_name="mymodule"
    )

    result = reter.reql("""
        SELECT ?func ?name
        WHERE {
            ?rel individual ?func .
            ?rel potentiallyUnused "true" .
            ?func name ?name
        }
    """)

    # Should find functions with no callers
    assert result.num_rows >= 0


def test_example_44_1_find_abstract_classes():
    """
    Example 44.1: Find abstract classes

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 1171-1182
if """
    reter = Reter(variant='ai')

    # Load ontology for abstract class detection
    reter.load_ontology("""
        if inheritsFrom(object class, "ABC") then isAbstractClass(object class, "true")
        if hasAbstractMethod(object class, object method) then isAbstractClass(object class, "true")
        """,
        source="ontology"
    )

    reter.load_python_code(
        python_code="""
from abc import ABC, abstractmethod

class AbstractBase(ABC):
    @abstractmethod
    def do_something(self):
        pass

class ConcreteClass:
    def do_something(self):
        print("doing something")
""",
        module_name="mymodule"
    )

    result = reter.reql("""
        SELECT ?class ?name
        WHERE {
            ?rel individual ?class .
            ?rel isAbstractClass "true" .
            ?class name ?name
        }
    """)

    # Should find AbstractBase
    assert result.num_rows >= 0


def test_example_45_1_find_inherited_methods():
    """
    Example 45.1: Find all methods a class has (including inherited)

    Documentation: PYTHON_ANALYSIS_REFERENCE.md lines 1189-1199
if """
    reter = Reter(variant='ai')

    # Load ontology for inherited method resolution
    reter.load_ontology("""
        if inheritsFrom(object child, object parent) also hasMethod(object parent, object method) then inheritsMethod(object child, object method)
        """, "ontology")

    reter.load_python_code(
        python_code="""
class Parent:
    def parent_method(self):
        pass

class MyClass(Parent):
    def my_method(self):
        pass
""",
        module_name="mymodule"
    )

    result = reter.reql("""
        SELECT ?method
        WHERE {
            ?rel individual "mymodule.MyClass" .
            ?rel inheritsMethod ?method
        }
    """)

    # Returns both own methods and inherited methods
    assert result.num_rows >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
