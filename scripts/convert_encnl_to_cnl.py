#!/usr/bin/env python3
"""
Convert ENCNL (Extended CNL) to our CNL format.

ENCNL is used by Cognitum's FluentEditor and has additional constructs
that our CNL parser doesn't support. This script extracts compatible statements.

Supported conversions:
- Every X is a Y. -> Every X is a Y.
- No X is a Y. -> No X is a Y.
- If X R something that R Y then X R Y. -> If X R something that R Y then X R Y.
- If X R Y then Y does-not R X. -> If X R Y then Y does-not R X.
- Nothing R itself. -> Nothing R itself.

Skipped patterns:
- X is a concept-type.
- X is a role-type.
- X has-description equal-to '...'.
- Comment: '...' .
- Label: '...' .
- See-Also: '...' .
- Namespace: '...'.
"""

import re
import sys
from pathlib import Path


def convert_encnl_to_cnl(input_path: str, output_path: str = None) -> str:
    """Convert ENCNL file to CNL format.

    Args:
        input_path: Path to input ENCNL file
        output_path: Optional path for output CNL file

    Returns:
        Converted CNL content
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')

    # Patterns to skip
    skip_patterns = [
        r'^Namespace:',
        r'^Comment:',
        r'^Comment\'',
        r'^Label:',
        r'^See-Also:',
        r'has-description equal-to',
        r'^\s*$',  # Empty lines
    ]

    # Patterns to keep (compile for efficiency)
    keep_patterns = [
        # Subsumption: Every X is a Y.
        (r'^Every\s+[\w-]+\s+is\s+an?\s+[\w-]+\.$', None),
        # Disjoint: No X is a Y.
        (r'^No\s+[\w-]+\s+is\s+an?\s+[\w-]+\.$', None),
        # Transitivity: If X R something that R Y then X R Y.
        (r'^If\s+X\s+[\w-]+\s+something\s+that\s+[\w-]+\s+Y\s+then\s+X\s+[\w-]+\s+Y\.$', None),
        # Asymmetry: If X R Y then Y does-not R X.
        (r'^If\s+X\s+[\w-]+\s+Y\s+then\s+Y\s+does-not\s+[\w-]+\s+X\.$', None),
        # Irreflexivity: Nothing R itself.
        (r'^Nothing\s+[\w-]+\s+itself\.$', None),
        # Symmetry: X R Y if-and-only-if Y R X.
        (r'^X\s+[\w-]+\s+Y\s+if-and-only-if\s+[\w-]+\.$', None),
    ]

    output_lines = []

    # First pass: collect all statements by type
    concept_types = []
    role_types = []
    subsumptions = []
    disjoints = []
    transitivity = []
    asymmetry = []
    irreflexivity = []
    other = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1

        # Skip multi-line content (look for continuation)
        while i < len(lines) and not lines[i-1].strip().endswith('.'):
            i += 1

        # Skip patterns
        if any(re.search(p, line) for p in skip_patterns):
            continue

        # Check against keep patterns
        if re.match(r'^Every\s+[\w-]+\s+is\s+an?\s+[\w-]+\.$', line):
            subsumptions.append(line)
        elif re.match(r'^No\s+[\w-]+\s+is\s+an?\s+[\w-]+\.$', line):
            disjoints.append(line)
        elif re.match(r'^If\s+X\s+[\w-]+\s+something\s+that\s+[\w-]+\s+Y\s+then\s+X\s+[\w-]+\s+Y\.$', line):
            transitivity.append(line)
        elif re.match(r'^If\s+X\s+[\w-]+\s+Y\s+then\s+Y\s+does-not\s+[\w-]+\s+X\.$', line):
            asymmetry.append(line)
        elif re.match(r'^Nothing\s+[\w-]+\s+itself\.$', line):
            irreflexivity.append(line)
        elif re.match(r'^If\s+X\s+[\w-]+\s+Y\s+then\s+X\s+[\w-]+\s+Y\.$', line):
            # Role equivalence (sub-property)
            other.append(line)
        elif line and not any(re.search(p, line) for p in skip_patterns):
            # Track unhandled lines for debugging
            pass

    # Output all statements
    for stmt in sorted(set(subsumptions)):
        output_lines.append(stmt)

    for stmt in sorted(set(disjoints)):
        output_lines.append(stmt)

    for stmt in sorted(set(transitivity)):
        output_lines.append(stmt)

    for stmt in sorted(set(asymmetry)):
        output_lines.append(stmt)

    for stmt in sorted(set(irreflexivity)):
        output_lines.append(stmt)

    for stmt in sorted(set(other)):
        output_lines.append(stmt)

    result = '\n'.join(output_lines)

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"Converted {input_path} -> {output_path}")
        print(f"  Subsumptions: {len(subsumptions)}")
        print(f"  Disjoints: {len(disjoints)}")
        print(f"  Transitivity axioms: {len(transitivity)}")
        print(f"  Asymmetry axioms: {len(asymmetry)}")
        print(f"  Irreflexivity axioms: {len(irreflexivity)}")
        print(f"  Other: {len(other)}")

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: convert_encnl_to_cnl.py <input.encnl> [output.cnl]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    if not output_path:
        output_path = str(Path(input_path).with_suffix('.cnl'))

    convert_encnl_to_cnl(input_path, output_path)


if __name__ == '__main__':
    main()
