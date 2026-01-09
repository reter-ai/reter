"""
Tests for CNL Concept Equivalence
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


class TestConceptEquivalence:
    """Test concept equivalence: Something is X if-and-only-if-it is Y."""

    def test_boy_young_male_man(self, get_facts):
        """Something is a boy if-and-only-if-it is a young-male-man."""
        facts = get_facts("Something is a boy if-and-only-if-it is a young-male-man.")
        eq = find_fact(facts, type='equivalence')
        assert eq is not None

    def test_man_definition(self, get_facts):
        """Something is a man if-and-only-if-it is an adult that is a male and is a person."""
        facts = get_facts("Something is a man if-and-only-if-it is an adult that is a male and is a person.")
        eq = find_fact(facts, type='equivalence')
        assert eq is not None

    def test_young_thing_complement(self, get_facts):
        """Something is a young-thing if-and-only-if-it is not an adult-thing."""
        facts = get_facts("Something is a young-thing if-and-only-if-it is not an adult-thing.")
        # Should create equivalence with complement
        eq = find_fact(facts, type='equivalence')
        assert eq is not None


class TestDisjointConcepts:
    """Test disjoint concepts: No X is a Y."""

    def test_no_man_is_woman(self, get_facts):
        """No man is a woman."""
        facts = get_facts("No man is a woman.")
        disjoint = find_fact(facts, type='alldisjoint_classes')
        assert disjoint is not None

    def test_no_herbivore_is_carnivore(self, get_facts):
        """No herbivore is a carnivore."""
        facts = get_facts("No herbivore is a carnivore.")
        disjoint = find_fact(facts, type='alldisjoint_classes')
        assert disjoint is not None

    def test_no_young_thing_is_adult(self, get_facts):
        """No young-thing is an adult-thing."""
        facts = get_facts("No young-thing is an adult-thing.")
        disjoint = find_fact(facts, type='alldisjoint_classes')
        assert disjoint is not None

    def test_no_cat_is_dog(self, get_facts):
        """No cat is a dog."""
        facts = get_facts("No cat is a dog.")
        disjoint = find_fact(facts, type='alldisjoint_classes')
        assert disjoint is not None


class TestDisjointUnion:
    """Test disjoint union (value partition)."""

    def test_person_disjoint_union(self, get_facts):
        """Something is a person if-and-only-if-it-either is a child, is a young-thing, is a middle-age-thing or is an old-thing."""
        cnl = "Something is a person if-and-only-if-it-either is a child, is a young-thing, is a middle-age-thing or is an old-thing."
        facts = get_facts(cnl)
        du = find_fact(facts, type='disjoint_union')
        assert du is not None

    def test_human_disjoint_union(self, get_facts):
        """Something is a human if-and-only-if-it-either is a child, is an old-man, is a middle-aged-man or is a young-man."""
        cnl = "Something is a human if-and-only-if-it-either is a child, is an old-man, is a middle-aged-man or is a young-man."
        facts = get_facts(cnl)
        du = find_fact(facts, type='disjoint_union')
        assert du is not None
