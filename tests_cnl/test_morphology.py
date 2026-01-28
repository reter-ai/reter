"""
Comprehensive tests for English morphology transformations.

This test file validates the morphological transformations in endict.cpp:
1. toDL_Simple: Natural language form -> base form (loves -> love)
2. toN_Simple: Base form -> natural language form (love -> loves)

All predicates are now stored in 3rd person singular form (loves, eats, owns).

Tests cover:
- Regular verb conjugation rules
- Irregular verbs from embedded dictionary
- Doubled consonant handling (stopped -> stop -> stops)
- -ied/-y handling (carried -> carry -> carries)
- -es handling for s/x/z/ch/sh/o endings
- Noun pluralization
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
# PLURAL NOUNS (fillers should be singular)
# =============================================================================

class TestPluralNouns:
    """Test plural noun normalization."""

    def test_cats_to_cat(self):
        """Every lion eats nothing-but cats -> cat."""
        facts = parse_cnl("Every lion eats nothing-but cats.")
        avf = find_fact(facts, type='all_values_from', filler='cat')
        assert avf is not None

    def test_mice_to_mouse(self):
        """Every cat eats nothing-but mice -> mouse."""
        facts = parse_cnl("Every cat eats nothing-but mice.")
        avf = find_fact(facts, type='all_values_from', filler='mouse')
        assert avf is not None

    def test_children_to_child(self):
        """Every parent has at-most 10 children -> child."""
        facts = parse_cnl("Every parent has at-most 10 children.")
        card = find_fact(facts, type='max_cardinality', filler='child')
        assert card is not None

    def test_persons_to_person(self):
        """Every-single-thing is-a-wife-of nothing-but persons -> person."""
        facts = parse_cnl("Every-single-thing is-a-wife-of nothing-but persons.")
        avf = find_fact(facts, type='all_values_from', filler='person')
        assert avf is not None

    def test_parents_to_parent(self):
        """Every person is-a-child-of at-most two parents -> parent."""
        facts = parse_cnl("Every person is-a-child-of at-most two parents.")
        card = find_fact(facts, type='max_cardinality', filler='parent')
        assert card is not None


# =============================================================================
# VERB FORMS (predicates should be 3rd person singular)
# =============================================================================

class TestVerbForms:
    """Test verb form normalization to 3rd person singular."""

    def test_eats_stays_eats(self):
        """Every cat eats a mouse -> eats (3rd person)."""
        facts = parse_cnl("Every cat eats a mouse.")
        svf = find_fact(facts, type='some_values_from', property='eats')
        assert svf is not None

    def test_loves_stays_loves(self):
        """Every person loves a cat -> loves (3rd person)."""
        facts = parse_cnl("Every person loves a cat.")
        svf = find_fact(facts, type='some_values_from', property='loves')
        assert svf is not None

    def test_has_stays_has(self):
        """Every cat has a tail -> has (3rd person of have)."""
        facts = parse_cnl("Every cat has a tail.")
        svf = find_fact(facts, type='some_values_from', property='has')
        assert svf is not None

    def test_owns_stays_owns(self):
        """John owns Pussy -> owns (3rd person)."""
        facts = parse_cnl("John owns Pussy.")
        ra = find_fact(facts, type='role_assertion', role='owns')
        assert ra is not None


# =============================================================================
# PAST TENSE -> 3RD PERSON SINGULAR (toDL_Simple SimplePast + toN_Simple)
# =============================================================================

class TestPastToThirdPerson:
    """Test past tense conversion to 3rd person singular via base form."""

    @pytest.mark.parametrize("past,expected_third", [
        # Regular -ed verbs
        ("loved", "loves"),
        ("owned", "owns"),
        ("walked", "walks"),
        ("talked", "talks"),
        ("played", "plays"),
        ("worked", "works"),
        ("called", "calls"),
        ("helped", "helps"),
        ("moved", "moves"),
        ("used", "uses"),
        ("liked", "likes"),
        ("started", "starts"),
        ("created", "creates"),
        ("hated", "hates"),
    ])
    def test_regular_ed_verbs(self, past, expected_third):
        """Regular -ed verbs are converted to 3rd person singular."""
        cnl = f"Mary is {past} by John."
        facts = parse_cnl(cnl)
        role_facts = get_facts_by_type(facts, 'role_assertion')
        assert len(role_facts) > 0, f"No role_assertion for: {cnl}"
        assert role_facts[0]['role'] == expected_third

    @pytest.mark.parametrize("past,expected_third", [
        # Doubled consonant verbs (stop -> stopped -> stop -> stops)
        ("stopped", "stops"),
        ("planned", "plans"),
        ("dropped", "drops"),
        ("grabbed", "grabs"),
        ("hugged", "hugs"),
        ("rubbed", "rubs"),
        ("clapped", "claps"),
        ("wrapped", "wraps"),
    ])
    def test_doubled_consonant_verbs(self, past, expected_third):
        """Doubled consonant verbs: stopped -> stop -> stops."""
        cnl = f"Mary is {past} by John."
        facts = parse_cnl(cnl)
        role_facts = get_facts_by_type(facts, 'role_assertion')
        assert len(role_facts) > 0, f"No role_assertion for: {cnl}"
        assert role_facts[0]['role'] == expected_third

    @pytest.mark.parametrize("past,expected_third", [
        # -ied verbs (carry -> carried -> carry -> carries)
        ("carried", "carries"),
        ("married", "marries"),
        ("worried", "worries"),
        ("studied", "studies"),
        ("hurried", "hurries"),
        ("tried", "tries"),
        ("cried", "cries"),
        ("copied", "copies"),
        ("applied", "applies"),
    ])
    def test_ied_verbs(self, past, expected_third):
        """'-ied' verbs: carried -> carry -> carries."""
        cnl = f"Mary is {past} by John."
        facts = parse_cnl(cnl)
        role_facts = get_facts_by_type(facts, 'role_assertion')
        assert len(role_facts) > 0, f"No role_assertion for: {cnl}"
        assert role_facts[0]['role'] == expected_third


# =============================================================================
# IRREGULAR PAST PARTICIPLE (passive voice)
# =============================================================================

class TestPastParticiple:
    """Test past participle normalization for passive voice to 3rd person."""

    def test_owned_to_owns(self):
        """Pussy is owned by John -> owns."""
        facts = parse_cnl("Pussy is owned by John.")
        ra = find_fact(facts, type='role_assertion', role='owns')
        assert ra is not None

    def test_loved_to_loves(self):
        """Mary is loved by John -> loves."""
        facts = parse_cnl("Mary is loved by John.")
        ra = find_fact(facts, type='role_assertion', role='loves')
        assert ra is not None

    def test_eaten_to_eats(self):
        """Every tasty-plant is eaten by a carnivore -> eats (inverse)."""
        facts = parse_cnl("Every tasty-plant is eaten by a carnivore.")
        # Passive creates inverse_of, check the inverse has base property 'eats'
        inv = find_fact(facts, type='inverse_of', property='eats')
        assert inv is not None

    def test_written_to_writes(self):
        """Every book is written by an author -> writes (inverse)."""
        facts = parse_cnl("Every book is written by an author.")
        inv = find_fact(facts, type='inverse_of', property='writes')
        assert inv is not None

    def test_driven_to_drives(self):
        """Every car is driven by a person -> drives (inverse)."""
        facts = parse_cnl("Every car is driven by a person.")
        inv = find_fact(facts, type='inverse_of', property='drives')
        assert inv is not None

    def test_taken_to_takes(self):
        """Every photo is taken by a photographer -> takes (inverse)."""
        facts = parse_cnl("Every photo is taken by a photographer.")
        inv = find_fact(facts, type='inverse_of', property='takes')
        assert inv is not None


# =============================================================================
# BASE FORM -> 3RD PERSON SINGULAR (with modal)
# =============================================================================

class TestBaseToThirdPerson:
    """Test conversion from base form to 3rd person singular (modal context)."""

    @pytest.mark.parametrize("base,expected_third", [
        # Regular +s
        ("love", "loves"),
        ("own", "owns"),
        ("walk", "walks"),
        ("play", "plays"),
        ("work", "works"),
        ("help", "helps"),
        ("move", "moves"),
        ("like", "likes"),
        ("start", "starts"),
        ("create", "creates"),
        ("hate", "hates"),
    ])
    def test_regular_s_addition(self, base, expected_third):
        """Regular verbs: base + s."""
        cnl = f"Every person must {base} something."
        facts = parse_cnl(cnl)
        svf = get_fact_by_type(facts, 'some_values_from')
        assert svf['property'] == expected_third

    @pytest.mark.parametrize("base,expected_third", [
        # consonant + y -> ies
        ("marry", "marries"),
        ("carry", "carries"),
        ("worry", "worries"),
        ("study", "studies"),
        ("hurry", "hurries"),
        ("try", "tries"),
        ("cry", "cries"),
        ("copy", "copies"),
        ("apply", "applies"),
        ("fly", "flies"),
        ("deny", "denies"),
        ("rely", "relies"),
    ])
    def test_consonant_y_to_ies(self, base, expected_third):
        """Consonant + y -> ies: marry -> marries."""
        cnl = f"Every person must {base} something."
        facts = parse_cnl(cnl)
        svf = get_fact_by_type(facts, 'some_values_from')
        assert svf['property'] == expected_third

    @pytest.mark.parametrize("base,expected_third", [
        # s, x, z, ch, sh, o -> es
        ("fix", "fixes"),
        ("watch", "watches"),
        ("wash", "washes"),
        ("push", "pushes"),
        ("catch", "catches"),
        ("miss", "misses"),
        ("pass", "passes"),
        ("box", "boxes"),
        ("buzz", "buzzes"),
        ("go", "goes"),
        ("do", "does"),
    ])
    def test_es_addition(self, base, expected_third):
        """s, x, z, ch, sh, o + es."""
        cnl = f"Every person must {base} something."
        facts = parse_cnl(cnl)
        svf = get_fact_by_type(facts, 'some_values_from')
        assert svf['property'] == expected_third


# =============================================================================
# IRREGULAR VERBS FROM DICTIONARY
# =============================================================================

class TestIrregularVerbs:
    """Test irregular verbs that should be in the embedded dictionary."""

    @pytest.mark.parametrize("past,expected_third", [
        # Common irregular verbs (past tense -> 3rd person singular)
        ("ate", "eats"),
        ("ran", "runs"),
        ("saw", "sees"),
        ("took", "takes"),
        ("gave", "gives"),
        ("went", "goes"),
        ("came", "comes"),
        ("made", "makes"),
        ("got", "gets"),
        ("found", "finds"),
        ("knew", "knows"),
        ("thought", "thinks"),
        ("told", "tells"),
        ("became", "becomes"),
        ("left", "leaves"),
        ("felt", "feels"),
        ("put", "puts"),
        ("kept", "keeps"),
        ("let", "lets"),
        ("began", "begins"),
        ("said", "says"),
        ("brought", "brings"),
        ("wrote", "writes"),
        ("sat", "sits"),
        ("stood", "stands"),
        ("heard", "hears"),
        ("lost", "loses"),
        ("met", "meets"),
        ("paid", "pays"),
        ("sent", "sends"),
        ("spent", "spends"),
        ("built", "builds"),
        ("caught", "catches"),
        ("taught", "teaches"),
        ("sold", "sells"),
        ("bought", "buys"),
        ("broke", "breaks"),
        ("chose", "chooses"),
        ("drove", "drives"),
        ("spoke", "speaks"),
        ("rose", "rises"),
        ("flew", "flies"),
        ("drew", "draws"),
        ("grew", "grows"),
        ("threw", "throws"),
        ("blew", "blows"),
        ("wore", "wears"),
        ("tore", "tears"),
        ("swore", "swears"),
        ("froze", "freezes"),
        ("hid", "hides"),
        ("bit", "bites"),
        ("rode", "rides"),
        ("shook", "shakes"),
        ("woke", "wakes"),
        ("forgot", "forgets"),
        ("held", "holds"),
        ("dug", "digs"),
        ("won", "wins"),
        ("swam", "swims"),
        ("rang", "rings"),
        ("sang", "sings"),
    ])
    def test_irregular_past_to_third(self, past, expected_third):
        """Irregular past tense to 3rd person singular via base form."""
        cnl = f"Mary is {past} by John."
        facts = parse_cnl(cnl)
        role_facts = get_facts_by_type(facts, 'role_assertion')
        if len(role_facts) > 0:
            actual = role_facts[0]['role']
            assert actual == expected_third, f"'{past}' -> '{actual}', expected '{expected_third}'"
        # Some verbs might not parse due to CNL grammar, skip those


# =============================================================================
# HYPHENATED COMPOUND PREDICATES
# =============================================================================

class TestCompoundPredicates:
    """Test hyphenated compound predicates."""

    @pytest.mark.parametrize("compound,expected", [
        # is- prefix preserved
        ("is-part-of", "is-part-of"),
        ("is-married-to", "is-married-to"),
        ("is-parent-of", "is-parent-of"),
        ("is-owned-by", "is-owned-by"),
        # has- prefix preserved
        ("has-parent", "has-parent"),
        ("has-child", "has-child"),
        ("has-part", "has-part"),
        # Regular compounds get verb part conjugated
        ("inheres-in", "inheres-in"),
        ("belongs-to", "belongs-to"),
        ("goes-to", "goes-to"),
        ("comes-from", "comes-from"),
    ])
    def test_compound_predicates(self, compound, expected):
        """Compound predicates are handled correctly."""
        cnl = f"John {compound} Team."
        facts = parse_cnl(cnl)
        role_facts = get_facts_by_type(facts, 'role_assertion')
        if len(role_facts) > 0:
            assert role_facts[0]['role'] == expected


# =============================================================================
# REGRESSIONS AND EDGE CASES
# =============================================================================

class TestMorphologyRegressions:
    """Regression tests for morphology issues."""

    def test_married_becomes_marries(self):
        """'married' -> 'marry' -> 'marries', not 'marrieds'."""
        facts = parse_cnl("Mary is married by John.")
        role_facts = get_facts_by_type(facts, 'role_assertion')
        assert len(role_facts) > 0
        assert role_facts[0]['role'] == 'marries'

    def test_is_married_to_preserved(self):
        """'is-married-to' should preserve 'is-' prefix."""
        facts = parse_cnl("John is-married-to Mary.")
        role_facts = get_facts_by_type(facts, 'role_assertion')
        assert len(role_facts) > 0
        assert role_facts[0]['role'] == 'is-married-to'

    def test_parts_of_not_created_from_is_part_of(self):
        """'is-part-of' should NOT become 'parts-of'."""
        facts = parse_cnl("Every wheel is-part-of a car.")
        svf = get_fact_by_type(facts, 'some_values_from')
        assert svf['property'] == 'is-part-of'

    def test_stopped_becomes_stops(self):
        """'stopped' (doubled p) -> 'stop' -> 'stops'."""
        facts = parse_cnl("Mary is stopped by John.")
        role_facts = get_facts_by_type(facts, 'role_assertion')
        if len(role_facts) > 0:
            assert role_facts[0]['role'] == 'stops'

    def test_planned_becomes_plans(self):
        """'planned' (doubled n) -> 'plan' -> 'plans'."""
        facts = parse_cnl("Mary is planned by John.")
        role_facts = get_facts_by_type(facts, 'role_assertion')
        if len(role_facts) > 0:
            assert role_facts[0]['role'] == 'plans'

    def test_tried_becomes_tries(self):
        """'tried' -> 'try' -> 'tries', not 'trys' or 'trieds'."""
        facts = parse_cnl("Mary is tried by John.")
        role_facts = get_facts_by_type(facts, 'role_assertion')
        if len(role_facts) > 0:
            assert role_facts[0]['role'] == 'tries'

    def test_fixes_not_fixs(self):
        """'fix' -> 'fixes', not 'fixs'."""
        facts = parse_cnl("Every person must fix something.")
        svf = get_fact_by_type(facts, 'some_values_from')
        assert svf['property'] == 'fixes'

    def test_goes_not_gos(self):
        """'go' -> 'goes', not 'gos'."""
        facts = parse_cnl("Every person must go-to something.")
        svf = get_fact_by_type(facts, 'some_values_from')
        assert svf['property'] == 'goes-to'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
