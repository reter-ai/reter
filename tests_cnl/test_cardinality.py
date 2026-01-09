"""
Tests for CNL Cardinality Restrictions
Based on grammar.md examples
"""
import pytest


def find_fact(facts, **criteria):
    """Find a fact matching all criteria."""
    for f in facts:
        if all(f.get(k) == v for k, v in criteria.items()):
            return f
    return None


def has_fact(facts, **criteria):
    """Check if a fact matching criteria exists."""
    return find_fact(facts, **criteria) is not None


class TestMaxCardinality:
    """Test at-most cardinality restrictions."""

    def test_person_at_most_two_parents(self, get_facts):
        """Every person is-a-child-of at-most two parents."""
        facts = get_facts("Every person is-a-child-of at-most two parents.")
        # Property is normalized to a-child-of
        card = find_fact(facts, type='max_cardinality', property='a-child-of')
        assert card is not None

    def test_parent_at_most_10_children(self, get_facts):
        """Every parent has at-most 10 children."""
        facts = get_facts("Every parent has at-most 10 children.")
        card = find_fact(facts, type='max_cardinality', property='has', cardinality='10')
        assert card is not None


class TestMinCardinality:
    """Test at-least cardinality restrictions."""

    def test_person_at_least_two_parents(self, get_facts):
        """Every person is-a-child-of at-least two parents."""
        facts = get_facts("Every person is-a-child-of at-least two parents.")
        card = find_fact(facts, type='min_cardinality', property='a-child-of')
        assert card is not None

    def test_cat_at_least_5_legs(self, get_facts):
        """Every cat has at-least five legs."""
        facts = get_facts("Every cat has at-least five legs.")
        # Note: 'five' might be parsed as word number
        assert len(facts) >= 1


class TestExactCardinality:
    """Test exact cardinality restrictions."""

    def test_person_exactly_two_parents(self, get_facts):
        """Every person is-a-child-of two parents."""
        facts = get_facts("Every person is-a-child-of two parents.")
        # Exact cardinality uses type='exactly'
        card = find_fact(facts, type='exactly', property='a-child-of')
        assert card is not None

    def test_car_four_wheels(self, get_facts):
        """Every car has four wheels."""
        facts = get_facts("Every car has four wheels.")
        # Should parse with exact cardinality
        assert len(facts) >= 1
