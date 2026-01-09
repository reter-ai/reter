"""
Tests for CNL Concept Subsumption
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


class TestBasicSubsumption:
    """Test basic concept subsumption: Every X is a Y."""

    def test_simple_subsumption(self, get_facts):
        """Every cat is a mammal."""
        facts = get_facts("Every cat is a mammal.")
        assert has_fact(facts, type='subsumption', sub='cat', sup='mammal')

    def test_tree_is_plant(self, get_facts):
        """Every tree is a plant."""
        facts = get_facts("Every tree is a plant.")
        assert has_fact(facts, type='subsumption', sub='tree', sup='plant')

    def test_giraffe_is_animal(self, get_facts):
        """Every giraffe is an animal."""
        facts = get_facts("Every giraffe is an animal.")
        assert has_fact(facts, type='subsumption', sub='giraffe', sup='animal')

    def test_lion_is_animal(self, get_facts):
        """Every lion is an animal."""
        facts = get_facts("Every lion is an animal.")
        assert has_fact(facts, type='subsumption', sub='lion', sup='animal')


class TestExistentialRestriction:
    """Test existential restrictions: Every X role a Y."""

    def test_branch_part_of_tree(self, get_facts):
        """Every branch is-part-of a tree."""
        facts = get_facts("Every branch is-part-of a tree.")
        # Should create subsumption with some_values_from
        assert len(facts) >= 1
        svf = find_fact(facts, type='some_values_from', property='part-of', filler='tree')
        assert svf is not None

    def test_giraffe_eats_plant(self, get_facts):
        """Every giraffe eats a plant."""
        facts = get_facts("Every giraffe eats a plant.")
        svf = find_fact(facts, type='some_values_from', property='eat', filler='plant')
        assert svf is not None


class TestUniversalRestriction:
    """Test universal restrictions: Every X role nothing-but Y."""

    def test_lion_eats_herbivore(self, get_facts):
        """Every lion eats nothing-but herbivore."""
        facts = get_facts("Every lion eats nothing-but herbivore.")
        avf = find_fact(facts, type='all_values_from', property='eat', filler='herbivore')
        assert avf is not None

    def test_wife_of_persons(self, get_facts):
        """Every-single-thing is-a-wife-of nothing-but persons."""
        facts = get_facts("Every-single-thing is-a-wife-of nothing-but persons.")
        avf = find_fact(facts, type='all_values_from', property='a-wife-of', filler='person')
        assert avf is not None


class TestComplexExpressions:
    """Test complex concept expressions with that-clauses."""

    def test_cat_with_that_clause(self, get_facts):
        """Every cat that is a brown-one has a red-eye."""
        facts = get_facts("Every cat that is a brown-one has a red-eye.")
        # Should create intersection and some_values_from
        assert len(facts) >= 1

    def test_palm_tree_with_complement(self, get_facts):
        """Every palm-tree has-part something that is not a branch."""
        facts = get_facts("Every palm-tree has-part something that is not a branch.")
        # Should have complement fact
        complement = find_fact(facts, type='complement', **{'class': 'branch'})
        assert complement is not None


class TestUnionAndIntersection:
    """Test union and intersection of concepts."""

    def test_union_with_andor(self, get_facts):
        """Every giraffe eats nothing-but thing that is a leaf and-or is a twig."""
        facts = get_facts("Every giraffe eats nothing-but thing that is a leaf and-or is a twig.")
        union = find_fact(facts, type='union')
        assert union is not None

    def test_intersection_with_and(self, get_facts):
        """Every tasty-plant is eaten by a carnivore and is eaten by a herbivore."""
        facts = get_facts("Every tasty-plant is eaten by a carnivore and is eaten by a herbivore.")
        # Should create intersection
        assert len(facts) >= 1
