"""Test quoted identifiers in CNL.

CNL supports quoted identifiers for concepts, roles, and instances:
- "concept-name" - double-quoted concept/role NAME
- `Instance Name` - backtick-quoted BIGNAME instance
- Title-Case - unquoted BIGNAME instance

Double quotes for concepts/roles, backticks for instances.
"""

import pytest
import reter_core.owl_rete_cpp as cpp


def parse_cnl(text):
    """Parse CNL and return list of fact dicts."""
    result = cpp.parse_cnl(text)
    facts = []
    for f in result.facts:
        fact_dict = {}
        for key in f.keys():
            fact_dict[key] = f.get(key)
        facts.append(fact_dict)
    return facts


class TestQuotedConcepts:
    """Test quoted concept names (NAME token with double quotes)."""

    def test_quoted_concept_basic(self):
        """Basic quoted concept name."""
        facts = parse_cnl('Every "my-concept" is a mammal.')
        assert len(facts) >= 1
        # Check that quotes are stripped
        fact = facts[0]
        assert fact.get("sub") == "my-concept"
        assert fact.get("sup") == "mammal"

    def test_quoted_concept_with_spaces(self):
        """Quoted concept with spaces."""
        facts = parse_cnl('Every "flying cat" is a mammal.')
        assert len(facts) >= 1
        fact = facts[0]
        assert fact.get("sub") == "flying cat"

    def test_quoted_concept_reserved_word(self):
        """Quoted concept using a reserved word."""
        # 'value' and 'thing' are keywords, but quoted they become concept names
        facts = parse_cnl('Every "value" is a "thing".')
        assert len(facts) >= 1
        fact = facts[0]
        assert fact.get("sub") == "value"
        assert fact.get("sup") == "thing"

    def test_quoted_concept_special_chars(self):
        """Quoted concept with special characters."""
        facts = parse_cnl('Every "concept@v1" is a category.')
        assert len(facts) >= 1
        fact = facts[0]
        assert fact.get("sub") == "concept@v1"

    def test_quoted_concept_escaped_quote(self):
        """Quoted concept with escaped quote ("")."""
        facts = parse_cnl('Every "say ""hello""" is a greeting.')
        assert len(facts) >= 1
        fact = facts[0]
        assert fact.get("sub") == 'say "hello"'


class TestQuotedRoles:
    """Test quoted role/property names."""

    def test_quoted_role_basic(self):
        """Basic quoted role name."""
        facts = parse_cnl('Every person "is-related-to" a person.')
        assert len(facts) >= 1
        # Find the some_values_from fact with the role
        for fact in facts:
            if fact.get("type") == "some_values_from":
                # Check that role is unquoted
                role = fact.get("property")
                if role == "is-related-to":
                    return
        # If we get here, role wasn't found correctly
        assert False, f"Role 'is-related-to' not found in facts: {facts}"

    def test_quoted_role_with_spaces(self):
        """Quoted role with spaces."""
        facts = parse_cnl('`John` "is friend of" `Mary`.')
        assert len(facts) >= 1
        # Check that a role_assertion was created with unquoted role
        # Note: morphology adds 's' to the verb part, so "is friend of" -> "is friend ofs"
        for fact in facts:
            if fact.get("type") == "role_assertion":
                # The field is 'predicate' not 'role'
                assert fact.get("role") == "is friend ofs"
                return
        assert False, "Role assertion not found"

    def test_quoted_data_property(self):
        """Quoted data property name."""
        facts = parse_cnl('`John` "has-age" equal-to 30.')
        assert len(facts) >= 1
        for fact in facts:
            if fact.get("type") == "data_assertion":
                assert fact.get("property") == "has-age"
                return
        assert False, "Data assertion not found"


class TestBacktickedInstances:
    """Test backtick-quoted instance names (`...` syntax)."""

    def test_backticked_bigname_basic(self):
        """Basic backticked BIGNAME instance."""
        facts = parse_cnl('`Eiffel Tower` is a landmark.')
        assert len(facts) >= 1
        for fact in facts:
            if fact.get("type") == "instance_of":
                assert fact.get("individual") == "Eiffel Tower"
                return
        assert False, "Instance not found"

    def test_backticked_bigname_with_spaces(self):
        """Backticked instance with multiple spaces."""
        facts = parse_cnl('`United Nations Building` is a headquarters.')
        assert len(facts) >= 1
        for fact in facts:
            if fact.get("type") == "instance_of":
                assert fact.get("individual") == "United Nations Building"
                return
        assert False, "Instance not found"

    def test_backticked_constant(self):
        """Backticked constant (replaces VERYBIGNAME)."""
        facts = parse_cnl('`USA GOVERNMENT` is an organization.')
        assert len(facts) >= 1
        for fact in facts:
            if fact.get("type") == "instance_of":
                assert fact.get("individual") == "USA GOVERNMENT"
                return
        assert False, "Instance not found"

    def test_backticked_bigname_escaped_backtick(self):
        """Backticked instance with escaped backtick."""
        facts = parse_cnl('`John ``JJ`` Doe` is a person.')
        assert len(facts) >= 1
        for fact in facts:
            if fact.get("type") == "instance_of":
                assert fact.get("individual") == 'John `JJ` Doe'
                return
        assert False, "Instance not found"


class TestTitleCaseInstances:
    """Test Title-Case instance names (unquoted BIGNAME)."""

    def test_titlecase_basic(self):
        """Basic Title-Case instance."""
        facts = parse_cnl('John is a person.')
        assert len(facts) >= 1
        for fact in facts:
            if fact.get("type") == "instance_of":
                assert fact.get("individual") == "John"
                return
        assert False, "Instance not found"

    def test_titlecase_hyphenated(self):
        """Title-Case instance with hyphens."""
        facts = parse_cnl('New-York is a city.')
        assert len(facts) >= 1
        for fact in facts:
            if fact.get("type") == "instance_of":
                assert fact.get("individual") == "New-York"
                return
        assert False, "Instance not found"


class TestQuotedInRoleAssertions:
    """Test quoted identifiers in role assertions."""

    def test_all_quoted(self):
        """All parts quoted in role assertion."""
        facts = parse_cnl('`John Doe` "is-married-to" `Jane Doe`.')
        assert len(facts) >= 1
        for fact in facts:
            if fact.get("type") == "role_assertion":
                assert fact.get("subject") == "John Doe"
                assert fact.get("role") == "is-married-to"
                assert fact.get("object") == "Jane Doe"
                return
        assert False, "Role assertion not found"

    def test_quoted_subject_only(self):
        """Only subject is quoted."""
        facts = parse_cnl('`New York City` is-located-in USA.')
        assert len(facts) >= 1
        for fact in facts:
            if fact.get("type") == "role_assertion":
                assert fact.get("subject") == "New York City"
                return
        assert False, "Role assertion not found"


class TestQuotedInSWRL:
    """Test quoted identifiers in SWRL rules."""

    def test_quoted_concept_in_swrl(self):
        """Quoted concept in SWRL body."""
        facts = parse_cnl('If a "flying-thing" has-wing a wing then the "flying-thing"(1) is a flyer.')
        assert len(facts) >= 1
        for fact in facts:
            if fact.get("type") == "swrl_rule":
                body = fact.get("body", "")
                head = fact.get("head", "")
                # Check that quotes are stripped in atoms
                assert "flying-thing" in body or "flying-thing" in head
                assert '"' not in body  # No quotes in the rule
                return
        assert False, "SWRL rule not found"


class TestTermsAnnotation:
    """Test that [terms] annotations are stripped from names."""

    def test_name_with_terms(self):
        """Name with [terms] annotation should have annotation stripped."""
        # Note: This depends on lexer supporting NAME with [terms]
        # e.g., "cat [gufo]" should become "cat"
        facts = parse_cnl('Every cat [gufo] is a mammal.')
        assert len(facts) >= 1
        fact = facts[0]
        # The [gufo] should be stripped
        assert fact.get("sub") == "cat"

    def test_quoted_name_with_terms(self):
        """Quoted name followed by [terms] annotation."""
        facts = parse_cnl('Every "domestic-cat" [gufo] is a mammal.')
        assert len(facts) >= 1
        fact = facts[0]
        assert fact.get("sub") == "domestic-cat"


class TestMixedQuoted:
    """Test mixing quoted and unquoted identifiers."""

    def test_quoted_unquoted_subsumption(self):
        """Mix of quoted and unquoted in subsumption."""
        facts = parse_cnl('Every "special-cat" is a mammal.')
        assert len(facts) >= 1
        fact = facts[0]
        assert fact.get("sub") == "special-cat"
        assert fact.get("sup") == "mammal"

    def test_complex_sentence(self):
        """Complex sentence with multiple quoted identifiers."""
        facts = parse_cnl('Every "flying-mammal" that "has-wing" a "bird-wing" is a bat.')
        assert len(facts) >= 1
        # Should parse without errors and strip all quotes


class TestMixedQuoteStyles:
    """Test mixing double-quoted concepts and backtick-quoted instances."""

    def test_backtick_instance_double_role(self):
        """Backticked instance with double-quoted role."""
        facts = parse_cnl('`John Doe` "is-married-to" Mary.')
        assert len(facts) >= 1
        for fact in facts:
            if fact.get("type") == "role_assertion":
                assert fact.get("subject") == "John Doe"
                assert fact.get("role") == "is-married-to"
                return
        assert False, "Role assertion not found"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
