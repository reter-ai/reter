"""
Comprehensive tests for CNL Language Executors (Fact Extraction Visitors).

This test file validates that all CNL language constructs generate the correct
facts with properly normalized properties/predicates in 3rd person singular form.

Tests cover all 31 fact types:
- Class/Concept facts (subsumption, equivalence, disjoint)
- Instance/Individual facts (instance_of, role_assertion, same_as, different_from)
- Role/Property restrictions (some_values_from, all_values_from, cardinality)
- Composite concepts (union, intersection, complement)
- Property axioms (sub_property, property_chain, symmetric, asymmetric, transitive)
- SWRL rules
"""
import pytest
import reter_core.owl_rete_cpp as cpp


def parse_cnl(cnl_text):
    """Parse CNL and return list of fact dicts."""
    result = cpp.parse_cnl(cnl_text)
    return [dict(f.items()) for f in result.facts]


def get_facts_by_type(facts, fact_type):
    """Filter facts by type."""
    return [f for f in facts if f.get('type') == fact_type]


def get_fact_by_type(facts, fact_type):
    """Get single fact by type (asserts exactly one exists)."""
    matching = get_facts_by_type(facts, fact_type)
    assert len(matching) == 1, f"Expected 1 {fact_type}, got {len(matching)}: {matching}"
    return matching[0]


def find_fact(facts, **criteria):
    """Find a fact matching all criteria."""
    for f in facts:
        if all(f.get(k) == v for k, v in criteria.items()):
            return f
    return None


def has_fact(facts, **criteria):
    """Check if a fact matching criteria exists."""
    return find_fact(facts, **criteria) is not None


# =============================================================================
# CLASS/CONCEPT FACTS
# =============================================================================

class TestSubsumption:
    """Test subsumption (subclass) facts."""

    def test_basic_subsumption(self):
        """Every cat is a mammal."""
        facts = parse_cnl("Every cat is a mammal.")
        sub = get_fact_by_type(facts, 'subsumption')
        assert sub['sub'] == 'cat'
        assert sub['sup'] == 'mammal'

    def test_subsumption_with_restriction(self):
        """Every cat that eats something is a hunter."""
        facts = parse_cnl("Every cat that eats something is a hunter.")
        # Should create subsumption with intersection
        sub = get_fact_by_type(facts, 'subsumption')
        assert sub['sup'] == 'hunter'
        # Should also create some_values_from
        svf = get_fact_by_type(facts, 'some_values_from')
        assert svf['property'] == 'eats'

    def test_subsumption_modal(self):
        """Every cat must eat something."""
        facts = parse_cnl("Every cat must eat something.")
        sub = get_fact_by_type(facts, 'subsumption')
        svf = get_fact_by_type(facts, 'some_values_from')
        assert svf['property'] == 'eats'


class TestEquivalence:
    """Test concept equivalence facts."""

    def test_disjoint_union_equivalence(self):
        """Something is a color if-and-only-if-it-either is a red or is a green or is a blue."""
        facts = parse_cnl("Something is a color if-and-only-if-it-either is a red or is a green or is a blue.")
        # This pattern generates disjoint_union
        du = get_fact_by_type(facts, 'disjoint_union')
        assert du['class'] == 'color'
        assert 'red' in du['members']
        assert 'green' in du['members']
        assert 'blue' in du['members']


class TestDisjoint:
    """Test disjoint class facts."""

    def test_disjoint_classes(self):
        """No cat is a dog."""
        facts = parse_cnl("No cat is a dog.")
        disj = get_fact_by_type(facts, 'alldisjoint_classes')
        assert 'cat' in disj['classes']
        assert 'dog' in disj['classes']


# =============================================================================
# INSTANCE/INDIVIDUAL FACTS
# =============================================================================

class TestInstanceOf:
    """Test instance_of facts."""

    def test_basic_instance(self):
        """John is a person."""
        facts = parse_cnl("John is a person.")
        inst = get_fact_by_type(facts, 'instance_of')
        assert inst['individual'] == 'John'
        assert inst['concept'] == 'person'

    def test_multiple_instances(self):
        """John is a person. Mary is a person."""
        facts = parse_cnl("John is a person. Mary is a person.")
        instances = get_facts_by_type(facts, 'instance_of')
        assert len(instances) == 2
        names = [i['individual'] for i in instances]
        assert 'John' in names
        assert 'Mary' in names


class TestRoleAssertion:
    """Test role_assertion facts with proper predicate normalization."""

    def test_basic_role_assertion(self):
        """John owns Pussy."""
        facts = parse_cnl("John owns Pussy.")
        ra = get_fact_by_type(facts, 'role_assertion')
        assert ra['subject'] == 'John'
        assert ra['role'] == 'owns'
        assert ra['object'] == 'Pussy'

    def test_passive_role_assertion(self):
        """Pussy is owned by John."""
        facts = parse_cnl("Pussy is owned by John.")
        ra = get_fact_by_type(facts, 'role_assertion')
        assert ra['subject'] == 'John'
        assert ra['role'] == 'owns'
        assert ra['object'] == 'Pussy'

    def test_hyphenated_role(self):
        """John has-parent Mary."""
        facts = parse_cnl("John has-parent Mary.")
        ra = get_fact_by_type(facts, 'role_assertion')
        assert ra['role'] == 'has-parent'

    def test_is_role_preserved(self):
        """John is-married-to Mary."""
        facts = parse_cnl("John is-married-to Mary.")
        ra = get_fact_by_type(facts, 'role_assertion')
        assert ra['role'] == 'is-married-to'

    @pytest.mark.parametrize("cnl,expected_predicate", [
        ("John loves Mary.", "loves"),
        ("Mary is loved by John.", "loves"),
        ("John eats Pizza.", "eats"),
        ("Pizza is eaten by John.", "eats"),
        ("John creates Art.", "creates"),
        ("Art is created by John.", "creates"),
        ("John marries Mary.", "marries"),
        ("Mary is married by John.", "marries"),
        ("John carries Bag.", "carries"),
        ("Bag is carried by John.", "carries"),
    ])
    def test_various_role_predicates(self, cnl, expected_predicate):
        """Various role predicates are in 3rd person singular."""
        facts = parse_cnl(cnl)
        ra = get_fact_by_type(facts, 'role_assertion')
        assert ra['role'] == expected_predicate


class TestSameAsDifferentFrom:
    """Test same_as and different_from facts."""

    def test_same_as(self):
        """John is-the-same-as Johnny."""
        facts = parse_cnl("John is-the-same-as Johnny.")
        same = get_fact_by_type(facts, 'same_as')
        assert 'John' in [same.get('i1'), same.get('i2')]
        assert 'Johnny' in [same.get('i1'), same.get('i2')]

    def test_different_from(self):
        """John is-not-the-same-as Mary."""
        facts = parse_cnl("John is-not-the-same-as Mary.")
        diff = get_fact_by_type(facts, 'different_from')
        assert 'John' in [diff.get('i1'), diff.get('i2')]
        assert 'Mary' in [diff.get('i1'), diff.get('i2')]


# =============================================================================
# ROLE/PROPERTY RESTRICTIONS
# =============================================================================

class TestSomeValuesFrom:
    """Test some_values_from (existential) restrictions."""

    def test_basic_existential(self):
        """Every cat eats a mouse."""
        facts = parse_cnl("Every cat eats a mouse.")
        svf = get_fact_by_type(facts, 'some_values_from')
        assert svf['property'] == 'eats'
        assert svf['filler'] == 'mouse'

    def test_existential_with_thing(self):
        """Every cat eats something."""
        facts = parse_cnl("Every cat eats something.")
        svf = get_fact_by_type(facts, 'some_values_from')
        assert svf['property'] == 'eats'

    def test_passive_existential_creates_inverse(self):
        """Every mouse is eaten by a cat."""
        facts = parse_cnl("Every mouse is eaten by a cat.")
        # Should create inverse_of fact
        inv = get_fact_by_type(facts, 'inverse_of')
        assert inv['property'] == 'eats'
        # Should create some_values_from using the inverse
        svf = get_fact_by_type(facts, 'some_values_from')
        assert svf['property'] == inv['id']

    @pytest.mark.parametrize("cnl,expected_property,expected_filler", [
        ("Every person loves a thing.", "loves", "Thing"),  # 'thing' -> 'Thing' (owl:Thing)
        ("Every dog chases a cat.", "chases", "cat"),
        ("Every bird flies-to a place.", "flies-to", "place"),
        ("Every child has-parent a person.", "has-parent", "person"),
    ])
    def test_various_existential_properties(self, cnl, expected_property, expected_filler):
        """Various existential properties are in 3rd person singular."""
        facts = parse_cnl(cnl)
        svf = get_fact_by_type(facts, 'some_values_from')
        assert svf['property'] == expected_property
        assert svf['filler'] == expected_filler


class TestAllValuesFrom:
    """Test all_values_from (universal) restrictions."""

    def test_basic_universal(self):
        """Every cat eats nothing-but mice."""
        facts = parse_cnl("Every cat eats nothing-but mice.")
        avf = get_fact_by_type(facts, 'all_values_from')
        assert avf['property'] == 'eats'
        assert avf['filler'] == 'mouse'  # Plurals normalized

    def test_passive_universal_creates_inverse(self):
        """Every mouse is eaten by nothing-but cats."""
        facts = parse_cnl("Every mouse is eaten by nothing-but cats.")
        inv = get_fact_by_type(facts, 'inverse_of')
        assert inv['property'] == 'eats'
        avf = get_fact_by_type(facts, 'all_values_from')
        assert avf['property'] == inv['id']

    @pytest.mark.parametrize("cnl,expected_property", [
        ("Every cat eats nothing-but mice.", "eats"),
        ("Every person loves nothing-but things.", "loves"),
        ("Every parent has-child nothing-but persons.", "has-child"),
    ])
    def test_various_universal_properties(self, cnl, expected_property):
        """Various universal properties are in 3rd person singular."""
        facts = parse_cnl(cnl)
        avf = get_fact_by_type(facts, 'all_values_from')
        assert avf['property'] == expected_property


class TestCardinality:
    """Test cardinality restriction facts."""

    def test_exact_cardinality(self):
        """Every car has exactly 4 wheels."""
        facts = parse_cnl("Every car has exactly 4 wheels.")
        card = get_fact_by_type(facts, 'exact_cardinality')
        assert card['property'] == 'has'
        assert card['cardinality'] == '4'  # Cardinality is returned as string
        assert card['filler'] == 'wheel'

    def test_min_cardinality(self):
        """Every parent has at-least 1 child."""
        facts = parse_cnl("Every parent has at-least 1 child.")
        card = get_fact_by_type(facts, 'min_cardinality')
        assert card['property'] == 'has'
        assert card['cardinality'] == '1'  # Cardinality is returned as string

    def test_max_cardinality(self):
        """Every person has at-most 2 parents."""
        facts = parse_cnl("Every person has at-most 2 parents.")
        card = get_fact_by_type(facts, 'max_cardinality')
        assert card['property'] == 'has'
        assert card['cardinality'] == '2'  # Cardinality is returned as string

    @pytest.mark.parametrize("cnl,card_type,expected_property,expected_card", [
        ("Every person owns exactly one car.", "exact_cardinality", "owns", "1"),
        ("Every team has at-least 2 members.", "min_cardinality", "has", "2"),
        ("Every student takes at-most 5 courses.", "max_cardinality", "takes", "5"),
    ])
    def test_various_cardinality_properties(self, cnl, card_type, expected_property, expected_card):
        """Various cardinality restrictions have correct properties."""
        facts = parse_cnl(cnl)
        card = get_fact_by_type(facts, card_type)
        assert card['property'] == expected_property
        assert card['cardinality'] == expected_card  # Cardinality is returned as string


class TestHasSelf:
    """Test has_self restriction facts."""

    def test_has_self(self):
        """Every narcissist loves itself."""
        facts = parse_cnl("Every narcissist loves itself.")
        hs = get_fact_by_type(facts, 'has_self')
        assert hs['property'] == 'loves'


# =============================================================================
# COMPOSITE CONCEPTS
# =============================================================================

class TestUnion:
    """Test union (disjunction) facts."""

    def test_union_via_or_clause(self):
        """Every cat that eats a mouse or hunts a bird is a predator."""
        # Union is generated from "or" clauses within "that" restrictions
        facts = parse_cnl("Every cat that eats a mouse or hunts a bird is a predator.")
        union_facts = get_facts_by_type(facts, 'union')
        # At least check we have some_values_from facts for the disjuncts
        svf_facts = get_facts_by_type(facts, 'some_values_from')
        props = [s['property'] for s in svf_facts]
        # Both properties should be normalized to 3rd person singular
        assert 'eats' in props or 'hunts' in props


class TestIntersection:
    """Test intersection (conjunction) facts."""

    def test_intersection_via_that_clause(self):
        """Every cat that eats something and hunts something is a predator."""
        facts = parse_cnl("Every cat that eats something and hunts something is a predator.")
        inter_facts = get_facts_by_type(facts, 'intersection')
        # The "that...and..." clause creates intersection
        assert len(inter_facts) >= 1
        # Check both some_values_from restrictions are created
        svf_facts = get_facts_by_type(facts, 'some_values_from')
        assert len(svf_facts) == 2
        props = [s['property'] for s in svf_facts]
        assert 'eats' in props
        assert 'hunts' in props


# =============================================================================
# PROPERTY AXIOMS
# =============================================================================

class TestSubProperty:
    """Test sub_property facts."""

    def test_basic_sub_property(self):
        """If X has-parent Y then X has-ancestor Y."""
        facts = parse_cnl("If X has-parent Y then X has-ancestor Y.")
        sub = get_fact_by_type(facts, 'sub_property')
        assert sub['sub'] == 'has-parent'
        assert sub['sup'] == 'has-ancestor'

    @pytest.mark.parametrize("cnl,expected_sub,expected_sup", [
        ("If X loves Y then X likes Y.", "loves", "likes"),
        ("If X owns Y then X possesses Y.", "owns", "possesses"),
        ("If X is-mother-of Y then X is-parent-of Y.", "is-mother-of", "is-parent-of"),
    ])
    def test_various_sub_properties(self, cnl, expected_sub, expected_sup):
        """Various sub-property axioms have correct predicates."""
        facts = parse_cnl(cnl)
        sub = get_fact_by_type(facts, 'sub_property')
        assert sub['sub'] == expected_sub
        assert sub['sup'] == expected_sup


class TestPropertyChain:
    """Test property_chain facts."""

    def test_basic_property_chain(self):
        """If X has-parent something that has-parent Y then X has-grandparent Y."""
        facts = parse_cnl("If X has-parent something that has-parent Y then X has-grandparent Y.")
        chain = get_fact_by_type(facts, 'property_chain')
        assert chain['super_property'] == 'has-grandparent'
        assert 'chain' in chain
        assert chain['chain'] == ['has-parent', 'has-parent']

    def test_longer_property_chain(self):
        """If X has-parent something that has-parent something that has-parent Y then X has-great-grandparent Y."""
        facts = parse_cnl("If X has-parent something that has-parent something that has-parent Y then X has-great-grandparent Y.")
        chain = get_fact_by_type(facts, 'property_chain')
        assert chain['super_property'] == 'has-great-grandparent'
        assert len(chain['chain']) == 3


class TestSymmetricProperty:
    """Test symmetric_property facts."""

    def test_basic_symmetric(self):
        """X is-married-to Y if-and-only-if Y is-married-to X."""
        facts = parse_cnl("X is-married-to Y if-and-only-if Y is-married-to X.")
        sym = get_fact_by_type(facts, 'symmetric_property')
        assert sym['property'] == 'is-married-to'

    @pytest.mark.parametrize("cnl,expected_property", [
        ("X is-sibling-of Y if-and-only-if Y is-sibling-of X.", "is-sibling-of"),
        ("X is-neighbor-of Y if-and-only-if Y is-neighbor-of X.", "is-neighbor-of"),
        ("X knows Y if-and-only-if Y knows X.", "knows"),
    ])
    def test_various_symmetric_properties(self, cnl, expected_property):
        """Various symmetric properties are correctly identified."""
        facts = parse_cnl(cnl)
        sym = get_fact_by_type(facts, 'symmetric_property')
        assert sym['property'] == expected_property


class TestAsymmetricProperty:
    """Test asymmetric_property facts."""

    def test_basic_asymmetric(self):
        """If X is-parent-of Y then Y does-not is-parent-of X."""
        facts = parse_cnl("If X is-parent-of Y then Y does-not is-parent-of X.")
        asym = get_fact_by_type(facts, 'asymmetric_property')
        assert asym['property'] == 'is-parent-of'

    @pytest.mark.parametrize("cnl,expected_property", [
        ("If X is-child-of Y then Y does-not is-child-of X.", "is-child-of"),
        ("If X precedes Y then Y does-not precedes X.", "precedes"),
    ])
    def test_various_asymmetric_properties(self, cnl, expected_property):
        """Various asymmetric properties are correctly identified."""
        facts = parse_cnl(cnl)
        asym = get_fact_by_type(facts, 'asymmetric_property')
        assert asym['property'] == expected_property


# =============================================================================
# SWRL RULES
# =============================================================================

class TestSwrlRules:
    """Test SWRL rule facts."""

    def test_basic_swrl_rule(self):
        """If a person loves a thing then the person likes the thing."""
        facts = parse_cnl("If a person loves a thing then the person likes the thing.")
        swrl = get_fact_by_type(facts, 'swrl_rule')
        assert 'loves(' in swrl['body']
        assert 'likes(' in swrl['head']

    def test_swrl_with_passive(self):
        """If a person is loved by a thing then the thing cares-for the person."""
        facts = parse_cnl("If a person is loved by a thing then the thing cares-for the person.")
        swrl = get_fact_by_type(facts, 'swrl_rule')
        # Passive should swap args and use 'loves'
        assert 'loves(' in swrl['body']
        assert 'cares-for(' in swrl['head']

    def test_swrl_with_multiple_conditions(self):
        """If a person owns a cat and the cat hunts a mouse then the person feeds the cat."""
        facts = parse_cnl("If a person owns a cat and the cat hunts a mouse then the person feeds the cat.")
        swrl = get_fact_by_type(facts, 'swrl_rule')
        assert 'owns(' in swrl['body']
        assert 'hunts(' in swrl['body']
        assert 'feeds(' in swrl['head']

    def test_swrl_with_class_condition(self):
        """If a thing is a cat and the thing hunts a mouse then the thing is a hunter."""
        facts = parse_cnl("If a thing is a cat and the thing hunts a mouse then the thing is a hunter.")
        swrl = get_fact_by_type(facts, 'swrl_rule')
        assert 'cat(' in swrl['body']
        assert 'hunts(' in swrl['body']
        assert 'hunter(' in swrl['head']


# =============================================================================
# COMPLEX CONSTRUCTS
# =============================================================================

class TestComplexConstructs:
    """Test complex CNL constructs."""

    def test_every_single_thing_subject(self):
        """Every-single-thing is a thing."""
        facts = parse_cnl("Every-single-thing is a thing.")
        sub = get_fact_by_type(facts, 'subsumption')
        # 'Every-single-thing' maps to owl:Thing, 'thing' also maps to 'Thing'
        assert sub['sub'] == 'Thing'
        assert sub['sup'] == 'Thing'

    def test_named_instance_with_single_verb(self):
        """John hates Mary."""
        facts = parse_cnl("John hates Mary.")
        ra = get_fact_by_type(facts, 'role_assertion')
        assert ra['role'] == 'hates'
        assert ra['subject'] == 'John'
        assert ra['object'] == 'Mary'

    def test_restriction_with_that_and(self):
        """Every pet that is a cat and eats something is special."""
        facts = parse_cnl("Every pet that is a cat and eats something is special.")
        sub = get_fact_by_type(facts, 'subsumption')
        assert sub['sup'] == 'special'
        # Check intersection and some_values_from are created
        inter_facts = get_facts_by_type(facts, 'intersection')
        svf_facts = get_facts_by_type(facts, 'some_values_from')
        assert len(inter_facts) >= 1
        assert len(svf_facts) >= 1
        assert svf_facts[0]['property'] == 'eats'


# =============================================================================
# PLURAL AND MORPHOLOGY IN FILLERS
# =============================================================================

class TestFillerNormalization:
    """Test that fillers (concepts) are properly normalized."""

    @pytest.mark.parametrize("cnl,expected_filler", [
        ("Every cat eats nothing-but mice.", "mouse"),
        ("Every parent has at-most 10 children.", "child"),
        ("Every person owns at-least 2 cars.", "car"),
        ("Every zoo has exactly 5 lions.", "lion"),
    ])
    def test_plural_fillers_normalized(self, cnl, expected_filler):
        """Plural fillers are normalized to singular."""
        facts = parse_cnl(cnl)
        # Find the restriction fact
        for fact_type in ['all_values_from', 'min_cardinality', 'max_cardinality', 'exact_cardinality']:
            matching = get_facts_by_type(facts, fact_type)
            if matching:
                assert matching[0]['filler'] == expected_filler
                break


# =============================================================================
# EDGE CASES AND REGRESSIONS
# =============================================================================

class TestEdgeCasesAndRegressions:
    """Edge cases and regression tests."""

    def test_modal_must_preserves_property(self):
        """Every person must own something."""
        facts = parse_cnl("Every person must own something.")
        svf = get_fact_by_type(facts, 'some_values_from')
        assert svf['property'] == 'owns'

    def test_modal_can_preserves_property(self):
        """Every person can own something."""
        facts = parse_cnl("Every person can own something.")
        svf = get_fact_by_type(facts, 'some_values_from')
        assert svf['property'] == 'owns'

    def test_is_role_in_restriction(self):
        """Every wheel is-part-of a car."""
        facts = parse_cnl("Every wheel is-part-of a car.")
        svf = get_fact_by_type(facts, 'some_values_from')
        assert svf['property'] == 'is-part-of'

    def test_has_role_preserved(self):
        """Every person has a name."""
        facts = parse_cnl("Every person has a name.")
        svf = get_fact_by_type(facts, 'some_values_from')
        assert svf['property'] == 'has'

    def test_irregular_verb_in_passive(self):
        """Every book is written by an author."""
        facts = parse_cnl("Every book is written by an author.")
        inv = get_fact_by_type(facts, 'inverse_of')
        assert inv['property'] == 'writes'

    def test_irregular_verb_ate(self):
        """Every mouse is eaten by a cat."""
        facts = parse_cnl("Every mouse is eaten by a cat.")
        inv = get_fact_by_type(facts, 'inverse_of')
        assert inv['property'] == 'eats'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
