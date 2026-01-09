#!/usr/bin/env python3
"""Extract CNL patterns from gufo_overview.md and grammar.md for testing."""

from pathlib import Path

def extract_gufo_patterns():
    """Extract patterns from gufo_overview.md."""
    gufo_md = Path(__file__).parent.parent.parent / 'reter_core/rete_cpp/cnl/gufo_overview.md'
    content = gufo_md.read_text(encoding='utf-8')
    lines = content.split('\n')

    current_section = 'intro'
    patterns = []

    for line in lines:
        if line.startswith('###'):
            current_section = line.strip('#').strip()
        elif line.startswith('    ') and not line.startswith('    #'):
            stripped = line.strip()
            if stripped and stripped.endswith('.') and not stripped.startswith('#'):
                patterns.append((current_section, stripped))

    return patterns


def extract_grammar_patterns():
    """Extract patterns from grammar.md."""
    grammar_md = Path(__file__).parent.parent.parent / 'reter_core/rete_cpp/cnl/grammar.md'
    content = grammar_md.read_text(encoding='utf-8')
    lines = content.split('\n')

    current_section = 'intro'
    patterns = []

    keywords = ['Every ', 'Something ', 'Nothing ', 'If ', 'No ', 'The ', 'A ', 'An ',
                'every ', 'X ', 'Anything ', 'Every-single-thing']
    skip_terms = ['LARK', '::=', '->', 'http://', 'www.', 'OWL', 'RDF', '.g4',
                  'ANTLR', 'lexer', 'parser', 'grammar']

    for line in lines:
        if line.startswith('##'):
            current_section = line.strip('#').strip()

        stripped = line.strip()
        if stripped and stripped.endswith('.') and not stripped.startswith('#') and not stripped.startswith('|'):
            if any(kw in stripped for kw in keywords):
                if not any(x in stripped for x in skip_terms):
                    patterns.append((current_section, stripped))

    return patterns


if __name__ == '__main__':
    gufo = extract_gufo_patterns()
    grammar = extract_grammar_patterns()

    print(f"gufo_overview.md: {len(gufo)} patterns")
    print(f"grammar.md: {len(grammar)} patterns")

    # Show first few
    print("\nFirst 5 gufo patterns:")
    for s, p in gufo[:5]:
        print(f"  [{s}] {p}")

    print("\nFirst 5 grammar patterns:")
    for s, p in grammar[:5]:
        print(f"  [{s}] {p}")
