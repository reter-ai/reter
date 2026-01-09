#!/usr/bin/env python3
"""
Extract CNL statements from markdown files with ```cnl-add fences.
"""

import re
import sys
from pathlib import Path


# Patterns to skip (unsupported by our CNL parser)
# All patterns are now supported - validation will filter any that fail to parse
SKIP_PATTERNS = []


def extract_cnl_from_md(input_path: str, output_path: str = None, validate: bool = True) -> str:
    """Extract CNL from markdown cnl-add fenced blocks."""
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract all cnl-add blocks
    pattern = r'```cnl-add\n(.*?)```'
    matches = re.findall(pattern, content, re.DOTALL)

    # Combine all CNL statements, skipping unsupported patterns
    cnl_lines = []
    skipped = []
    for block in matches:
        for line in block.strip().split('\n'):
            line = line.strip()
            if not line:
                continue

            # Check if line matches any skip pattern
            skip = False
            for pat in SKIP_PATTERNS:
                if re.search(pat, line):
                    skip = True
                    skipped.append(line)
                    break

            if not skip:
                cnl_lines.append(line)

    # Optionally validate each line parses
    if validate:
        try:
            import reter_core.owl_rete_cpp as cpp
            valid_lines = []
            for line in cnl_lines:
                result = cpp.parse_cnl(line)
                if len(result.facts) > 0:
                    valid_lines.append(line)
                else:
                    skipped.append(line)
            cnl_lines = valid_lines
        except ImportError:
            pass  # Skip validation if module not available

    result = '\n'.join(cnl_lines)

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"Extracted {len(cnl_lines)} valid CNL statements")
        print(f"Skipped {len(skipped)} unsupported statements")
        print(f"Output: {output_path}")

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: extract_cnl_from_md.py <input.md> [output.cnl]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else str(Path(input_path).with_suffix('.cnl'))

    extract_cnl_from_md(input_path, output_path)


if __name__ == '__main__':
    main()
