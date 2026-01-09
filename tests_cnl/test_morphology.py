"""
Tests for CNL Morphology (singular/plural, verb forms)
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


class TestPluralNouns:
    """Test plural noun normalization."""

    def test_cats_to_cat(self, get_facts):
        """Every lion eats nothing-but cats -> cat."""
        facts = get_facts("Every lion eats nothing-but cats.")
        avf = find_fact(facts, type='all_values_from', filler='cat')
        assert avf is not None

    def test_mice_to_mouse(self, get_facts):
        """Every cat eats nothing-but mice -> mouse."""
        facts = get_facts("Every cat eats nothing-but mice.")
        avf = find_fact(facts, type='all_values_from', filler='mouse')
        assert avf is not None

    def test_children_to_child(self, get_facts):
        """Every parent has at-most 10 children -> child."""
        facts = get_facts("Every parent has at-most 10 children.")
        card = find_fact(facts, type='max_cardinality', filler='child')
        assert card is not None

    def test_persons_to_person(self, get_facts):
        """Every-single-thing is-a-wife-of nothing-but persons -> person."""
        facts = get_facts("Every-single-thing is-a-wife-of nothing-but persons.")
        avf = find_fact(facts, type='all_values_from', filler='person')
        assert avf is not None

    def test_parents_to_parent(self, get_facts):
        """Every person is-a-child-of at-most two parents -> parent."""
        facts = get_facts("Every person is-a-child-of at-most two parents.")
        card = find_fact(facts, type='max_cardinality', filler='parent')
        assert card is not None


class TestVerbForms:
    """Test verb form normalization (3rd person singular to base)."""

    def test_eats_to_eat(self, get_facts):
        """Every cat eats a mouse -> eat."""
        facts = get_facts("Every cat eats a mouse.")
        svf = find_fact(facts, type='some_values_from', property='eat')
        assert svf is not None

    def test_loves_to_love(self, get_facts):
        """Every person loves a cat -> love."""
        facts = get_facts("Every person loves a cat.")
        svf = find_fact(facts, type='some_values_from', property='love')
        assert svf is not None

    def test_has_stays_has(self, get_facts):
        """Every cat has a tail -> has (irregular)."""
        facts = get_facts("Every cat has a tail.")
        svf = find_fact(facts, type='some_values_from', property='has')
        assert svf is not None

    def test_owns_to_own(self, get_facts):
        """John owns Pussy -> own."""
        facts = get_facts("John owns Pussy.")
        ra = find_fact(facts, type='role_assertion', predicate='own')
        assert ra is not None


class TestPastParticiple:
    """Test past participle normalization for passive voice."""

    def test_owned_to_own(self, get_facts):
        """Pussy is owned by John -> own."""
        facts = get_facts("Pussy is owned by John.")
        ra = find_fact(facts, type='role_assertion', predicate='own')
        assert ra is not None

    def test_loved_to_love(self, get_facts):
        """Mary is loved by John -> love."""
        facts = get_facts("Mary is loved by John.")
        ra = find_fact(facts, type='role_assertion', predicate='love')
        assert ra is not None

    def test_eaten_to_eat(self, get_facts):
        """Every tasty-plant is eaten by a carnivore -> eat."""
        facts = get_facts("Every tasty-plant is eaten by a carnivore.")
        svf = find_fact(facts, type='some_values_from', property='eat')
        assert svf is not None

    def test_written_to_write(self, get_facts):
        """Every book is written by an author -> write."""
        facts = get_facts("Every book is written by an author.")
        svf = find_fact(facts, type='some_values_from', property='write')
        assert svf is not None

    def test_driven_to_drive(self, get_facts):
        """Every car is driven by a person -> drive."""
        facts = get_facts("Every car is driven by a person.")
        svf = find_fact(facts, type='some_values_from', property='drive')
        assert svf is not None

    def test_taken_to_take(self, get_facts):
        """Every photo is taken by a photographer -> take."""
        facts = get_facts("Every photo is taken by a photographer.")
        svf = find_fact(facts, type='some_values_from', property='take')
        assert svf is not None
