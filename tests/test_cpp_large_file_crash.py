#!/usr/bin/env python3
"""
Test C++ parser with large real-world files to reproduce crash.

The bug: C++ parser segfaults on certain large files (e.g. Bitcoin's
net_processing.cpp at ~6200 lines / 302KB). The process dies silently
without raising a Python exception.

This test isolates the crash to reter_core's load_cpp_from_string.
"""

import os
import pytest
from reter_core import owl_rete_cpp as owl


BITCOIN_ROOT = r"F:\bitcoin"
BITCOIN_CPP = os.path.join(BITCOIN_ROOT, "src", "net_processing.cpp")


def _load_cpp_string(code: str, filename: str = "test.cpp"):
    """Helper: load C++ code string into a fresh network, return fact count."""
    network = owl.ReteNetwork()
    wme_count = owl.load_cpp_from_string(network, code, filename, filename)
    return wme_count, network


@pytest.mark.skipif(
    not os.path.exists(BITCOIN_CPP),
    reason=f"Bitcoin source not found at {BITCOIN_CPP}"
)
class TestBitcoinNetProcessing:
    """Reproduce crash on Bitcoin's net_processing.cpp."""

    @pytest.fixture
    def code(self):
        with open(BITCOIN_CPP, "r", encoding="utf-8") as f:
            return f.read()

    def test_load_full_file(self, code):
        """Load the entire file — this is the crash reproducer."""
        wme_count, network = _load_cpp_string(code, "src/net_processing.cpp")
        assert wme_count > 0, "Expected facts from net_processing.cpp"
        print(f"OK: {wme_count} facts from {len(code)} bytes")

    def test_load_first_half(self, code):
        """Load first half to bisect where the crash occurs."""
        lines = code.splitlines(keepends=True)
        half = "".join(lines[: len(lines) // 2])
        wme_count, _ = _load_cpp_string(half, "src/net_processing_half1.cpp")
        print(f"First half: {wme_count} facts from {len(lines)//2} lines")

    def test_load_second_half(self, code):
        """Load second half to bisect where the crash occurs."""
        lines = code.splitlines(keepends=True)
        half = "".join(lines[len(lines) // 2 :])
        wme_count, _ = _load_cpp_string(half, "src/net_processing_half2.cpp")
        print(f"Second half: {wme_count} facts from {len(lines) - len(lines)//2} lines")

    def test_load_in_quarters(self, code):
        """Load in quarters to narrow down the crash location."""
        lines = code.splitlines(keepends=True)
        total = len(lines)
        q = total // 4

        for i, (start, end) in enumerate([(0, q), (q, 2*q), (2*q, 3*q), (3*q, total)]):
            chunk = "".join(lines[start:end])
            label = f"Q{i+1} (lines {start+1}-{end})"
            try:
                wme_count, _ = _load_cpp_string(chunk, f"quarter_{i+1}.cpp")
                print(f"  {label}: OK, {wme_count} facts")
            except Exception as e:
                print(f"  {label}: EXCEPTION: {e}")
                raise


class TestCppParserLimits:
    """Test parser with synthetically large C++ code."""

    def test_many_methods(self):
        """Generate a class with many methods to stress the parser."""
        methods = "\n".join(
            f"    void method_{i}(int a{i}, double b{i}) {{ /* body */ }}"
            for i in range(500)
        )
        code = f"class BigClass {{\npublic:\n{methods}\n}};"
        wme_count, _ = _load_cpp_string(code, "big_class.cpp")
        assert wme_count > 0
        print(f"500 methods: {wme_count} facts")

    def test_deep_nesting(self):
        """Deeply nested scopes."""
        depth = 50
        code = "void deep() {\n"
        for i in range(depth):
            code += "  " * (i + 1) + f"if (cond{i}) {{\n"
        code += "  " * (depth + 1) + "int x = 0;\n"
        for i in range(depth - 1, -1, -1):
            code += "  " * (i + 1) + "}\n"
        code += "}\n"
        wme_count, _ = _load_cpp_string(code, "deep_nesting.cpp")
        print(f"Depth {depth}: {wme_count} facts")

    def test_many_includes(self):
        """Many include directives."""
        includes = "\n".join(f'#include "header_{i}.h"' for i in range(200))
        code = includes + "\n\nvoid func() {}\n"
        wme_count, _ = _load_cpp_string(code, "many_includes.cpp")
        print(f"200 includes: {wme_count} facts")

    def test_long_lines(self):
        """Very long lines (template instantiations etc.)."""
        # Simulate a long template chain
        long_type = "std::map<" + ", ".join(f"Type{i}" for i in range(100)) + ">"
        code = f"{long_type} global_var;\nvoid use_it({long_type} arg) {{}}\n"
        wme_count, _ = _load_cpp_string(code, "long_lines.cpp")
        print(f"Long lines: {wme_count} facts")

    def test_large_enum(self):
        """Large enum (common in protocol code)."""
        values = ",\n".join(f"    VALUE_{i} = {i}" for i in range(1000))
        code = f"enum BigEnum {{\n{values}\n}};\n"
        wme_count, _ = _load_cpp_string(code, "large_enum.cpp")
        print(f"1000-value enum: {wme_count} facts")
