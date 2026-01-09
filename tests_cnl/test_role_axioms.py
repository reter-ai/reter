"""
Tests for CNL Role Axioms
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


class TestRoleSubsumption:
    """Test role subsumption: If X role Y then X super-role Y."""

    def test_proper_part_of_is_part_of(self, get_facts):
        """If X is-proper-part-of Y then X is-part-of Y."""
        facts = get_facts("If X is-proper-part-of Y then X is-part-of Y.")
        sub = find_fact(facts, type='sub_property')
        assert sub is not None


class TestSymmetricProperty:
    """Test symmetric role: X role Y if-and-only-if Y role X."""

    def test_friend_of_symmetric(self, get_facts):
        """X is-friend-of Y if-and-only-if Y is-friend-of X."""
        facts = get_facts("X is-friend-of Y if-and-only-if Y is-friend-of X.")
        sym = find_fact(facts, type='symmetric_property')
        assert sym is not None

    def test_married_to_symmetric(self, get_facts):
        """X is-married-to Y if-and-only-if Y is-married-to X."""
        facts = get_facts("X is-married-to Y if-and-only-if Y is-married-to X.")
        sym = find_fact(facts, type='symmetric_property')
        assert sym is not None

    def test_sibling_symmetric(self, get_facts):
        """X has-sibling Y if-and-only-if Y has-sibling X."""
        facts = get_facts("X has-sibling Y if-and-only-if Y has-sibling X.")
        sym = find_fact(facts, type='symmetric_property')
        assert sym is not None


class TestAsymmetricProperty:
    """Test asymmetric role: If X role Y then Y does-not role X."""

    def test_parent_of_asymmetric(self, get_facts):
        """If X is-parent-of Y then Y does-not is-parent-of X."""
        facts = get_facts("If X is-parent-of Y then Y does-not is-parent-of X.")
        asym = find_fact(facts, type='asymmetric_property')
        assert asym is not None


class TestPropertyChain:
    """Test property chains (transitivity)."""

    def test_has_part_transitive(self, get_facts):
        """If X has-part something that has-part Y then X has-part Y."""
        facts = get_facts("If X has-part something that has-part Y then X has-part Y.")
        # This should create a property chain or transitive property
        assert len(facts) >= 1

    def test_grandparent_chain(self, get_facts):
        """If X has-parent something that has-parent Y then X has-grandparent Y."""
        facts = get_facts("If X has-parent something that has-parent Y then X has-grandparent Y.")
        chain = find_fact(facts, type='property_chain')
        assert chain is not None


class TestReflexiveProperty:
    """Test reflexive properties: Every-single-thing role itself."""

    def test_part_of_reflexive(self, get_facts):
        """Every-single-thing is-part-of itself."""
        facts = get_facts("Every-single-thing is-part-of itself.")
        has_self = find_fact(facts, type='has_self')
        assert has_self is not None

    def test_likes_itself(self, get_facts):
        """Every man likes itself."""
        facts = get_facts("Every man likes itself.")
        has_self = find_fact(facts, type='has_self')
        assert has_self is not None


class TestIrreflexiveProperty:
    """Test irreflexive properties: Nothing role itself."""

    def test_parent_of_irreflexive(self, get_facts):
        """Nothing is-parent-of itself."""
        facts = get_facts("Nothing is-parent-of itself.")
        # Should create a restriction on has_self
        assert len(facts) >= 1

    def test_proper_part_irreflexive(self, get_facts):
        """Every-single-thing is not a thing that is-proper-part-of itself."""
        facts = get_facts("Every-single-thing is not a thing that is-proper-part-of itself.")
        assert len(facts) >= 1
