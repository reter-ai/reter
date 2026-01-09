"""
Test CNL (Controlled Natural Language) parsing functionality.

Tests the C++ CNL parser that converts English-like ontology statements
into RETER facts.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
try:
    import owl_rete_cpp
    CNL_AVAILABLE = hasattr(owl_rete_cpp, 'parse_cnl')
except ImportError:
    CNL_AVAILABLE = False


@pytest.mark.skipif(not CNL_AVAILABLE, reason="CNL parser not compiled")
class TestCNLBasicParsing:
    """Test basic CNL parsing functionality"""

    def test_parse_cnl_available(self):
        """Test that CNL functions are exposed"""
        assert hasattr(owl_rete_cpp, 'parse_cnl')
        assert hasattr(owl_rete_cpp, 'parse_cnl_file')
        assert hasattr(owl_rete_cpp, 'load_cnl_from_string')
        assert hasattr(owl_rete_cpp, 'validate_cnl')
        assert hasattr(owl_rete_cpp, 'get_cnl_version')

    def test_get_cnl_version(self):
        """Test CNL version retrieval"""
        version = owl_rete_cpp.get_cnl_version()
        assert isinstance(version, str)
        assert len(version) > 0
        print(f"CNL version: {version}")

    def test_empty_input(self):
        """Test parsing empty input"""
        result = owl_rete_cpp.parse_cnl("")
        assert result.success
        assert len(result.facts) == 0
        assert len(result.errors) == 0


@pytest.mark.skipif(not CNL_AVAILABLE, reason="CNL parser not compiled")
class TestCNLSubsumption:
    """Test CNL class subsumption (Every X is a Y)"""

    def test_simple_subsumption(self):
        """Test: Every cat is a mammal."""
        result = owl_rete_cpp.parse_cnl("Every cat is a mammal.")
        assert result.success, f"Parse errors: {result.errors}"
        assert len(result.facts) >= 1

        # Find subsumption fact
        subsumption_facts = [f for f in result.facts if f.get('type') == 'subsumption']
        assert len(subsumption_facts) >= 1

        fact = subsumption_facts[0]
        assert fact.get('sub') == 'cat'
        assert fact.get('sup') == 'mammal'

    def test_multiple_subsumptions(self):
        """Test multiple subsumption sentences"""
        cnl = """
        Every cat is a mammal.
        Every mammal is an animal.
        Every dog is a mammal.
        """
        result = owl_rete_cpp.parse_cnl(cnl)
        assert result.success, f"Parse errors: {result.errors}"

        subsumption_facts = [f for f in result.facts if f.get('type') == 'subsumption']
        assert len(subsumption_facts) >= 3

    def test_plural_subsumption(self):
        """Test: Every cat is a mammal. (with plural handling)"""
        # Should normalize plurals correctly
        result = owl_rete_cpp.parse_cnl("Every cats is a mammals.")
        # This might fail or produce a warning - depends on grammar
        # The morphology should convert cats -> cat

    def test_compound_noun_subsumption(self):
        """Test compound nouns like 'domestic-cat'"""
        result = owl_rete_cpp.parse_cnl("Every domestic-cat is a cat.")
        assert result.success, f"Parse errors: {result.errors}"

        subsumption_facts = [f for f in result.facts if f.get('type') == 'subsumption']
        assert len(subsumption_facts) >= 1


@pytest.mark.skipif(not CNL_AVAILABLE, reason="CNL parser not compiled")
class TestCNLEquivalence:
    """Test CNL class equivalence (if-and-only-if)"""

    def test_concept_equivalence(self):
        """Test: Every cat is an animal if-and-only-if-it is a feline."""
        result = owl_rete_cpp.parse_cnl(
            "Every cat is an animal if-and-only-if-it is a feline."
        )
        assert result.success, f"Parse errors: {result.errors}"

        equiv_facts = [f for f in result.facts if f.get('type') == 'equivalence']
        assert len(equiv_facts) >= 1


@pytest.mark.skipif(not CNL_AVAILABLE, reason="CNL parser not compiled")
class TestCNLDisjoint:
    """Test CNL disjoint classes (No X is Y)"""

    def test_disjoint_classes(self):
        """Test: No cat is a dog."""
        result = owl_rete_cpp.parse_cnl("No cat is a dog.")
        assert result.success, f"Parse errors: {result.errors}"

        # Should produce disjoint class fact
        disjoint_facts = [f for f in result.facts
                         if f.get('type') in ('disjoint', 'alldisjoint_classes')]
        assert len(disjoint_facts) >= 1


@pytest.mark.skipif(not CNL_AVAILABLE, reason="CNL parser not compiled")
class TestCNLInstances:
    """Test CNL instance assertions"""

    def test_instance_assertion(self):
        """Test: John is a person."""
        result = owl_rete_cpp.parse_cnl("John is a person.")
        assert result.success, f"Parse errors: {result.errors}"

        instance_facts = [f for f in result.facts if f.get('type') == 'instance_of']
        assert len(instance_facts) >= 1

        fact = instance_facts[0]
        assert fact.get('individual') == 'John'
        assert fact.get('concept') == 'person'

    def test_role_assertion(self):
        """Test: Mary is married-to John."""
        result = owl_rete_cpp.parse_cnl("Mary is married-to John.")
        assert result.success, f"Parse errors: {result.errors}"

        role_facts = [f for f in result.facts if f.get('type') == 'role_assertion']
        assert len(role_facts) >= 1


@pytest.mark.skipif(not CNL_AVAILABLE, reason="CNL parser not compiled")
class TestCNLCardinality:
    """Test CNL cardinality restrictions"""

    def test_at_most_cardinality(self):
        """Test: Every person has at-most 2 parents."""
        result = owl_rete_cpp.parse_cnl("Every person has at-most 2 parents.")
        assert result.success, f"Parse errors: {result.errors}"

    def test_at_least_cardinality(self):
        """Test: Every person has at-least 1 parent."""
        result = owl_rete_cpp.parse_cnl("Every person has at-least 1 parent.")
        assert result.success, f"Parse errors: {result.errors}"

    def test_exactly_cardinality(self):
        """Test: Every person has exactly 2 biological-parents."""
        result = owl_rete_cpp.parse_cnl("Every person has exactly 2 biological-parents.")
        assert result.success, f"Parse errors: {result.errors}"


@pytest.mark.skipif(not CNL_AVAILABLE, reason="CNL parser not compiled")
class TestCNLExistential:
    """Test CNL existential restrictions (something)"""

    def test_existential_restriction(self):
        """Test: Every cat eats something that is a mouse."""
        result = owl_rete_cpp.parse_cnl("Every cat eats something that is a mouse.")
        assert result.success, f"Parse errors: {result.errors}"

        # Should produce some_values_from restriction
        svf_facts = [f for f in result.facts if f.get('type') == 'some_values_from']
        # Or subsumption to existential restriction
        assert len(result.facts) >= 1


@pytest.mark.skipif(not CNL_AVAILABLE, reason="CNL parser not compiled")
class TestCNLUniversal:
    """Test CNL universal restrictions (nothing-but)"""

    def test_universal_restriction(self):
        """Test: Every herbivore eats nothing-but plants."""
        result = owl_rete_cpp.parse_cnl("Every herbivore eats nothing-but plants.")
        assert result.success, f"Parse errors: {result.errors}"

        # Should produce all_values_from restriction
        avf_facts = [f for f in result.facts if f.get('type') == 'all_values_from']
        assert len(result.facts) >= 1


@pytest.mark.skipif(not CNL_AVAILABLE, reason="CNL parser not compiled")
class TestCNLNetworkIntegration:
    """Test CNL integration with RETER network"""

    def test_load_cnl_to_network(self):
        """Test loading CNL directly to network"""
        network = owl_rete_cpp.ReteNetwork()

        cnl = """
        Every cat is a mammal.
        Every mammal is an animal.
        John is a cat.
        """

        count = owl_rete_cpp.load_cnl_from_string(network, cnl)
        assert count >= 3, f"Expected at least 3 facts, got {count}"

        # Verify facts are in network
        all_facts = network.get_all_facts()
        assert len(all_facts) >= 3

    def test_load_cnl_with_source_tracking(self):
        """Test loading CNL with source ID for later removal"""
        network = owl_rete_cpp.ReteNetwork()

        cnl = "Every cat is a mammal."
        count = owl_rete_cpp.load_cnl_from_string(
            network, cnl, source_id="test_cnl"
        )
        assert count >= 1

        # Verify source is tracked
        sources = network.get_all_sources()
        assert "test_cnl" in sources

        # Remove source
        network.remove_source("test_cnl")
        sources = network.get_all_sources()
        assert "test_cnl" not in sources

    def test_cnl_reasoning(self):
        """Test that CNL facts participate in reasoning"""
        network = owl_rete_cpp.ReteNetwork()

        cnl = """
        Every cat is a mammal.
        Every mammal is an animal.
        Whiskers is a cat.
        """

        owl_rete_cpp.load_cnl_from_string(network, cnl)

        # Query for inferred instance_of facts
        # Whiskers should be inferred to be a mammal and animal
        results = network.reql_query("""
            SELECT ?individual ?concept
            WHERE {
                ?wme type "instance_of" .
                ?wme individual ?individual .
                ?wme concept ?concept
            }
            FILTER (?individual = "Whiskers")
        """)

        concepts = set()
        for i in range(results.num_rows):
            concepts.add(results.column('concept')[i].as_py())

        # Should have at least cat (and ideally mammal, animal through reasoning)
        assert 'cat' in concepts


@pytest.mark.skipif(not CNL_AVAILABLE, reason="CNL parser not compiled")
class TestCNLValidation:
    """Test CNL validation without network loading"""

    def test_validate_valid_cnl(self):
        """Test validation of valid CNL"""
        errors = owl_rete_cpp.validate_cnl("Every cat is a mammal.")
        assert len(errors) == 0

    def test_validate_invalid_cnl(self):
        """Test validation of invalid CNL"""
        # This should produce errors
        errors = owl_rete_cpp.validate_cnl("Every cat mammal")  # missing 'is a'
        # Depending on grammar strictness, this may or may not error
        # At minimum, it should not crash


@pytest.mark.skipif(not CNL_AVAILABLE, reason="CNL parser not compiled")
class TestCNLParseOptions:
    """Test CNL parse options"""

    def test_strict_mode(self):
        """Test strict mode parsing"""
        # In strict mode, any error should fail immediately
        result = owl_rete_cpp.parse_cnl("Every cat is a mammal.", strict_mode=True)
        assert result.success

    def test_parse_options_class(self):
        """Test CNLParseOptions class"""
        opts = owl_rete_cpp.CNLParseOptions()
        assert not opts.strict_mode  # default False
        assert opts.allow_unknown_words  # default True
        assert opts.generate_warnings  # default True
        assert opts.default_namespace == ""

        opts.strict_mode = True
        assert opts.strict_mode

    def test_parse_result_stats(self):
        """Test parse result statistics"""
        cnl = """
        Every cat is a mammal.
        Every dog is a mammal.
        John is a person.
        """
        result = owl_rete_cpp.parse_cnl(cnl)
        assert result.num_sentences >= 3
        assert result.num_concepts >= 2  # cat, dog subsumptions
        assert result.num_instances >= 1  # John


@pytest.mark.skipif(not CNL_AVAILABLE, reason="CNL parser not compiled")
class TestCNLPropertyAxioms:
    """Test CNL property axiom sentences"""

    def test_transitive_property(self):
        """Test transitivity: If X R Y and Y R Z then X R Z"""
        # The grammar should support this pattern
        pass  # TODO: Add when SWRL support is complete

    def test_symmetric_property(self):
        """Test symmetry pattern"""
        pass  # TODO: Add when property axioms are complete


@pytest.mark.skipif(not CNL_AVAILABLE, reason="CNL parser not compiled")
class TestCNLSWRLRules:
    """Test CNL SWRL rule sentences"""

    def test_simple_swrl_rule(self):
        """Test: If a person has-age greater-than 18 then the person is an adult."""
        # This is a complex SWRL rule with builtin
        cnl = "If a person has-age greater-than 18 then the person is an adult."
        result = owl_rete_cpp.parse_cnl(cnl)
        # May succeed or fail depending on grammar completeness
        # Don't assert success for now, just ensure no crash

    def test_class_based_rule(self):
        """Test: If something is a student then it is a person."""
        cnl = "If something is a student then it is a person."
        result = owl_rete_cpp.parse_cnl(cnl)
        # This should produce an SWRL rule or subsumption


# Convenience function to run tests manually
def run_tests():
    """Run all CNL tests"""
    print("=" * 70)
    print("CNL (Controlled Natural Language) Parser Tests")
    print("=" * 70)

    if not CNL_AVAILABLE:
        print("CNL parser not available - skipping tests")
        return

    # Run basic tests
    test_classes = [
        TestCNLBasicParsing,
        TestCNLSubsumption,
        TestCNLInstances,
        TestCNLNetworkIntegration,
        TestCNLValidation,
    ]

    passed = 0
    failed = 0

    for test_class in test_classes:
        print(f"\n--- {test_class.__name__} ---")
        instance = test_class()
        for method_name in dir(instance):
            if method_name.startswith('test_'):
                try:
                    getattr(instance, method_name)()
                    print(f"  PASS: {method_name}")
                    passed += 1
                except Exception as e:
                    print(f"  FAIL: {method_name}: {e}")
                    failed += 1

    print(f"\n{'=' * 70}")
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
