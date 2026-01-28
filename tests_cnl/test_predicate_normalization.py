"""
Comprehensive tests for CNL predicate normalization.

This test file validates that all CNL grammar constructs correctly normalize
predicates/roles to 3rd person singular form, and that passive voice is handled
correctly with inverse properties where appropriate.

Key behaviors tested:
1. Verb form: "loves" -> "loves", "owned" -> "owns" (3rd person singular)
2. Passive voice normalization: "loved" -> "loves", "owned" -> "owns"
3. Hyphenated role normalization: "inheres-in" -> "inheres-in", "has-parent" -> "has-parent"
4. Passive instance assertions: subject/object swapping
5. Passive restrictions: inverse property generation
6. SWRL passive: argument swapping
7. Property chains: chain field inclusion
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


# =============================================================================
# INSTANCE ASSERTIONS (ABox)
# =============================================================================

class TestInstanceAssertionNormalization:
    """Test predicate normalization in instance assertions."""

    def test_active_verb_normalized(self):
        """'John loves Mary' -> predicate: 'loves'"""
        facts = parse_cnl("John loves Mary.")
        fact = get_fact_by_type(facts, 'role_assertion')
        assert fact['role'] == 'loves', f"Expected 'loves', got '{fact['role']}'"

    def test_passive_verb_normalized(self):
        """'Mary is loved by John' -> predicate: 'loves'"""
        facts = parse_cnl("Mary is loved by John.")
        fact = get_fact_by_type(facts, 'role_assertion')
        assert fact['role'] == 'loves', f"Expected 'loves', got '{fact['role']}'"

    def test_passive_swaps_subject_object(self):
        """Passive voice swaps subject/object: John is agent, Mary is patient."""
        facts = parse_cnl("Mary is loved by John.")
        fact = get_fact_by_type(facts, 'role_assertion')
        assert fact['subject'] == 'John', f"Expected subject 'John', got '{fact['subject']}'"
        assert fact['object'] == 'Mary', f"Expected object 'Mary', got '{fact['object']}'"

    def test_active_passive_produce_same_fact(self):
        """Active and passive voice produce identical role assertions."""
        active_facts = parse_cnl("John owns Pussy.")
        passive_facts = parse_cnl("Pussy is owned by John.")

        active = get_fact_by_type(active_facts, 'role_assertion')
        passive = get_fact_by_type(passive_facts, 'role_assertion')

        assert active['role'] == passive['role'] == 'owns'
        assert active['subject'] == passive['subject'] == 'John'
        assert active['object'] == passive['object'] == 'Pussy'

    def test_hyphenated_role_normalized(self):
        """'inheres-in' -> 'inheres-in' (3rd person singular)"""
        facts = parse_cnl("Alfa inheres-in Beta.")
        fact = get_fact_by_type(facts, 'role_assertion')
        assert fact['role'] == 'inheres-in', f"Expected 'inheres-in', got '{fact['role']}'"

    def test_is_role_pattern_preserved(self):
        """'is-part-of' -> 'is-part-of' (is- prefix preserved)"""
        facts = parse_cnl("John is-part-of Team.")
        fact = get_fact_by_type(facts, 'role_assertion')
        assert fact['role'] == 'is-part-of', f"Expected 'is-part-of', got '{fact['role']}'"

    @pytest.mark.parametrize("cnl,expected_predicate", [
        ("John eats Pizza.", "eats"),
        ("Pizza is eaten by John.", "eats"),
        ("John hates Mary.", "hates"),
        ("Mary is hated by John.", "hates"),
        ("John creates Art.", "creates"),
        ("Art is created by John.", "creates"),
    ])
    def test_various_verbs_normalized(self, cnl, expected_predicate):
        """Various verbs are correctly converted to 3rd person singular."""
        facts = parse_cnl(cnl)
        role_facts = get_facts_by_type(facts, 'role_assertion')
        assert len(role_facts) > 0, f"No role_assertion found for: {cnl}"
        assert role_facts[0]['role'] == expected_predicate


# =============================================================================
# EXISTENTIAL RESTRICTIONS (TBox)
# =============================================================================

class TestExistentialRestrictionNormalization:
    """Test predicate normalization in existential restrictions."""

    def test_active_existential_normalized(self):
        """'Every man owns a cat' -> property: 'owns'"""
        facts = parse_cnl("Every man owns a cat.")
        svf = get_fact_by_type(facts, 'some_values_from')
        assert svf['property'] == 'owns', f"Expected 'owns', got '{svf['property']}'"

    def test_passive_existential_uses_inverse(self):
        """'Every man is owned by a cat' -> inverse_of + some_values_from"""
        facts = parse_cnl("Every man is owned by a cat.")

        # Should have inverse_of fact
        inv_facts = get_facts_by_type(facts, 'inverse_of')
        assert len(inv_facts) == 1, "Expected inverse_of fact for passive"
        assert inv_facts[0]['property'] == 'owns'

        # some_values_from should reference the inverse
        svf = get_fact_by_type(facts, 'some_values_from')
        assert svf['property'] == inv_facts[0]['id'], "SVF should use inverse property"

    def test_active_passive_existential_differ(self):
        """Active and passive existential produce different DL expressions."""
        active = parse_cnl("Every man owns a cat.")  # man ⊑ ∃owns.cat
        passive = parse_cnl("Every man is owned by a cat.")  # man ⊑ ∃owns⁻.cat

        # Active: direct property
        active_svf = get_fact_by_type(active, 'some_values_from')
        assert active_svf['property'] == 'owns'

        # Passive: inverse property
        passive_inv = get_facts_by_type(passive, 'inverse_of')
        assert len(passive_inv) == 1

    @pytest.mark.parametrize("cnl,expected_property", [
        ("Every person loves a thing.", "loves"),
        ("Every cat eats a mouse.", "eats"),
        ("Every child has-parent a person.", "has-parent"),
    ])
    def test_various_existential_normalized(self, cnl, expected_property):
        """Various existential restrictions are in 3rd person singular."""
        facts = parse_cnl(cnl)
        svf = get_fact_by_type(facts, 'some_values_from')
        assert svf['property'] == expected_property


# =============================================================================
# UNIVERSAL RESTRICTIONS (TBox)
# =============================================================================

class TestUniversalRestrictionNormalization:
    """Test predicate normalization in universal restrictions."""

    def test_active_universal_normalized(self):
        """'Every cat eats nothing-but mice' -> property: 'eats'"""
        facts = parse_cnl("Every cat eats nothing-but mice.")
        avf = get_fact_by_type(facts, 'all_values_from')
        assert avf['property'] == 'eats', f"Expected 'eats', got '{avf['property']}'"

    def test_passive_universal_uses_inverse(self):
        """'Every mouse is eaten by nothing-but cats' -> inverse_of + all_values_from"""
        facts = parse_cnl("Every mouse is eaten by nothing-but cats.")

        # Should have inverse_of fact
        inv_facts = get_facts_by_type(facts, 'inverse_of')
        assert len(inv_facts) == 1, "Expected inverse_of fact for passive"
        assert inv_facts[0]['property'] == 'eats'

        # all_values_from should reference the inverse
        avf = get_fact_by_type(facts, 'all_values_from')
        assert avf['property'] == inv_facts[0]['id'], "AVF should use inverse property"

    def test_active_passive_universal_differ(self):
        """Active and passive universal produce different DL expressions."""
        active = parse_cnl("Every cat eats nothing-but mice.")  # cat ⊑ ∀eats.mouse
        passive = parse_cnl("Every mouse is eaten by nothing-but cats.")  # mouse ⊑ ∀eats⁻.cat

        # Active: direct property
        active_avf = get_fact_by_type(active, 'all_values_from')
        assert active_avf['property'] == 'eats'

        # Passive: inverse property
        passive_inv = get_facts_by_type(passive, 'inverse_of')
        assert len(passive_inv) == 1


# =============================================================================
# CARDINALITY RESTRICTIONS
# =============================================================================

class TestCardinalityRestrictionNormalization:
    """Test predicate normalization in cardinality restrictions."""

    @pytest.mark.parametrize("cnl,card_type,expected_property", [
        ("Every person owns exactly one car.", "exact_cardinality", "owns"),
        ("Every person owns at-most two cars.", "max_cardinality", "owns"),
        ("Every person owns at-least one car.", "min_cardinality", "owns"),
        ("Every person has-parent exactly 2 persons.", "exact_cardinality", "has-parent"),
    ])
    def test_cardinality_normalized(self, cnl, card_type, expected_property):
        """Cardinality restrictions have 3rd person singular properties."""
        facts = parse_cnl(cnl)
        card = get_fact_by_type(facts, card_type)
        assert card['property'] == expected_property


# =============================================================================
# PROPERTY AXIOMS
# =============================================================================

class TestPropertyAxiomNormalization:
    """Test predicate normalization in property axioms."""

    def test_property_chain_normalized_and_complete(self):
        """Property chain has 3rd person singular roles and includes chain field."""
        facts = parse_cnl("If X has-parent something that has-parent Y then X has-grandparent Y.")
        chain = get_fact_by_type(facts, 'property_chain')

        # Check super_property is in 3rd person singular
        assert chain['super_property'] == 'has-grandparent'

        # Check chain field exists and is in 3rd person singular
        assert 'chain' in chain, "chain field missing from property_chain"
        assert chain['chain'] == ['has-parent', 'has-parent']

    def test_sub_property_normalized(self):
        """Sub-property axiom has 3rd person singular roles."""
        facts = parse_cnl("If X has-parent Y then X has-ancestor Y.")
        sub = get_fact_by_type(facts, 'sub_property')
        assert sub['sub'] == 'has-parent'
        assert sub['sup'] == 'has-ancestor'

    def test_symmetric_property_normalized(self):
        """Symmetric property axiom preserves is- prefix."""
        facts = parse_cnl("X is-married-to Y if-and-only-if Y is-married-to X.")
        sym = get_fact_by_type(facts, 'symmetric_property')
        assert sym['property'] == 'is-married-to'

    def test_asymmetric_property_normalized(self):
        """Asymmetric property axiom preserves is- prefix."""
        facts = parse_cnl("If X is-parent-of Y then Y does-not is-parent-of X.")
        asym = get_fact_by_type(facts, 'asymmetric_property')
        assert asym['property'] == 'is-parent-of'


# =============================================================================
# SWRL RULES
# =============================================================================

class TestSWRLNormalization:
    """Test predicate normalization in SWRL rules."""

    def test_swrl_active_verbs_normalized(self):
        """SWRL rules use 3rd person singular verbs in body and head."""
        facts = parse_cnl("If a person loves a thing then the person likes the thing.")
        swrl = get_fact_by_type(facts, 'swrl_rule')

        assert 'loves(' in swrl['body'], f"Expected 'loves' in body: {swrl['body']}"
        assert 'likes(' in swrl['head'], f"Expected 'likes' in head: {swrl['head']}"

    def test_swrl_passive_swaps_arguments(self):
        """SWRL passive voice swaps arguments correctly."""
        facts = parse_cnl("If a person is loved by a thing then the thing cares-for the person.")
        swrl = get_fact_by_type(facts, 'swrl_rule')

        # Passive "is loved by" should have thing as subject, person as object
        # loves(?thing, ?person) not loves(?person, ?thing)
        assert 'loves(?thing' in swrl['body'] or 'loves(?thing2, ?person1)' in swrl['body'], \
            f"Passive should swap args: {swrl['body']}"

    def test_swrl_hyphenated_roles_normalized(self):
        """SWRL rules use 3rd person singular for hyphenated roles."""
        facts = parse_cnl("If a man owns a cat and the cat hunts a mouse then the man feeds the cat.")
        swrl = get_fact_by_type(facts, 'swrl_rule')

        assert 'owns(' in swrl['body']
        assert 'hunts(' in swrl['body']
        assert 'feeds(' in swrl['head']

    def test_swrl_complex_with_passive(self):
        """Complex SWRL with passive voice."""
        facts = parse_cnl("If a person is loved by a thing then the thing cares-for the person.")
        swrl = get_fact_by_type(facts, 'swrl_rule')

        # Body should have loves with swapped args
        assert 'loves(' in swrl['body']
        # Head should have cares-for in 3rd person singular
        assert 'cares-for(' in swrl['head']


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Test edge cases in predicate normalization."""

    @pytest.mark.parametrize("verb,past,expected", [
        ("love", "loved", "loves"),
        ("own", "owned", "owns"),
        ("hate", "hated", "hates"),
        ("create", "created", "creates"),
        ("walk", "walked", "walks"),
        ("talk", "talked", "talks"),
        ("phone", "phoned", "phones"),  # base ends in 'e', special case
    ])
    def test_past_tense_to_3rd_person(self, verb, past, expected):
        """Various past tense forms are correctly converted to 3rd person singular."""
        # Use passive voice to trigger past tense handling
        cnl = f"Mary is {past} by John."
        facts = parse_cnl(cnl)
        role_facts = get_facts_by_type(facts, 'role_assertion')
        if role_facts:
            assert role_facts[0]['role'] == expected, \
                f"'{past}' should become '{expected}', got '{role_facts[0]['role']}'"

    def test_third_person_singular_preserved(self):
        """Third person singular verbs are preserved: 'loves' -> 'loves'"""
        facts = parse_cnl("Every person loves a thing.")
        svf = get_fact_by_type(facts, 'some_values_from')
        assert svf['property'] == 'loves'

    def test_hyphenated_verb_3rd_person(self):
        """Hyphenated verbs: 'inheres-in' -> 'inheres-in' (already 3rd person)"""
        facts = parse_cnl("Every quality inheres-in something.")
        svf = get_fact_by_type(facts, 'some_values_from')
        assert svf['property'] == 'inheres-in'

    def test_has_prefix_preserved(self):
        """'has-parent' -> 'has-parent' (has is already 3rd person singular of have)"""
        facts = parse_cnl("Every child has-parent a person.")
        svf = get_fact_by_type(facts, 'some_values_from')
        assert svf['property'] == 'has-parent'

    def test_consonant_y_to_ies(self):
        """Consonant + y -> ies: 'marry' -> 'marries', 'carry' -> 'carries'"""
        # Test with role assertion (named individuals)
        facts = parse_cnl("John marries Mary.")
        role_facts = get_facts_by_type(facts, 'role_assertion')
        assert len(role_facts) > 0
        assert role_facts[0]['role'] == 'marries'

        # Test with existential restriction
        facts = parse_cnl("Every person carries a bag.")
        svf = get_fact_by_type(facts, 'some_values_from')
        assert svf['property'] == 'carries'

    def test_x_to_xes(self):
        """x -> xes: 'fix' -> 'fixes'"""
        facts = parse_cnl("Every person fixes a car.")
        svf = get_fact_by_type(facts, 'some_values_from')
        assert svf['property'] == 'fixes'

    def test_go_to_goes(self):
        """Special case: 'go' -> 'goes'"""
        facts = parse_cnl("Every person goes-to a place.")
        svf = get_fact_by_type(facts, 'some_values_from')
        assert svf['property'] == 'goes-to'


# =============================================================================
# REGRESSION TESTS
# =============================================================================

class TestRegressions:
    """Regression tests for previously broken functionality."""

    def test_owned_becomes_owns(self):
        """Regression: 'owned' should become 'owns', not 'own' or 'owne'"""
        facts = parse_cnl("Pussy is owned by John.")
        fact = get_fact_by_type(facts, 'role_assertion')
        assert fact['role'] == 'owns', f"Got '{fact['role']}' instead of 'owns'"

    def test_passive_existential_has_inverse(self):
        """Regression: passive existential must use inverse property"""
        facts = parse_cnl("Every man is owned by a cat.")
        inv_facts = get_facts_by_type(facts, 'inverse_of')
        assert len(inv_facts) == 1, "Missing inverse_of for passive existential"

    def test_passive_universal_has_inverse(self):
        """Regression: passive universal must use inverse property"""
        facts = parse_cnl("Every mouse is eaten by nothing-but cats.")
        inv_facts = get_facts_by_type(facts, 'inverse_of')
        assert len(inv_facts) == 1, "Missing inverse_of for passive universal"

    def test_property_chain_has_chain_field(self):
        """Regression: property_chain must include chain field"""
        facts = parse_cnl("If X has-parent something that has-parent Y then X has-grandparent Y.")
        chain = get_fact_by_type(facts, 'property_chain')
        assert 'chain' in chain, "chain field missing"
        assert isinstance(chain['chain'], list), "chain should be a list"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
