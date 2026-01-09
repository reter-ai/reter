"""Test quoted identifiers in CNL.

CNL supports quoted identifiers for concepts, roles, and instances:
- "concept-name" - quoted concept/role NAME
- The-"Instance Name" - quoted BIGNAME instance
- THE-"CONSTANT" - quoted VERYBIGNAME constant

Quotes allow arbitrary characters including spaces, reserved words, and special chars.
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
    """Test quoted concept names (NAME token with quotes)."""

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
        facts = parse_cnl('John "is friend of" Mary.')
        assert len(facts) >= 1
        # Check that a role_assertion was created with unquoted role
        for fact in facts:
            if fact.get("type") == "role_assertion":
                # The field is 'predicate' not 'role'
                assert fact.get("predicate") == "is friend of"
                return
        assert False, "Role assertion not found"

    def test_quoted_data_property(self):
        """Quoted data property name."""
        facts = parse_cnl('John "has-age" equal-to 30.')
        assert len(facts) >= 1
        for fact in facts:
            if fact.get("type") == "data_assertion":
                assert fact.get("property") == "has-age"
                return
        assert False, "Data assertion not found"


class TestQuotedInstances:
    """Test quoted instance names (BIGNAME with The-"..." prefix)."""

    def test_quoted_bigname_basic(self):
        """Basic quoted BIGNAME instance."""
        facts = parse_cnl('The-"Eiffel Tower" is a landmark.')
        assert len(facts) >= 1
        for fact in facts:
            if fact.get("type") == "instance_of":
                assert fact.get("individual") == "Eiffel Tower"
                return
        assert False, "Instance not found"

    def test_quoted_bigname_with_spaces(self):
        """Quoted instance with multiple spaces."""
        facts = parse_cnl('The-"United Nations Building" is a headquarters.')
        assert len(facts) >= 1
        for fact in facts:
            if fact.get("type") == "instance_of":
                assert fact.get("individual") == "United Nations Building"
                return
        assert False, "Instance not found"

    def test_quoted_verybigname_basic(self):
        """Basic quoted VERYBIGNAME constant."""
        facts = parse_cnl('THE-"USA GOVERNMENT" is an organization.')
        assert len(facts) >= 1
        for fact in facts:
            if fact.get("type") == "instance_of":
                assert fact.get("individual") == "USA GOVERNMENT"
                return
        assert False, "Instance not found"

    def test_quoted_bigname_escaped_quote(self):
        """Quoted instance with escaped quote."""
        facts = parse_cnl('The-"John ""Johnny"" Doe" is a person.')
        assert len(facts) >= 1
        for fact in facts:
            if fact.get("type") == "instance_of":
                assert fact.get("individual") == 'John "Johnny" Doe'
                return
        assert False, "Instance not found"


class TestQuotedInRoleAssertions:
    """Test quoted identifiers in role assertions."""

    def test_all_quoted(self):
        """All parts quoted in role assertion."""
        facts = parse_cnl('The-"John Doe" "is-married-to" The-"Jane Doe".')
        assert len(facts) >= 1
        for fact in facts:
            if fact.get("type") == "role_assertion":
                assert fact.get("subject") == "John Doe"
                assert fact.get("predicate") == "is-married-to"  # Field is 'predicate' not 'role'
                assert fact.get("object") == "Jane Doe"
                return
        assert False, "Role assertion not found"

    def test_quoted_subject_only(self):
        """Only subject is quoted."""
        facts = parse_cnl('The-"New York City" is-located-in USA.')
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


class TestBacktickedConcepts:
    """Test backtick-quoted concept names (`...` syntax)."""

    def test_backticked_concept_basic(self):
        """Basic backticked concept name."""
        facts = parse_cnl('Every `my-concept` is a mammal.')
        assert len(facts) >= 1
        fact = facts[0]
        assert fact.get("sub") == "my-concept"
        assert fact.get("sup") == "mammal"

    def test_backticked_concept_with_spaces(self):
        """Backticked concept with spaces."""
        facts = parse_cnl('Every `flying cat` is a mammal.')
        assert len(facts) >= 1
        fact = facts[0]
        assert fact.get("sub") == "flying cat"

    def test_backticked_concept_reserved_word(self):
        """Backticked concept using a reserved word."""
        facts = parse_cnl('Every `value` is a `thing`.')
        assert len(facts) >= 1
        fact = facts[0]
        assert fact.get("sub") == "value"
        assert fact.get("sup") == "thing"

    def test_backticked_concept_escaped_backtick(self):
        """Backticked concept with escaped backtick (``)."""
        facts = parse_cnl('Every `say ``hello``` is a greeting.')
        assert len(facts) >= 1
        fact = facts[0]
        assert fact.get("sub") == 'say `hello`'


class TestBacktickedInstances:
    """Test backtick-quoted instance names (The-`...` syntax)."""

    def test_backticked_bigname_basic(self):
        """Basic backticked BIGNAME instance."""
        facts = parse_cnl('The-`Eiffel Tower` is a landmark.')
        assert len(facts) >= 1
        for fact in facts:
            if fact.get("type") == "instance_of":
                assert fact.get("individual") == "Eiffel Tower"
                return
        assert False, "Instance not found"

    def test_backticked_bigname_with_spaces(self):
        """Backticked instance with multiple spaces."""
        facts = parse_cnl('The-`United Nations Building` is a headquarters.')
        assert len(facts) >= 1
        for fact in facts:
            if fact.get("type") == "instance_of":
                assert fact.get("individual") == "United Nations Building"
                return
        assert False, "Instance not found"

    def test_backticked_verybigname_basic(self):
        """Basic backticked VERYBIGNAME constant."""
        facts = parse_cnl('THE-`USA GOVERNMENT` is an organization.')
        assert len(facts) >= 1
        for fact in facts:
            if fact.get("type") == "instance_of":
                assert fact.get("individual") == "USA GOVERNMENT"
                return
        assert False, "Instance not found"

    def test_backticked_bigname_escaped_backtick(self):
        """Backticked instance with escaped backtick."""
        facts = parse_cnl('The-`John ``JJ`` Doe` is a person.')
        assert len(facts) >= 1
        for fact in facts:
            if fact.get("type") == "instance_of":
                assert fact.get("individual") == 'John `JJ` Doe'
                return
        assert False, "Instance not found"


class TestBacktickedRoles:
    """Test backtick-quoted role/property names."""

    def test_backticked_role_basic(self):
        """Basic backticked role name."""
        facts = parse_cnl('Every person `is-related-to` a person.')
        assert len(facts) >= 1
        for fact in facts:
            if fact.get("type") == "some_values_from":
                role = fact.get("property")
                if role == "is-related-to":
                    return
        assert False, f"Role 'is-related-to' not found in facts: {facts}"

    def test_backticked_role_with_spaces(self):
        """Backticked role with spaces."""
        facts = parse_cnl('John `is friend of` Mary.')
        assert len(facts) >= 1
        for fact in facts:
            if fact.get("type") == "role_assertion":
                assert fact.get("predicate") == "is friend of"
                return
        assert False, "Role assertion not found"

    def test_backticked_data_property(self):
        """Backticked data property name."""
        facts = parse_cnl('John `has-age` equal-to 30.')
        assert len(facts) >= 1
        for fact in facts:
            if fact.get("type") == "data_assertion":
                assert fact.get("property") == "has-age"
                return
        assert False, "Data assertion not found"


class TestMixedQuoteStyles:
    """Test mixing double-quoted and backtick-quoted identifiers."""

    def test_double_and_backtick_mixed(self):
        """Mix of double quotes and backticks in same sentence."""
        facts = parse_cnl('Every `special-cat` is a "mammal".')
        assert len(facts) >= 1
        fact = facts[0]
        assert fact.get("sub") == "special-cat"
        assert fact.get("sup") == "mammal"

    def test_backtick_instance_double_role(self):
        """Backticked instance with double-quoted role."""
        facts = parse_cnl('The-`John Doe` "is-married-to" Mary.')
        assert len(facts) >= 1
        for fact in facts:
            if fact.get("type") == "role_assertion":
                assert fact.get("subject") == "John Doe"
                assert fact.get("predicate") == "is-married-to"
                return
        assert False, "Role assertion not found"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
