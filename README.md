# RETER

High-performance Description Logic reasoner with C++ RETE engine.

## Installation

With uv (no clone needed):
```bash
uv pip install git+https://github.com/codeine-ai/reter.git --find-links https://raw.githubusercontent.com/codeine-ai/reter/main/reter_core/index.html
```

Or clone and install:
```bash
git clone https://github.com/codeine-ai/reter.git && uv pip install ./reter --find-links ./reter/reter_core/
```

With pip:
```bash
git clone https://github.com/codeine-ai/reter.git
cd reter
pip install . --find-links ./reter_core/
```

## Quick Start

```python
from reter import Reter

# Create reasoner
r = Reter()

# Load ontology
r.load_ontology("""
Person ⊑ᑦ Animal
Student ⊑ᑦ Person
Person（John）
Student（Alice）
""")

# Query instances
people = r.instances_of("Person")
for p in people:
    print(p["?x"])

# REQL queries
result = r.reql("SELECT ?x WHERE { ?x type Person }")
print(result.to_pandas())
```

## Features

- Fast OWL 2 RL reasoning using C++ RETE algorithm
- Description Logic parser (C++ implementation)
- SWRL rule support
- Query interface with Arrow integration
- Source tracking for incremental ontology loading
- Python, JavaScript, C#, and C++ code analysis

## License

**reter** (this package) is licensed under the [MIT License](LICENSE).

**reter-core** (the C++ engine, distributed as binary wheels) is proprietary software owned by Codeine.AI. It is distributed in binary form only and may only be used as a dependency of the reter package. See [LICENSE](LICENSE) for details.
