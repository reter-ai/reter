# RETER and Ontology-Aided Software Engineering (OASE)

> **Diagrams**: Original dissertation figures are available in `books/OASE_files/`

## Theoretical Foundation

RETER implements concepts from **Ontology-Aided Software Engineering (OASE)**, a formal methodology developed by Dr. Paweł Kapłański in his 2012 PhD dissertation at Gdańsk University of Technology. OASE bridges the gap between formal methods and practical software engineering by using Description Logic (DL) as the semantic foundation and Controlled Natural Language (CNL) as the human interface.

### Computer Semiotics Context

OASE positions itself within computer semiotics, addressing four perspectives of signs:

```
                    ┌─────────────────────┐
                    │  Signs as Artifacts │ → Aesthetics, Interface Design
                    └─────────┬───────────┘
                              │
┌──────┐              ┌───────▼───────┐
│ OASE │─────────────►│ Signs as      │ → Systems Description
└──────┘              │ System        │
    │                 └───────────────┘
    │                         │
    │                 ┌───────▼───────┐
    └────────────────►│ Signs as      │ → CSCW, Work Analysis
                      │ Behaviour     │
                      └───────┬───────┘
                              │
                      ┌───────▼───────┐
                      │ Signs as      │ → Cognitive Science
                      │ Knowledge     │
                      └───────────────┘
```

### Description Logic Complexity

RETER uses **SHIQ** Description Logic, which has **ExpTime** complexity:

```
Complexity Hierarchy:
─────────────────────────────────────────────────────────
N2ExpTime │ SROIQ, SROIQBs
─────────────────────────────────────────────────────────
NExpTime  │ SHOIQ, SHOIQBs, SHIQBs, ALCB
─────────────────────────────────────────────────────────
ExpTime   │ SHIQ ← RETER, ALC, ALC(∩), ALC(¬), SHIQbs
─────────────────────────────────────────────────────────
PTime     │ DLP, EL, EL++, EL(∩), DLP(∩)
─────────────────────────────────────────────────────────
```

SHIQ supports: **S**ubsumption, **H**ierarchy, **I**nverse roles, **Q**ualified number restrictions.

### The OASE Reference Model

```
┌─────────────────────────────────────────────────────────┐
│                    OASE-English (CNL)                   │
│         Human-readable formal specifications            │
├─────────────────────────────────────────────────────────┤
│                   Description Logic                      │
│            Formal semantics & reasoning                  │
├─────────────────────────────────────────────────────────┤
│              Object-Oriented Methodology                 │
│         UML, Design Patterns, Architecture              │
├─────────────────────────────────────────────────────────┤
│               Programming Language                       │
│              Java, C#, Python, C++                      │
└─────────────────────────────────────────────────────────┘
```

### Knowledge Organization

OASE organizes software knowledge into three components:

| Component | Purpose | Examples |
|-----------|---------|----------|
| **T-Box (Terminology)** | General OO rules and concepts | Polymorphism, encapsulation, inheritance |
| **A-Box (World Description)** | Actual program entities | Classes, methods, dependencies in your code |
| **Integrity Constraints (IC)** | Requirements and rules | Design patterns, architectural constraints |

### The Meaning Triangle of Software Entities

OASE applies semiotic theory to software development. Every software entity (class, method, module) exists within a meaning triangle:

```
                Software Concept
                (Mental Model)
                     /\
                    /  \
         Symbolizes/    \Refers to
                  /      \
                 /        \
    Software Symbol -------- Software Entity
    (Code/UML Icon)  Stands for  (Virtual Object)
```

This triadic relationship means:
- **Symbols** (code identifiers, UML icons) represent concepts
- **Concepts** (mental models) refer to entities
- **Entities** (virtual objects at runtime) are denoted by symbols

### Classification of Software Ontologies

During software development, four distinct ontologies emerge:

| Ontology | Phase | Content | OASE Role |
|----------|-------|---------|-----------|
| **Requirements Ontology** | Inception | User needs, constraints | T-Box + IC |
| **Architecture Ontology** | Elaboration | High-level structure, styles | T-Box |
| **Design Ontology** | Construction | Classes, patterns, relationships | T-Box + A-Box |
| **Program Structure Ontology** | Implementation | Actual code entities | A-Box |

### The Pragmatic Software Circle

OASE fits into the cyclic software development process:

```
                    ┌──────────────┐
                    │    Design    │
                    │  (Designer)  │
                    └──────┬───────┘
                           │ Design Constraints
                           ▼
    ┌──────────────┐       ┌──────────────┐
    │  Refactoring │◄──────│ Programming  │
    │   (Tester)   │       │ (Programmer) │
    └──────┬───────┘       └──────────────┘
           │ Test Results         ▲
           └──────────────────────┘
                Working Software
```

OASE enables **bidirectional collaboration**: designers specify constraints, programmers implement code, and the OASE-Validator ensures consistency between design and implementation.

---

## RETER Implementation

RETER implements OASE concepts through its core components:

### 1. Code Extraction (A-Box Generation)

RETER automatically extracts semantic facts from source code across multiple languages:

```python
from reter import Reter

r = Reter()
r.load_python_directory("src/")      # Python
r.load_javascript_directory("web/")  # JavaScript
r.load_csharp_directory("backend/")  # C#
r.load_cpp_directory("core/")        # C++
r.load_html_directory("templates/")  # HTML
```

Each code entity becomes a fact in the A-Box:
- Classes → `instance_of(MyClass, oo:Class)`
- Methods → `instance_of(myMethod, oo:Method)`, `definedIn(myMethod, MyClass)`
- Inheritance → `inheritsFrom(Child, Parent)`
- Calls → `calls(caller, callee)`

### 2. Ontology Definition (T-Box)

RETER includes built-in ontologies for object-oriented concepts:

```
# Object-Oriented Meta-Ontology (built-in)
oo:Class is_subclass_of oo:Entity
oo:Method is_subclass_of oo:Entity
oo:Function is_subclass_of oo:Entity

# Relationships
definedIn has_domain oo:Method
definedIn has_range oo:Class
inheritsFrom has_domain oo:Class
inheritsFrom has_range oo:Class
```

### 3. Comment-Based Annotations (Integrity Constraints)

RETER supports `:::` annotations in code comments to add semantic metadata:

```python
class OrderService:
    """
    Handles order processing.

    ::: This is-in-layer Service-Layer.
    ::: This is a service.
    ::: This depends-on `services.PaymentService`.
    ::: This implements `IOrderService`.
    """

    def process_order(self, order):
        """
        ::: This is a use-case.
        ::: This is a critical-path.
        """
        pass
```

#### Annotation Types

| Type | Syntax | Description |
|------|--------|-------------|
| **Layer** | `::: This is-in-layer Service-Layer.` | Architectural layer (relation) |
| **Concept** | `::: This is a service.` | Functional role (concept assertion) |
| **Object Role** | `::: This depends-on Target.` | Relates two entities |
| **Data Role** | `::: This has-owner "Team A".` | Attaches data to entity |

#### Supported Languages

| Language | Comment Style |
|----------|---------------|
| Python | Docstrings: `"""::: ..."""` |
| JavaScript | JSDoc: `/** ::: ... */` |
| C# | XML docs: `/// ::: ...` |
| C++ | Block comments: `/* ::: ... */` |
| HTML | HTML comments: `<!-- ::: ... -->` |

---

## Architectural Layer Validation

One of the most powerful applications is enforcing architectural constraints.

### Defining Layers

Annotate your classes with architectural layer information:

```python
# presentation/controllers/user_controller.py
class UserController:
    """
    ::: This is-in-layer Presentation-Layer.
    ::: This is a controller.
    ::: This depends-on `services.UserService`.
    """

# services/user_service.py
class UserService:
    """
    ::: This is-in-layer Service-Layer.
    ::: This is a service.
    ::: This depends-on `repositories.UserRepository`.
    """

# repositories/user_repository.py
class UserRepository:
    """
    ::: This is-in-layer Infrastructure-Layer.
    ::: This is a repository.
    """
```

### Detecting Layer Violations

Query for architectural violations where Presentation layer directly accesses Data layer:

```python
# REQL query to find layer violations
violations = r.reql('''
    SELECT ?controller ?repo WHERE {
        ?controller type user:PresentationLayer .
        ?repo type user:DataAccessLayer .
        ?controller calls ?method .
        ?method definedIn ?repo
    }
''')

if violations[0].to_pylist():
    print("VIOLATION: Presentation layer directly accessing Data layer!")
    for ctrl, repo in zip(violations[0].to_pylist(), violations[1].to_pylist()):
        print(f"  {ctrl} -> {repo}")
```

### Layer Dependency Rules

Define allowed dependencies between layers:

```
┌─────────────────────┐
│  PresentationLayer  │ ──→ Can only depend on ServiceLayer
├─────────────────────┤
│    ServiceLayer     │ ──→ Can depend on DataAccessLayer, InfrastructureLayer
├─────────────────────┤
│  DataAccessLayer    │ ──→ Can depend on InfrastructureLayer
├─────────────────────┤
│ InfrastructureLayer │ ──→ No dependencies on upper layers
└─────────────────────┘
```

---

## Design Pattern Formalization

OASE allows formalizing design patterns as ontological constraints.

### Singleton Pattern

```python
class DatabaseConnection:
    """
    ::: This is a singleton.
    ::: This has-private-constructor "true".
    ::: This has-static-instance "true".
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

Validation query:
```python
# Find Singletons missing required elements
r.reql('''
    SELECT ?class WHERE {
        ?class type singleton .
        NOT EXISTS {
            ?method definedIn ?class .
            ?method name "getInstance"
        }
    }
''')
```

### Factory Pattern

```python
class VehicleFactory:
    """
    ::: This is a factory.
    ::: This creates `domain.Vehicle`.
    """

    def create_vehicle(self, type: str):
        """
        ::: This is a factory-method.
        """
        pass
```

### Observer Pattern

```python
class EventEmitter:
    """
    ::: This is a subject.
    ::: This notifies Event-Listener.
    """

class EventListener:
    """
    ::: This is a observer.
    ::: This subscribes-to Event-Emitter.
    """
```

---

## Pseudo-Modal Requirements

OASE introduces pseudo-modal expressions for requirement validation using `must`, `should`, and `can` keywords.

### Modality Levels

| Keyword | Violation Level | Description |
|---------|-----------------|-------------|
| `must` | **Error** | Critical requirement, blocks deployment |
| `should` | **Warning** | Best practice, should be addressed |
| `can` | **Info** | Optional capability or permission |

### Examples

```python
class PaymentProcessor:
    """
    ::: This must implement `IPaymentProcessor`.
    ::: This must have-method "validate".
    ::: This should have-less-than-methods 10.
    ::: This should have-docstring "true".
    ::: This can depend-on `ExternalPaymentGateway`.
    """
```

### Validation Algorithm

```
ALGORITHM ValidateConstraints(knowledge_base, constraints):
    FOR each constraint IN constraints:
        result = evaluate(constraint, knowledge_base)

        IF constraint.modality == "must" AND NOT result:
            RAISE Error(constraint.explanation)

        IF constraint.modality == "should" AND NOT result:
            LOG Warning(constraint.explanation)

        IF constraint.modality == "can" AND result:
            LOG Info("Capability used: " + constraint.description)
```

---

## OASE-English / CNL (Implemented)

RETER includes a **full implementation** of Controlled Natural Language (CNL) based on OASE-English. This allows you to write ontology statements in English-like syntax that is automatically translated to Description Logic.

### Using CNL in Python

```python
from reter import Reter

r = Reter()

# Load CNL statements directly
r.load_cnl('''
    Every cat is a mammal.
    Every mammal is an animal.
    Felix is a cat.
    Every herbivore eats nothing-but plants.
''')

# Or load from a .cnl file
r.load_cnl_file("ontology.cnl")

# Validate CNL without loading
import owl_rete_cpp
errors = owl_rete_cpp.validate_cnl("Every cat is mammal.")  # Missing 'a'
```

### Supported Sentence Patterns

| CNL Pattern | Description Logic | Example |
|-------------|-------------------|---------|
| `Every C is a D` | `C ⊑ D` | Every cat is a mammal. |
| `Something is C if-and-only-if-it is D` | `C ≡ D` | Something is a boy if-and-only-if-it is a young-male-man. |
| `No C is a D` | `C ⊑ ¬D` | No cat is a dog. |
| `Every C has R at-most N D` | `C ⊑ ≤n R.D` | Every person is-a-child-of at-most two parents. |
| `Every C has R at-least N D` | `C ⊑ ≥n R.D` | Every person is-a-child-of at-least two parents. |
| `Every C R something` | `C ⊑ ∃R.⊤` | Every cat eats something. |
| `Every C R nothing-but D` | `C ⊑ ∀R.D` | Every herbivore eats nothing-but plants. |
| `X is a C` | `C(X)` | Felix is a cat. |
| `X R Y` | `R(X,Y)` | Mary is-married-to John. |

### SWRL Rules in CNL

CNL supports full SWRL rule syntax:

```
# Simple rule with variables
If a person has-age greater-or-equal-to 18 then the person is an adult-person.

# Rule with multiple conditions
If a person(1) has-parent a person(2) and the person(2) is a female-person
then the person(1) has-mother the person(2).

# Transitivity rule
If X has-part something that has-part Y then X has-part Y.

# Rule with built-in math
If a cat has-size equal-to the value(1) and the value(1) * 2.0 = the value(2)
then the cat has-doubled-size equal-to the value(2).
```

### Naming Conventions

| Entity Type | Format | Examples |
|-------------|--------|----------|
| Instances | Capital-Case-Dashed | `John-Doe`, `Main-Controller`, `Felix` |
| Concepts | lowercase-dashed | `service`, `data-access-layer`, `mammal` |
| Roles | lowercase-dashed | `is-part-of`, `depends-on`, `has-parent` |
| Custom identifiers | `THE-"..."` | `THE-"K22 P2"`, `THE-"Order #123"` |
| Software entities | `[Namespace.Class]` | `[System.String]`, `[app.UserService]` |

### Data Types and Properties

```
# Data type declarations
Every person has-name nothing-but (some string value).
Every person has-age nothing-but (some integer value).
Every person has-birthday (some datetime value).

# Data property assertions
John has-name equal-to 'John Smith'.
John has-age equal-to 25.
John has-birthday equal-to 2000-01-15.

# Data constraints
Every cat has-name that-has-length lower-or-equal-to 10.
Every adult-person has-age greater-or-equal-to 18.
```

### Modal Expressions (must/should/can)

CNL supports pseudo-modal expressions for requirements:

```
# Critical requirements (Error if not met)
Every patient must have-age (some integer value).
Every application must have-status a thing that is either Operable or Inoperable.

# Best practices (Warning if not met)
Every service should have-documentation (some string value).

# Capabilities (Info when used)
Every patient can have-medical-history (some string value).

# Prohibitions
Every patient can-not have-age greater-than 200.
```

### Built-in Functions

CNL includes SWRL built-ins for math, strings, and dates:

```
# Math operations
If a cat has-size equal-to the value(1) and the value(1) + 10 = the value(2)
then the cat has-new-size equal-to the value(2).

# String operations
If a cat has-name equal-to the value(1) and upper-cased the value(1) = the value(2)
then the cat has-upper-name equal-to the value(2).

# Duration
If a cat has-age equal-to the value(1) and 365 days 0 hours 0 minutes 0 seconds = the value(2)
then the cat has-age-in-duration equal-to the value(2).
```

### Complete Example

```python
from reter import Reter

r = Reter()

# Define an architectural ontology in CNL
r.load_cnl('''
    # Layer hierarchy
    Every presentation-layer is a layer.
    Every service-layer is a layer.
    Every data-access-layer is a layer.

    # Layer constraints
    Every presentation-layer depends-on nothing-but service-layer.
    Every service-layer depends-on nothing-but data-access-layer.
    No data-access-layer depends-on a presentation-layer.

    # Component classifications
    User-Controller is a presentation-layer.
    User-Service is a service-layer.
    User-Repository is a data-access-layer.

    # Dependencies
    User-Controller depends-on User-Service.
    User-Service depends-on User-Repository.

    # Rules for violation detection
    If a presentation-layer depends-on a data-access-layer
    then the presentation-layer is a layer-violator.
''')

# Query for violations
violators = r.pattern(('?x', 'type', 'user:layer-violator'))
```

---

## OASE-Assertions (Runtime Debugging)

While OASE-Annotations validate design-time constraints, **OASE-Assertions** validate runtime contracts using CNL. This implements the Design by Contract paradigm.

### Python Implementation

```python
class PaymentProcessor:
    """
    ::: This is-in-layer Service-Layer.
    ::: This is a service.
    ::: This handles `payments.Transaction`.
    """

    def process_payment(self, transaction, amount):
        """
        ::: This is a critical-path.

        Pre-condition assertions (checked at runtime in debug mode):
        ::: transaction must have-status equal-to 'pending'.
        ::: amount must be greater-than 0.

        Post-condition:
        ::: transaction must have-status equal-to 'completed'.
        """
        # Validate pre-conditions
        r = Reter()
        r.load_cnl(f"Transaction-{transaction.id} has-status equal-to '{transaction.status}'.")
        r.load_cnl(f"Transaction-{transaction.id} has-amount equal-to {amount}.")

        # Check assertion
        if not r.check_cnl(f"Transaction-{transaction.id} must have-status equal-to 'pending'."):
            raise AssertionError("Pre-condition failed: transaction must be pending")

        # ... process payment ...

        transaction.status = 'completed'
```

### Pipes & Filters Pattern with Assertions

The dissertation shows how OASE-Assertions validate filter compatibility at runtime:

```python
class Filter:
    """
    ::: This is a pipes-and-filters.
    ::: This has-input-pipe Pipe-A.
    ::: This has-output-pipe Pipe-B.
    """

    def process(self, input_stream):
        """
        ::: input_stream must be-connectable-to Pipe-A.
        """
        # Runtime validation of pipe compatibility
        pass

# CNL axiom defining pipe compatibility
r.load_cnl("Pipe-A is-connectable-to Pipe-B.")
r.load_cnl("Pipe-B is-connectable-to Pipe-C.")
```

---

## The OASE Meta-Model

The dissertation defines a formal meta-model for object-oriented structures in Description Logic.

### Core Relationships

```
# Class instantiation
be-instance-of: Object → Class
{Object-Pawel} ⊑ ∃be-instance-of.{Class-Client}

# Inheritance (partial ordering)
be-subclass-of: Class → Class  (transitive)
If X is-subclass-of something that is-subclass-of Y then X is-subclass-of Y.

# Type inference
If X is-instance-of Y then Y is-type-of X.
If X is-instance-of something that is-subclass-of Y then Y is-type-of X.

# Part-whole relationships
be-member-of: Part → Whole
If X has-member-that-is Y then X is-part-of Y.
If X has-member-that-is something that is-part-of Y then X is-part-of Y.

# Method calls (transitive)
If X calls something that calls Y then X calls Y.
If X creates something that is-constructed-by Y then X calls Y.
```

### Type Inference Chain

The `be-type-of` relationship is inferred through the subclass chain:

```
  ○─────────────────────be-subclass-of─────────────────────○
  │                           │                            │
  │    be-subclass-of         │       be-subclass-of       │
  ▼         │                 ▼              │             ▼
  ●─────────┴────►●───────────┴─────────►●───┴────────────►●
  ▲               ▲                       ▲
  │               │                       │
  │ be-instance-of│                       │
  │               │                       │
  ○───────────────┘                       │
  │                                       │
  └─────────────be-type-of (inferred)─────┘

  Solid lines (─): Explicit relations
  Dashed concept: Inferred relations (be-type-of propagates through subclass chain)
```

This means if `obj` is-instance-of `ClassA` and `ClassA` is-subclass-of `ClassB`, then `ClassB` is-type-of `obj` (inferred).

### Class Hierarchies

OASE introduces the `hierarchize` relationship to group related classes:

```python
r.load_cnl('''
    # Define class hierarchy
    Hierarchy-Animals hierarchizes Class-Animal.
    Class-Cat is-subclass-of Class-Animal.
    Class-Dog is-subclass-of Class-Animal.

    # Propagation rule
    If X hierarchizes something that is-subclass-of Y then X hierarchizes Y.

    # Query: all classes in the Animal hierarchy
    Every hC is equivalent to something that is
        hierarchized by something that hierarchizes Class-Animal.
''')
```

### Abstract and Final Classes

```python
r.load_cnl('''
    # Abstract class (cannot be instantiated)
    Class-Animal has-instance-that-is nothing.
    Class-Animal is-subclass-of nothing.  # Root of hierarchy

    # Final class (cannot be inherited)
    Class-Bulldog is-superclass-of nothing.
''')
```

---

## Advanced Design Pattern Formalization

### Adapter Pattern

The dissertation provides a complete OASE formalization of the Adapter pattern:

```python
r.load_cnl('''
    # Adapter pattern structure
    Every adapter is a target.
    Every adapter adapts exactly one adaptee.

    # Class-adapter (via inheritance)
    Every class-adapter is-subclass-of something that is an adaptee.

    # Object-adapter (via aggregation)
    Every object-adapter has-member-that-is exactly one adaptee.

    # Request delegation
    If an adapter has-method something that calls something that
        is-specific-request-of an adaptee
    then the adapter adapts the adaptee.
''')

# Validate adapter implementation
r.load_cnl('''
    # Concrete adapter
    Class-JsonToXmlAdapter is an adapter.
    Class-JsonToXmlAdapter adapts Class-JsonParser.

    # Validation: adapter must delegate to adaptee
    Class-JsonToXmlAdapter must have-method something that
        calls something that is-defined-in Class-JsonParser.
''')
```

### Strategy Pattern

```python
r.load_cnl('''
    # Strategy pattern
    Every context has-strategy exactly one strategy.
    Every concrete-strategy is a strategy.

    # Strategies are interchangeable
    If X is a strategy and Y is a strategy then X is-equivalent-to Y.

    # Context delegates to strategy
    If a context has-strategy a strategy then
        the context delegates-to the strategy.
''')
```

### Observer Pattern

```python
r.load_cnl('''
    # Observer pattern
    Every subject notifies at-least one observer.
    Every observer subscribes-to exactly one subject.

    # Notification chain
    If a subject has-state-changed equal-to true
    then the subject notifies every observer that subscribes-to the subject.

    # Loose coupling
    No subject depends-on an observer.
''')
```

---

## Inferred-UI Pattern

One of the innovative applications from the dissertation is **Inferred-UI**: automatically generating user interfaces from ontologies using reasoning services.

### Concept

```
┌─────────────────────────────────────────────────────────┐
│                    Knowledge Base                        │
│              (T-Box + A-Box + IC)                       │
├─────────────────────────────────────────────────────────┤
│                      Reasoner                            │
│           (Infers taxonomy, validates IC)               │
├─────────────────────────────────────────────────────────┤
│                    MVC Generator                         │
│   (Generates UI controls from inferred concepts)        │
├─────────────────────────────────────────────────────────┤
│                Generated Application                     │
│        (View + Controller + Model binding)              │
└─────────────────────────────────────────────────────────┘
```

### Algorithm

1. Traverse the inferred ontology from top concept
2. For each concept subsumption → generate Panel control
3. For each instance with relationships → generate Combo Box
4. For data properties → generate Text Box
5. Controller updates A-Box; View reflects inferred knowledge

### RETER Implementation Idea

```python
def generate_ui_from_ontology(reter_instance):
    """Generate UI components from RETER knowledge base."""

    # Get all concepts
    concepts = reter_instance.reql('''
        SELECT ?concept WHERE {
            ?concept type owl:Class
        }
    ''')

    for concept in concepts:
        # Get concept hierarchy
        parents = reter_instance.reql(f'''
            SELECT ?parent WHERE {{
                {concept} subClassOf ?parent
            }}
        ''')

        # Get instances
        instances = reter_instance.reql(f'''
            SELECT ?instance WHERE {{
                ?instance type {concept}
            }}
        ''')

        # Generate UI component based on structure
        yield UIComponent(
            type='panel' if parents else 'root',
            concept=concept,
            instances=instances
        )
```

---

## Self-Implemented Requirement

The dissertation introduces **Self-Implemented Requirement**: allowing end-users to modify system requirements at runtime using CNL.

### Concept

Traditional requirement changes require:
1. User → Requirement Engineer → Designer → Programmer → Tester

With Self-Implemented Requirement:
1. User directly modifies T-Box via CNL interface
2. System adapts automatically through reasoning

### Use Case: Business Rules

```python
# User interface allows business users to enter rules in CNL
user_rule = "Every order that has-value greater-than 1000 must be-approved-by a manager."

# System validates and applies the rule
r = Reter()
r.load_cnl(user_rule)

# Check if existing orders violate the new rule
violations = r.reql('''
    SELECT ?order WHERE {
        ?order type Order .
        ?order hasValue ?value .
        FILTER(?value > 1000)
        NOT EXISTS { ?order approvedBy ?manager . ?manager type Manager }
    }
''')

if violations:
    notify_users("New rule requires manager approval for these orders")
```

### Clinical Decision Support System Example

The dissertation demonstrates this pattern in a medical CDSS:

```python
# Medical professional enters diagnostic rule
r.load_cnl('''
    If a patient has-symptom fever and
       the patient has-symptom cough and
       the patient has-symptom shortness-of-breath
    then the patient is-suspected-of respiratory-infection.

    Every patient that is-suspected-of respiratory-infection
        should have-test chest-xray.
''')

# System automatically infers diagnoses and recommends tests
suspected = r.reql('''
    SELECT ?patient WHERE {
        ?patient type user:respiratory-infection
    }
''')
```

---

## OASE-Transformations

The dissertation introduces **OASE-Transformations**: template-based mappings from class descriptors to OASE-English scripts using StringTemplate.

### Class Descriptors

A class descriptor is a part-whole structure representing a class:

```
ClassDescriptor:
├── className: "Manager"
├── baseClasses: ["Employee", "Human"]
├── fields:
│   └── position: {name: "position", type: "Position"}
├── methods:
│   └── approve: {name: "approve", returnType: "bool", params: [...]}
└── constructors: [...]
```

### Direct-Mapping vs OASE-Mapping

The dissertation presents two approaches:

| Approach | Mapping | Use Case |
|----------|---------|----------|
| **Direct-Mapping** | class→concept, object→instance | Simple type checking |
| **OASE-Mapping** | pattern→concept, class→instance, object→instance | Full pattern reasoning |

### StringTemplate Transformation Example

```python
# OASE-Transformation for class to CNL
def transform_class(cls):
    """Transform class descriptor to CNL."""
    cnl = []

    # Class declaration
    cnl.append(f"[{cls.name}] is a class.")

    # Inheritance
    for base in cls.bases:
        cnl.append(f"[{cls.name}] is-subtype-of [{base}].")

    # Fields
    for field in cls.fields:
        cnl.append(f"[{cls.name}.{field.name}] is an attribute.")
        cnl.append(f"[{cls.name}.{field.name}] is-member-of [{cls.name}].")
        cnl.append(f"Everything (that fills [{cls.name}.{field.name}]) "
                   f"has-type-that-is [{field.type}].")

    # Methods
    for method in cls.methods:
        cnl.append(f"[{cls.name}.{method.name}] is a method.")
        cnl.append(f"[{cls.name}.{method.name}] is-member-of [{cls.name}].")

    return "\n".join(cnl)
```

---

## OASE-Tools Architecture

The dissertation describes a complete toolchain for OASE:

### Tool Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     T-Box Engineers                              │
│         (Designers, Requirement Engineers)                       │
│                          │                                       │
│              ┌───────────▼───────────┐                          │
│              │  OASE-English Editor  │                          │
│              │  (Predictive Editor)  │                          │
│              └───────────┬───────────┘                          │
│                          │                                       │
├──────────────────────────┼──────────────────────────────────────┤
│                          │                                       │
│              ┌───────────▼───────────┐                          │
│              │    OASE-Validator     │◄─────┐                   │
│              │   (DL Reasoner +      │      │                   │
│              │    Explainer)         │      │                   │
│              └───────────┬───────────┘      │                   │
│                          │                  │                   │
├──────────────────────────┼──────────────────┼───────────────────┤
│                          │                  │                   │
│  ┌───────────────────────▼──────────────────┴────────┐          │
│  │            OASE-Transformation Processor           │          │
│  │     (StringTemplate → OASE-English Scripts)        │          │
│  └───────────────────────┬───────────────────────────┘          │
│                          │                                       │
│              ┌───────────▼───────────┐                          │
│              │     A-Box Producers   │                          │
│              │     (Programmers)     │                          │
│              └───────────────────────┘                          │
│                                                                  │
│  Tools: OASE-Annotator (IDE Plugin), OASE-Diagrammer (UML)      │
└─────────────────────────────────────────────────────────────────┘
```

### OASE-Validator Components

```python
# OASE-Validator internal structure
class OASEValidator:
    """
    Components:
    1. Lexer - tokenizes OASE-English sentences
    2. Parser - produces AST from tokens
    3. Morphology - handles English verb forms
    4. AST Visitor - transforms AST to DL
    5. Reasoner - SHIQ DL reasoning
    6. Explainer - generates explanations
    7. IC Validator - checks integrity constraints
    """

    def validate(self, world_description, instance_knowledge, integrity_constraints):
        # Tell reasoner about world description
        self.reasoner.load(world_description)
        self.reasoner.load(instance_knowledge)

        # Check consistency
        if not self.reasoner.is_consistent():
            return ValidationResult(status="inconsistency")

        # Check integrity constraints
        for ic in integrity_constraints:
            for instance in ic.left_hand_side:
                if instance not in ic.right_hand_side:
                    severity = ic.modality  # error or warning
                    explanation = self.explainer.explain(ic, instance)
                    yield ValidationResult(severity, explanation)
```

### Predictive Editor

The LALR(1) grammar of OASE-English enables predictive editing:

```python
# Predictive completion example
def get_completions(partial_sentence):
    """
    Given: "Every cat is a "
    Returns: ['mammal', 'animal', 'thing', 'something', ...]

    The LALR(1) grammar determines valid next tokens.
    """
    parser_state = parse_partial(partial_sentence)
    valid_tokens = get_valid_continuations(parser_state)

    # Filter by ontology context
    if expecting_concept():
        return [c for c in ontology.concepts if c.startswith(prefix)]
    elif expecting_role():
        return [r for r in ontology.roles if r.startswith(prefix)]
    elif expecting_instance():
        return [i for i in ontology.instances if i.startswith(prefix)]
```

---

## OASE as Design Pattern Language

The dissertation formalizes design patterns as OASE specifications, enabling automated validation.

### Pattern Formalization Structure

Every design pattern specification includes:
1. **Participating classes** - The roles (adapter, target, adaptee, client)
2. **Relationships** - How classes connect
3. **Collaboration rules** - How methods should delegate

### Complete Adapter Pattern Specification

```python
r.load_cnl('''
    # === STRUCTURAL CONSTRAINTS ===

    # Adapter must be subtype of target
    Every adapter must be-subtype-of a target.

    # Adapter must reference exactly one adaptee
    Every adapter has-member-that-is exactly one adaptee.

    # === BEHAVIORAL CONSTRAINTS ===

    # Adapter request methods must delegate to adaptee
    Every adapter-request must call something that implements
        an adaptee-specific-request.

    # Client operations should call target requests
    Every client-operation should call something that implements
        a target-request.

    # === ROLE ASSIGNMENTS (per pattern instance) ===

    # Pattern: JsonToXml-Adapter-1
    [JsonToXmlAdapter] is an adapter.
    [IXmlWriter] is a target.
    [JsonParser] is an adaptee.
    [XmlConsumer] is an adapter-client.

    # Method role assignments
    [JsonToXmlAdapter.write] is an adapter-request.
    [JsonParser.parse] is an adaptee-specific-request.
    [IXmlWriter.write] is a target-request.
    [XmlConsumer.process] is a client-operation.
''')

# Validate the implementation
violations = r.validate_constraints()
for v in violations:
    print(f"{v.severity}: {v.explanation}")
```

### Factory Pattern Specification

```python
r.load_cnl('''
    # Factory pattern structure
    Every factory creates at-least one product.
    Every concrete-factory is a factory.
    Every concrete-product is a product.

    # Factory methods
    Every factory-method is-member-of a factory.
    Every factory-method returns something that is a product.

    # Concrete factories create concrete products
    If a concrete-factory has-method a factory-method
    then the factory-method creates a concrete-product.

    # Client uses factory, not concrete products directly
    Every client uses a factory.
    No client creates a concrete-product.
''')
```

### Singleton Pattern Specification

```python
r.load_cnl('''
    # Singleton constraints
    Every singleton has-instance-that-is at-most one thing.
    Every singleton has-constructor-that-is a private-constructor.

    # Static accessor
    Every singleton has-method something that is a get-instance-method.
    Every get-instance-method is a static-method.
    Every get-instance-method returns the singleton.

    # Validate: DatabaseConnection is singleton
    [DatabaseConnection] is a singleton.
    [DatabaseConnection] must have-constructor-that-is a private-constructor.
    [DatabaseConnection.getInstance] must be a get-instance-method.
''')
```

---

## Modal Expression Semantics

The dissertation clarifies the precise semantics of pseudo-modal expressions:

### Truth Table

| Expression | Semantics | Validation |
|------------|-----------|------------|
| `A is B` | All A instances are B instances | Inconsistency if violated |
| `A must be B` | All A should be B | **Error** if any A is not B |
| `A should be B` | All A ideally are B | **Warning** if any A is not B |
| `A can be B` | Some A may be B | **Warning** if no A is B |
| `A cannot be B` | No A should be B | **Error** if any A is B |
| `A should not be B` | A ideally not B | **Warning** if any A is B |
| `A must not be B` | A required not B | **Warning** if no A is not B |

### Validation Algorithm

```python
def validate_modal(kb, constraint):
    """
    Validate a pseudo-modal constraint against knowledge base.

    Args:
        kb: Knowledge base with A-Box and T-Box
        constraint: Modal expression to validate

    Returns:
        List of validation results
    """
    lhs_instances = kb.query(constraint.left_hand_side)
    rhs_instances = kb.query(constraint.right_hand_side)

    results = []
    for instance in lhs_instances:
        in_rhs = instance in rhs_instances

        if constraint.modality == "must" and not in_rhs:
            results.append(Error(instance, constraint))
        elif constraint.modality == "should" and not in_rhs:
            results.append(Warning(instance, constraint))
        elif constraint.modality == "can" and not in_rhs:
            # Only warn if NO instances satisfy
            pass
        elif constraint.modality == "cannot" and in_rhs:
            results.append(Error(instance, constraint))
        elif constraint.modality == "should not" and in_rhs:
            results.append(Warning(instance, constraint))

    return results
```

### Programmer Ambiguity Note

The dissertation survey found that programmers often confuse `is` (factual assertion) with `must` (requirement). When annotating code:

- Use `is` for describing current structure: `[UserService] is a service.`
- Use `must` for design requirements: `[UserService] must have-tests.`
- Use `should` for best practices: `[UserService] should have-documentation.`

---

## Practical Use Cases

### 1. Onboarding New Developers

Query the codebase architecture:
```python
# What are the main architectural layers?
layers = r.reql('''
    SELECT ?layer (COUNT(?class) AS ?count) WHERE {
        ?class type ?layer .
        FILTER(CONTAINS(?layer, "Layer"))
    }
    GROUP BY ?layer
''')

# What does each service depend on?
deps = r.reql('''
    SELECT ?service ?dependency WHERE {
        ?service type user:ServiceLayer .
        ?service dependsOn ?dependency
    }
''')
```

### 2. Code Review Automation

```python
def review_pull_request(changed_files):
    r = Reter()
    for file in changed_files:
        r.load_python_file(file)

    # Check for layer violations
    violations = r.reql('''
        SELECT ?source ?target WHERE {
            ?source type user:PresentationLayer .
            ?target type user:DataAccessLayer .
            ?source dependsOn ?target
        }
    ''')

    if violations:
        return "BLOCKED: Architectural violation detected"

    # Check for missing annotations on new classes
    unannotated = r.reql('''
        SELECT ?class WHERE {
            ?class type oo:Class .
            NOT EXISTS { ?class type ?layer . FILTER(CONTAINS(?layer, "Layer")) }
        }
    ''')

    if unannotated:
        return "WARNING: New classes missing layer annotations"

    return "APPROVED"
```

### 3. Documentation Generation

```python
# Generate architecture documentation from annotations
arch = r.reql('''
    SELECT ?class ?layer ?deps WHERE {
        ?class type ?layer .
        FILTER(CONTAINS(?layer, "Layer"))
        OPTIONAL { ?class dependsOn ?deps }
    }
''')

# Output as Mermaid diagram
print("```mermaid")
print("graph TD")
for cls, layer, dep in arch:
    print(f"    {cls} --> {dep}")
print("```")
```

### 4. Technical Debt Detection

```python
# Find God Classes (too many methods)
god_classes = r.reql('''
    SELECT ?class (COUNT(?method) AS ?count) WHERE {
        ?class type oo:Class .
        ?method definedIn ?class
    }
    GROUP BY ?class
    HAVING (?count > 20)
''')

# Find circular dependencies
circular = r.reql('''
    SELECT ?a ?b WHERE {
        ?a dependsOn ?b .
        ?b dependsOn ?a
    }
''')
```

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Architecture Validation

on: [pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install RETER
        run: pip install reter reter-core

      - name: Validate Architecture
        run: |
          python -c "
          from reter import Reter
          r = Reter()
          r.load_python_directory('src/')

          # Check layer violations
          violations = r.reql('''
              SELECT ?source ?target WHERE {
                  ?source type user:PresentationLayer .
                  ?target type user:DataAccessLayer .
                  ?source calls ?method .
                  ?method definedIn ?target
              }
          ''')

          if violations[0].to_pylist():
              print('Architecture violations found!')
              exit(1)
          "
```

---

## Already Implemented Features

The following OASE-inspired features are already available in RETER:

| Feature | Status | API |
|---------|--------|-----|
| CNL/OASE-English Parser | ✅ Implemented | `r.load_cnl()`, `r.load_cnl_file()` |
| SWRL Rules in CNL | ✅ Implemented | `If...then...` syntax in CNL |
| Modal Expressions | ✅ Implemented | `must`, `should`, `can` keywords |
| Natural Language Queries | ✅ Implemented | `natural_language_query()` MCP tool |
| Hybrid Query Routing | ✅ Implemented | `hybrid_query()` MCP tool |
| Code Smell Detection | ✅ Implemented | `recommender("refactoring")` MCP tool |
| Semantic Code Search | ✅ Implemented | `semantic_search()` MCP tool |
| UML Diagram Generation | ✅ Implemented | `diagram()` MCP tool |
| Multi-language Support | ✅ Implemented | Python, JS, C#, C++, HTML |
| Comment Annotations | ✅ Implemented | `:::` in docstrings/comments |
| A-Box Extraction | ✅ Implemented | `load_python_file()`, etc. |
| T-Box Definition | ✅ Implemented | Built-in OO ontology |
| RETE Algorithm | ✅ Implemented | C++ RETE network in reter_core |
| Reasoning Tasks | ✅ Implemented | Subsumption, classification, satisfiability |

### OASE Semiotic Framework Mapping

| OASE Layer | Description | RETER Implementation |
|------------|-------------|----------------------|
| **Syntax** | Symbols and their structure | ANTLR4 CNL parser, CADSL grammar |
| **Semantics** | Formal meaning in DL | SHIQ Description Logic reasoner |
| **Pragmatics** | Practical usage by stakeholders | MCP tools, IDE integration, CI/CD |

---

## Future Extensions

### 1. Real-time IDE Integration

- VSCode/JetBrains extension with live annotation suggestions
- Inline layer violation warnings as you type
- Auto-complete for `:::` annotations
- Quick-fix suggestions for detected violations

### 2. CNL-based Constraint Validation

Extend modal expressions (`must`/`should`/`can`) with automatic validation:

```python
# Define constraints in CNL
r.load_cnl('''
    Every service must have-tests (some value).
    Every controller should have-less-than 10 methods.
    Every entity can-not depend-on a controller.
''')

# Validate codebase against constraints
violations = r.validate_constraints()
for v in violations:
    print(f"{v.severity}: {v.entity} - {v.message}")
```

### 3. Automatic Refactoring Suggestions

Based on detected patterns and violations, suggest refactorings:
- Extract interface when multiple implementations exist
- Split God Class into smaller services
- Introduce facade when too many dependencies

### 4. Design Pattern Code Generation

```python
# Generate Singleton boilerplate from CNL
r.load_cnl("Database-Connection is a singleton.")

# RETER generates:
# - Private constructor
# - Static instance field
# - getInstance() method
generated_code = r.generate_pattern_code("Database-Connection")
```

### 5. CNL-to-REQL Compiler

Direct translation from CNL queries to REQL:

```python
# Query in CNL
result = r.query_cnl("Every class that is a service and has more-than 10 methods?")

# Automatically compiled to REQL and executed
```

### 6. OASE-Assertions Runtime Validator

Implement runtime contract checking:

```python
@reter.assert_pre("order must have-status equal-to 'pending'")
@reter.assert_post("order must have-status equal-to 'completed'")
def process_order(order):
    # Pre-condition checked automatically before execution
    # Post-condition checked automatically after execution
    pass
```

### 7. Inferred-UI Generator

Generate UI components from ontology structure (from dissertation):

```python
# Given an ontology, generate a CRUD interface
ui = reter.generate_ui(
    ontology_file="domain.cnl",
    framework="react"  # or "vue", "angular"
)
```

### 8. Self-Implemented Requirement Editor

Allow non-technical users to modify business rules:

```python
# CNL-based rule editor for business users
rule_editor = reter.RuleEditor(
    ontology=r,
    allowed_concepts=["order", "customer", "approval"],
    allowed_predicates=["must", "should", "can"]
)
# User can enter: "Every order that has-value greater-than 5000 must be-approved-by director."
```

### 9. Explanation Generation

Generate natural language explanations for reasoning results (from dissertation):

```python
# Why is this class considered a layer violator?
explanation = r.explain("Why is Class-UserController a layer-violator?")
# Returns: "Class-UserController is a layer-violator because:
#          1. It is marked as PresentationLayer
#          2. It depends-on Class-UserRepository
#          3. Class-UserRepository is marked as DataAccessLayer
#          4. According to rule: 'Every PresentationLayer can-not depend-on DataAccessLayer'"
```

### 10. Knowledge Cartography

Implement polynomial-time reasoning using binary descriptor matching (from dissertation):

```python
# For very large codebases, use Knowledge Cartography approach
r.set_reasoning_mode("cartography")  # Instead of full DL reasoning
# Uses binary string matching for efficient subsumption checking
```

---

## References

1. Kapłański, P. (2012). *Ontology-Aided Software Engineering*. PhD Dissertation, Gdańsk University of Technology. [www.oase-tools.net](http://www.oase-tools.net)

2. Baader, F., et al. (2003). *The Description Logic Handbook*. Cambridge University Press.

3. Alexander, C. (1977). *A Pattern Language*. Oxford University Press.

4. Gamma, E., et al. (1994). *Design Patterns: Elements of Reusable Object-Oriented Software*. Addison-Wesley.

5. Buschmann, F., et al. (1996). *Pattern-Oriented Software Architecture Volume 1*. Wiley.

6. Sowa, J.F. (2000). *Knowledge Representation: Logical, Philosophical, and Computational Foundations*. Brooks/Cole.

7. Horrocks, I., et al. (2006). *The Even More Irresistible SROIQ*. KR 2006.

8. Ogden, C.K. & Richards, I.A. (1923). *The Meaning of Meaning*. Routledge & Kegan Paul.

9. Andersen, P.B. (1990). *A Theory of Computer Semiotics*. Cambridge University Press.

---

## Dissertation Figures Reference

Key figures from `books/OASE_files/`:

| Figure | File | Description |
|--------|------|-------------|
| Fig. 3 | `image008.png` | OASE workflow: Designer ↔ Computer ↔ Programmer |
| Fig. 10 | `image010.png` | Ogden-Richards Meaning Triangle |
| Fig. 15 | `image015.png` | Description Logic complexity hierarchy |
| Fig. 20 | `image020.png` | OASE in computer semiotics context |
| Fig. 27 | `image027.png` | UML diagram types mapped to formal languages |
| Fig. 33 | `image033.png` | Class Descriptor structure (full UML) |
| Fig. 37 | `image037.png` | Type inference through subclass chain |
| Fig. 39 | `image039.png` | Class hierarchy with abstract/final constraints |
| Fig. 42 | `image042.png` | Pipes & Filters pattern diagram |
| Fig. 44 | `image044.png` | OASE-Validator internal architecture |
| Fig. 45 | `image045.png` | OASE-English Predictor reusability |
| Fig. 50 | `image050.png` | MVC architectural pattern |
| Fig. 52 | `image052.png` | Inferred-UI: Ontology → Generated UI |

---

## Quick Reference

### Annotation Cheat Sheet

```python
# Layer Classification (relations - Title-Case layer names)
::: This is-in-layer Presentation-Layer.
::: This is-in-layer Service-Layer.
::: This is-in-layer Infrastructure-Layer.
::: This is-in-layer Core-Layer.
::: This is-in-layer Utility-Layer.

# Component Types (concept assertions - lowercase)
::: This is a controller.
::: This is a service.
::: This is a repository.
::: This is a factory.
::: This is a singleton.

# Relationships (relations)
::: This depends-on `other.Service`.
::: This implements `IInterface`.
::: This is-part-of `module.name`.
::: This calls `other.method`.

# Data Properties
::: This has-owner "Team A".
::: This has-version "1.0.0".
::: This has-priority "high".

# Requirements (Future)
::: This must implement `IDisposable`.
::: This should have-less-than-methods 10.
```

### Common Queries

```python
# All classes in a layer
r.pattern(('?class', 'type', 'user:ServiceLayer'))

# All dependencies
r.pattern(('?source', 'dependsOn', '?target'))

# Classes implementing an interface
r.reql('SELECT ?class WHERE { ?class implements ?interface }')

# Method call graph
r.reql('SELECT ?caller ?callee WHERE { ?caller calls ?callee }')
```

### CNL Quick Reference

```
# Subsumption (concept hierarchy)
Every cat is a mammal.
Every mammal is an animal.

# Equivalence
Something is a boy if-and-only-if-it is a young-male-man.

# Disjoint concepts
No cat is a dog.
Every herbivore is not a carnivore.

# Cardinality restrictions
Every person is-a-child-of at-most two parents.
Every person has-name at-most one (some string value).

# Existential restriction
Every cat eats something.
Every branch is-part-of a tree.

# Universal restriction
Every herbivore eats nothing-but plants.
Every lion eats nothing-but herbivore.

# Instance assertions
Felix is a cat.
John is a person.

# Role assertions
Mary is-married-to John.
Felix is-owned-by John.

# Data properties
John has-name equal-to 'John Smith'.
John has-age equal-to 25.

# SWRL rules
If a person has-age greater-or-equal-to 18 then the person is an adult-person.
If X has-part something that has-part Y then X has-part Y.

# Modal expressions
Every service must have-documentation (some string value).
Every controller should have-less-than 10 methods.
Every patient can have-medical-history (some string value).
```

---

## OASEMapping.stg and RETER Extractors Comparison

This section analyzes how the original OASE transformation template (`OASEMapping.stg`) relates to RETER's current fact extraction system.

### OASEMapping.stg Overview

The `OASEMapping.stg` file (from Dr. Kapłański's OASE-Tools) is a StringTemplate file that transforms **Class Descriptors** (structured objects representing parsed classes) into OASE-English CNL assertions. It contains:

1. **`global()` template** - Base axioms for transitivity, type inference, and relationship semantics
2. **`mapType(class)` template** - Transforms a class descriptor into CNL assertions

### Class Descriptor Model (OASEMapping.stg expects)

```
ClassDescriptor {
    className: string                    // "MyClass"
    baseFullNames: string[]              // ["BaseClass", "IInterface"]
    isAbstract: boolean
    isFinal: boolean

    fields: FieldDescriptor[] {
        name: string                     // "myField"
        typeDesc: TypeDescriptor {
            className: string            // "List"
            setElementTypeFullName: string  // "Item" (for collections)
        }
    }

    constructors: ConstructorDescriptor[] {
        calls: CallDescriptor[]          // {typeDesc.className, name}
        creates: CreateDescriptor[]      // {className}
        gets: AccessDescriptor[]         // {typeDesc.className, name}
        sets: AccessDescriptor[]         // {typeDesc.className, name}
    }

    methods: MethodDescriptor[] {
        name: string
        returnTypeDesc: TypeDescriptor
        parameters: TypeDescriptor[]
        calls: CallDescriptor[]
        creates: CreateDescriptor[]
        gets: AccessDescriptor[]
        sets: AccessDescriptor[]
    }
}
```

### RETER Fact Extraction Model

RETER extractors produce **flat RDF-style facts** (subject-predicate-object triples):

```
Fact {
    subject: string      // Entity ID: "Namespace.ClassName"
    predicate: string    // Property: "type", "hasName", "definedIn", "calls"
    object: string       // Value: "cs:Class", "MyClass", etc.
    attributes: map      // Additional metadata: inFile, atLine, etc.
}
```

### Mapping Comparison Table

| OASE Class Descriptor | RETER Fact Pattern | Notes |
|----------------------|-------------------|-------|
| `class.className` | `(?class, type, cs:Class)` + `(?class, hasName, "Name")` | RETER uses qualified ID as subject |
| `class.baseFullNames` | `(?class, extends, ?baseClass)` | Created in `visitClass_base()` |
| `class.isAbstract` | `(?class, isAbstract, "true")` | Attribute on class fact |
| `class.isFinal` / `isSealed` | `(?class, isSealed, "true")` | C# uses "sealed", Java uses "final" |
| `class.fields[].name` | `(?field, type, cs:Field)` + `(?field, hasName, "name")` | |
| `class.fields[].typeDesc` | `(?field, hasType, ?type)` | Type information as role assertion |
| `class.methods[].name` | `(?method, type, cs:Method)` + `(?method, hasName, "name")` | |
| `class.methods[].definedIn` | `(?method, definedIn, ?class)` | Links method to containing class |
| `class.methods[].returnTypeDesc` | `(?method, returnType, ?type)` | Attribute on method fact |
| `class.methods[].parameters` | `(?param, type, cs:Parameter)` + `(?param, parameterOf, ?method)` | |
| `class.methods[].calls` | `(?method, calls, ?callee)` | Call graph edges |
| `class.constructors[].creates` | `(?constructor, creates, ?type)` | Object instantiation tracking |
| `class.methods[].gets` | `(?method, reads, ?field)` | Field access tracking (if implemented) |
| `class.methods[].sets` | `(?method, writes, ?field)` | Field mutation tracking (if implemented) |

### Key Architectural Difference

| Aspect | OASEMapping.stg | RETER |
|--------|----------------|-------|
| **Data Model** | Hierarchical objects (Class → Methods → Calls) | Flat facts (triples) |
| **Aggregation** | Pre-aggregated by parser | Aggregated via queries/rules |
| **Output** | CNL text assertions | RDF-compatible facts |
| **Reasoning** | Post-transformation DL reasoner | Built-in Rete engine |

### OASE `global()` Axioms vs RETER Rules

The `global()` template defines inference rules. Here's how they map to RETER:

```
OASE (CNL):
If X is-subclass-of something that is-subclass-of Y then X is-subclass-of Y.

RETER (Rule Pattern):
r.rule(
    [('?X', 'extends', '?Z'), ('?Z', 'extends', '?Y')],
    [('?X', 'extends', '?Y')]  # Transitive closure
)
```

```
OASE (CNL):
If X is-instance-of something that is-subclass-of Y then Y is-type-of X.

RETER (Rule Pattern):
r.rule(
    [('?X', 'type', '?class'), ('?class', 'extends', '?Y')],
    [('?X', 'type', '?Y')]  # Type inheritance
)
```

```
OASE (CNL):
If X calls something that calls Y then X calls Y.

RETER (Rule Pattern):
r.rule(
    [('?X', 'calls', '?Z'), ('?Z', 'calls', '?Y')],
    [('?X', 'transitively-calls', '?Y')]  # Transitive call graph
)
```

### Bridging RETER Facts to OASE Class Descriptors

To use OASEMapping.stg with RETER-extracted facts, aggregate flat facts into class descriptors:

```python
def build_class_descriptor(rete, class_id):
    """Aggregate RETER facts into OASE-compatible class descriptor."""

    # Get class basics
    class_facts = rete.query([('?class', 'type', 'cs:Class'), ('?class', 'hasName', '?name')])

    # Get base classes
    bases = rete.query([(class_id, 'extends', '?base')])

    # Get methods
    methods = rete.query([('?method', 'definedIn', class_id), ('?method', 'type', 'cs:Method')])

    # Get fields
    fields = rete.query([('?field', 'definedIn', class_id), ('?field', 'type', 'cs:Field')])

    # Build descriptor object
    return {
        'className': class_id.split('.')[-1],
        'baseFullNames': [b['base'] for b in bases],
        'isAbstract': rete.has_fact(class_id, 'isAbstract', 'true'),
        'isFinal': rete.has_fact(class_id, 'isSealed', 'true'),
        'fields': [build_field_descriptor(rete, f['field']) for f in fields],
        'methods': [build_method_descriptor(rete, m['method']) for m in methods],
    }
```

### Current RETER Extraction Coverage

| Feature | C# | C++ | Python | JavaScript |
|---------|-----|-----|--------|------------|
| Classes/Types | ✅ | ✅ | ✅ | ✅ |
| Inheritance | ✅ | ✅ | ✅ | ✅ |
| Methods | ✅ | ✅ | ✅ | ✅ |
| Fields/Properties | ✅ | ✅ | ✅ | ✅ |
| Parameters | ✅ | ✅ | ✅ | ✅ |
| Method Calls | ✅ | ✅ | ✅ | ✅ |
| Object Creates | Partial | Partial | Partial | Partial |
| Field Gets/Sets | ❌ | ❌ | ❌ | ❌ |
| Access Modifiers | ✅ | ✅ | N/A | N/A |
| Type Annotations | ✅ | ✅ | ✅ | Partial |
| ::: Annotations | ✅ | ✅ | ✅ | ✅ |

### Recommended Extensions for Full OASE Compatibility

To achieve full OASEMapping.stg compatibility, RETER extractors could be extended:

1. **Field Access Tracking** (`gets`/`sets`)
   ```cpp
   // In visitPrimary_expression():
   // Detect field reads: obj.field (without assignment)
   // Detect field writes: obj.field = value
   ```

2. **Object Creation Tracking** (`creates`)
   ```cpp
   // Already partially implemented via 'new' expression detection
   // Extend to capture constructor arguments
   ```

3. **Collection Type Detection**
   ```cpp
   // Parse generic type arguments: List<Item> → setElementTypeFullName = "Item"
   ```

4. **Signature-based Method Signatures**
   ```cpp
   // Map OASE "Signature" concept to RETER method identifiers
   ```

### Using CNL as OASE-English Output

Since RETER includes a full CNL implementation, facts can be verbalized:

```python
# Extract facts
facts = rete.query([('?s', '?p', '?o')])

# Generate CNL using grammar
for fact in facts:
    if fact['p'] == 'type':
        print(f'The-thing-called "{fact["s"]}" is a {fact["o"]}.')
    elif fact['p'] == 'extends':
        print(f'The-thing-called "{fact["s"]}" is-subclass-of the-thing-called "{fact["o"]}".')
    elif fact['p'] == 'calls':
        print(f'The-thing-called "{fact["s"]}" calls the-thing-called "{fact["o"]}".')
```

This produces output compatible with OASE-English semantics.
