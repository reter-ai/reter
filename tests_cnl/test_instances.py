"""
Tests for CNL Instance Assertions
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


class TestInstanceOf:
    """Test instance assertions: X is a Y."""

    def test_sophie_is_giraffe(self, get_facts):
        """Sophie is a giraffe."""
        facts = get_facts("Sophie is a giraffe.")
        assert has_fact(facts, type='instance_of', individual='Sophie', concept='giraffe')

    def test_leo_is_lion(self, get_facts):
        """Leo is a lion."""
        facts = get_facts("Leo is a lion.")
        assert has_fact(facts, type='instance_of', individual='Leo', concept='lion')

    def test_john_is_person(self, get_facts):
        """John is a person."""
        facts = get_facts("John is a person.")
        assert has_fact(facts, type='instance_of', individual='John', concept='person')

    def test_tom_is_man(self, get_facts):
        """Tom is a man."""
        facts = get_facts("Tom is a man.")
        assert has_fact(facts, type='instance_of', individual='Tom', concept='man')

    def test_mark_is_man(self, get_facts):
        """Mark is a man."""
        facts = get_facts("Mark is a man.")
        assert has_fact(facts, type='instance_of', individual='Mark', concept='man')


class TestRoleAssertions:
    """Test role assertions between instances."""

    def test_john_owns_pussy(self, get_facts):
        """John owns Pussy."""
        facts = get_facts("John owns Pussy.")
        assert has_fact(facts, type='role_assertion', subject='John', predicate='own', object='Pussy')

    def test_john_loves_mary(self, get_facts):
        """John loves Mary."""
        facts = get_facts("John loves Mary.")
        assert has_fact(facts, type='role_assertion', subject='John', predicate='love', object='Mary')

    def test_tom_loves_mary(self, get_facts):
        """Tom loves Mary."""
        facts = get_facts("Tom loves Mary.")
        assert has_fact(facts, type='role_assertion', subject='Tom', predicate='love', object='Mary')

    def test_john_is_married_to_mary(self, get_facts):
        """John is-married-to Mary."""
        facts = get_facts("John is-married-to Mary.")
        assert has_fact(facts, type='role_assertion', subject='John', predicate='married-to', object='Mary')


class TestPassiveVoice:
    """Test passive voice role assertions."""

    def test_passive_owned_by(self, get_facts):
        """Pussy is owned by John."""
        facts = get_facts("Pussy is owned by John.")
        # Should produce same as active voice
        assert has_fact(facts, type='role_assertion', subject='John', predicate='own', object='Pussy')

    def test_passive_loved_by(self, get_facts):
        """Mary is loved by John."""
        facts = get_facts("Mary is loved by John.")
        # Should produce same as active voice
        assert has_fact(facts, type='role_assertion', subject='John', predicate='love', object='Mary')

    def test_passive_loved_by_tom(self, get_facts):
        """Mary is loved by Tom."""
        facts = get_facts("Mary is loved by Tom.")
        assert has_fact(facts, type='role_assertion', subject='Tom', predicate='love', object='Mary')


class TestActivePassiveEquivalence:
    """Test that active and passive voice produce equivalent facts."""

    def test_owns_equivalence(self, get_facts):
        """John owns Pussy = Pussy is owned by John."""
        facts_active = get_facts("John owns Pussy.")
        facts_passive = get_facts("Pussy is owned by John.")

        # Both should produce exactly one role_assertion
        active = find_fact(facts_active, type='role_assertion')
        passive = find_fact(facts_passive, type='role_assertion')

        assert active is not None
        assert passive is not None
        assert active['subject'] == passive['subject']
        assert active['predicate'] == passive['predicate']
        assert active['object'] == passive['object']

    def test_loves_equivalence(self, get_facts):
        """John loves Mary = Mary is loved by John."""
        facts_active = get_facts("John loves Mary.")
        facts_passive = get_facts("Mary is loved by John.")

        active = find_fact(facts_active, type='role_assertion')
        passive = find_fact(facts_passive, type='role_assertion')

        assert active is not None
        assert passive is not None
        assert active['subject'] == passive['subject']
        assert active['predicate'] == passive['predicate']
        assert active['object'] == passive['object']
