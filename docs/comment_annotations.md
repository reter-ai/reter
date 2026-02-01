# Comment-Based Semantic Annotations

RETER supports extracting semantic facts from specially formatted comments in your code. Two syntax styles are available:

1. **CNL syntax** (`:::`) - **PREFERRED** - Natural language style using Controlled Natural Language
2. **Predicate syntax** (`@reter:`) - **DEPRECATED** - Compact, programmatic style (still supported for backwards compatibility)

This allows you to add architectural metadata, dependency information, and custom semantic relationships directly in your source code.

## Overview

Comment annotations let you define semantic facts that become queryable alongside the automatically extracted code structure. This is useful for:

- Documenting architectural layers (Presentation, Service, Infrastructure)
- Explicitly declaring dependencies between components
- Marking code with custom concepts (critical-path, security-sensitive, etc.)
- Adding metadata that can't be inferred from code structure

---

## CNL Annotations (`:::`) - PREFERRED

CNL (Controlled Natural Language) provides a readable, English-like syntax for semantic annotations.

### Basic Format

```
::: This is-in-layer Service-Layer.
::: This is a repository.
::: This depends-on `services.PaymentService`.
```

### Key Rules

- **Layers** use relations: `This is-in-layer <Layer-Name>.` (hyphenated, Title-Case)
- **Components** use concept assertions: `This is a <concept>.` (lowercase)
- **Relations** use predicates: `This depends-on <Target>.`
- **`This`** is automatically resolved to the current class/method as a fully qualified name
- Use **backticks** for qualified names: `` `module.ClassName` ``
- Sentences end with `.` or `?`
- No acronyms - use full words (e.g., `Domain-Specific-Language-Layer` not `DSL-Layer`)

### Supported Prefixes

- `:::`
- `#reter-cnl:`
- `reter-cnl:`

### CNL Sentence Patterns

| Pattern | Example | Meaning |
|---------|---------|---------|
| **Layer relation** | `This is-in-layer Service-Layer.` | Architectural layer |
| **Concept assertion** | `This is a repository.` | Functional role |
| **Role assertion** | `This depends-on Payment-Service.` | Object property |
| **Data property** | `This has-version "1.0".` | Data value |
| **Subsumption** | `Every controller is a component.` | Class hierarchy |
| **Restriction** | `Every service must have-logger.` | Existential restriction |

### Architectural Layers

| Layer | CNL Name |
|-------|----------|
| Presentation | `Presentation-Layer` |
| Service | `Service-Layer` |
| Domain-Specific-Language | `Domain-Specific-Language-Layer` |
| Infrastructure | `Infrastructure-Layer` |
| Core | `Core-Layer` |
| Test | `Test-Layer` |
| Utility | `Utility-Layer` |

### Functional Components (Concepts)

| Component | CNL Concept |
|-----------|-------------|
| Repository | `repository` |
| Service | `service` |
| Handler | `handler` |
| Manager | `manager` |
| Parser | `parser` |
| Compiler | `compiler` |
| Value-Object | `value-object` |
| Factory | `factory` |
| Builder | `builder` |

---

## Language Examples (CNL)

### Python

```python
class OrderService:
    """
    Handles order processing.

    ::: This is-in-layer Service-Layer.
    ::: This is a service.
    ::: This depends-on `services.PaymentService`.
    ::: This has-owner "Team A".
    """

    def process_order(self, order):
        """
        ::: This is a critical-path.
        """
        pass
```

### JavaScript / TypeScript

```javascript
/**
 * Authentication service.
 * ::: This is-in-layer Service-Layer.
 * ::: This is a handler.
 * ::: This depends-on `TokenStore`.
 */
class AuthService {
    /**
     * ::: This is a critical-path.
     */
    login(credentials) {
        // ...
    }
}
```

### C#

```csharp
/// <summary>
/// Order repository.
/// ::: This is-in-layer Infrastructure-Layer.
/// ::: This is a repository.
/// ::: This implements `IOrderRepository`.
/// </summary>
public class OrderRepository
{
    /// ::: This is a database-operation.
    public void Save(Order order) { }
}
```

### C++

```cpp
/**
 * Memory pool allocator.
 * ::: This is-in-layer Core-Layer.
 * ::: This is a manager.
 * ::: This has-complexity "O(1)".
 */
class MemoryPool {
public:
    // ::: This is a performance-critical.
    void* allocate(size_t size);
};
```

### HTML

```html
<!DOCTYPE html>
<!-- ::: This is a web-page. -->
<!-- ::: This belongs-to Marketing-Site. -->
<html>
<head>
    <!-- ::: This has-author "Design Team". -->
    <title>Home</title>
</head>
<body>
    <!-- ::: This is a user-interface-component. -->
    <main id="content">...</main>
</body>
</html>
```

---

## Common Use Cases

### Architectural Layers

```python
class UserController:
    """
    ::: This is-in-layer Presentation-Layer.
    ::: This is a controller.
    """

class UserService:
    """
    ::: This is-in-layer Service-Layer.
    ::: This is a service.
    ::: This depends-on `app.repositories.UserRepository`.
    """

class UserRepository:
    """
    ::: This is-in-layer Infrastructure-Layer.
    ::: This is a repository.
    """
```

### Security Annotations

```python
class AuthService:
    """
    ::: This is a security-critical.
    ::: This requires-audit "true".
    """

    def validate_token(self, token):
        """
        ::: This is a security-sensitive.
        ::: This handles-credentials "JSON-Web-Token".
        """
```

### Domain-Driven Design

```python
class Order:
    """
    ::: This is a aggregate-root.
    ::: This is-in-bounded-context Order-Management.
    """

class OrderLine:
    """
    ::: This is a entity.
    ::: This is-part-of `domain.Order`.
    """

class OrderPlaced:
    """
    ::: This is a domain-event.
    ::: This is-raised-by `domain.Order`.
    """
```

### Design Patterns

```python
class ConfigManager:
    """
    ::: This is a singleton.
    """

class VehicleFactory:
    """
    ::: This is a factory.
    ::: This creates `domain.Vehicle`.
    """
```

### Cross-File Dependencies

```python
# file: services/order_service.py
class OrderService:
    """
    ::: This depends-on `services.payment.PaymentGateway`.
    ::: This depends-on `services.inventory.StockService`.
    ::: This publishes `events.OrderCreated`.
    """
```

---

## Querying Annotations

### Pattern API

```python
from reter import Reter

r = Reter()
r.load_python_code(code, 'services.py')

# Find all Service-Layer classes
results = r.pattern(('?class', 'is-in-layer', 'Service-Layer')).to_list()
for result in results:
    print(result['?class'])

# Find dependencies
deps = r.pattern(('?source', 'depends-on', '?target')).to_list()
for dep in deps:
    print(f"{dep['?source']} depends on {dep['?target']}")
```

### REQL Queries

```python
# Find classes in Service-Layer
results = r.reql('SELECT ?c WHERE { ?c is-in-layer Service-Layer }')
classes = results[0].to_pylist()

# Find what Service-Layer depends on
results = r.reql('''
    SELECT ?source ?target WHERE {
        ?source is-in-layer Service-Layer .
        ?source depends-on ?target
    }
''')
```

---

## Predicate Annotations (`@reter:`) - DEPRECATED

> **Note:** This syntax is deprecated. Use `:::` instead.

The predicate syntax is still supported for backwards compatibility.

### Basic Format

```
@reter: Predicate(Argument1, Argument2, ...)
```

### Three Types

| Type | Syntax | Description |
|------|--------|-------------|
| **Concept** | `@reter: Concept(Individual)` | Asserts that an entity belongs to a concept/class |
| **Object Role** | `@reter: role(Subject, Object)` | Relates two entities |
| **Data Role** | `@reter: role(Subject, "literal")` | Relates an entity to a literal value |

### Supported Prefixes

- `@reter:`
- `#reter:`
- `reter:`
- `@semantic:`
- `@owl:`
- `@fact:`

### Migration to CNL

| Deprecated Predicate Syntax | Preferred CNL Syntax |
|----------------------------|----------------------|
| `@reter: ServiceLayer(self)` | `::: This is-in-layer Service-Layer.` |
| `@reter: Repository(self)` | `::: This is a repository.` |
| `@reter: dependsOn(self, services.X)` | ``::: This depends-on `services.X`.`` |
| `@reter: hasOwner(self, "Team A")` | `::: This has-owner "Team A".` |

---

## Best Practices

1. **Use `:::`** - The CNL syntax is preferred and more readable
2. **Use qualified names** for cross-file references with backticks
3. **Use `This`** for the current class/method to avoid duplication
4. **Be consistent** with naming conventions across your codebase
5. **No acronyms** - Use `Domain-Specific-Language-Layer` not `DSL-Layer`
6. **Lowercase concepts** - Use `This is a repository.` not `This is a Repository.`

## Fact Types Generated

| Annotation Type | Generated Fact Type | Key Attributes |
|-----------------|---------------------|----------------|
| Layer relation | `role_assertion` | `subject`, `role`, `object` |
| Concept assertion | `instance_of` | `individual`, `concept` |
| Object Role | `role_assertion` | `subject`, `role`, `object` |
| Data Role | `role_assertion` | `subject`, `role`, `value`, `datatype` |

All facts include:
- `inFile` - Source file path
- `atLine` - Line number
- `source` - `"cnl_annotation"` or `"comment_annotation"`
