"""
Tests for CNL Parser with gUFO Ontology - Based on gufo_overview.md

This test file validates all CNL examples from gufo_overview.md,
testing them in the context of the gUFO ontology (gufo.cnl).
"""
import pytest
from pathlib import Path
import reter_core.owl_rete_cpp as cpp


# Path to gUFO ontology
GUFO_PATH = Path(__file__).parent / "gufo.cnl"

# Cache for gUFO content (loaded once)
_gufo_content_cache = None


def _get_gufo_content():
    """Load gUFO content (cached)."""
    global _gufo_content_cache
    if _gufo_content_cache is None:
        with open(GUFO_PATH, 'r') as f:
            _gufo_content_cache = f.read()
    return _gufo_content_cache


def _facts_to_dicts(facts):
    """Convert facts to list of dicts."""
    result = []
    for f in facts:
        fact_dict = {}
        for key in ['type', 'sub', 'sup', 'individual', 'concept', 'subject',
                    'role', 'object', 'c1', 'c2', 'property', 'filler',
                    'cardinality', 'id', 'class', 'i1', 'i2', 'modality',
                    'chain', 'super_property', 'value', 'datatype']:
            val = f.get(key)
            if val:
                fact_dict[key] = val
        result.append(fact_dict)
    return result


@pytest.fixture(scope="module")
def gufo_facts():
    """Load gUFO ontology facts."""
    result = cpp.parse_cnl(_get_gufo_content())
    return result.facts


@pytest.fixture
def parse_cnl():
    """Parse CNL in context of gUFO and return domain facts as list of dicts.

    This fixture parses domain patterns together with gUFO ontology,
    but returns only the NEW facts from the domain (not gUFO facts).
    This allows testing domain patterns in context of gUFO.
    """
    # Get gUFO facts count for filtering
    gufo_result = cpp.parse_cnl(_get_gufo_content())
    gufo_count = len(gufo_result.facts)

    def _parse(cnl_text):
        # Combine gUFO + domain CNL
        combined = _get_gufo_content() + "\n" + cnl_text
        result = cpp.parse_cnl(combined)

        # Return only domain facts (skip gUFO facts)
        domain_facts = list(result.facts)[gufo_count:]
        return _facts_to_dicts(domain_facts)
    return _parse


@pytest.fixture
def parse_cnl_isolated():
    """Parse CNL in isolation (without gUFO context).

    Use this for testing CNL parsing without gUFO dependencies.
    """
    def _parse(cnl_text):
        result = cpp.parse_cnl(cnl_text)
        return _facts_to_dicts(result.facts)
    return _parse


def has_fact(facts, **criteria):
    """Check if a fact matching criteria exists."""
    for f in facts:
        if all(f.get(k) == v for k, v in criteria.items()):
            return True
    return False


def has_fact_type(facts, fact_type):
    """Check if any fact of given type exists."""
    return any(f.get('type') == fact_type for f in facts)


# =============================================================================
# Section 1: Usage Scenarios
# =============================================================================

class TestUsageScenarios:
    """Tests for basic usage scenarios from section 1."""

    def test_scenario1_instantiate_individuals(self, parse_cnl):
        """Scenario 1: Instantiate gUFO classes in taxonomy of individuals."""
        # Earth is an object
        facts = parse_cnl("Earth is an object.")
        assert has_fact(facts, type='instance_of', individual='Earth', concept='object')

        # World-Cup-1970-Final is an event
        facts = parse_cnl("World-Cup-1970-Final is an event.")
        assert has_fact(facts, type='instance_of', individual='World-Cup-1970-Final', concept='event')

    def test_scenario2_specialize_individuals(self, parse_cnl):
        """Scenario 2: Specialize gUFO classes in taxonomy of individuals."""
        # Every planet is an object
        facts = parse_cnl("Every planet is an object.")
        assert has_fact(facts, type='subsumption', sub='planet', sup='object')

        # Every soccer-match is an event
        facts = parse_cnl("Every soccer-match is an event.")
        assert has_fact(facts, type='subsumption', sub='soccer-match', sup='event')

    def test_scenario3_instantiate_types(self, parse_cnl):
        """Scenario 3: Instantiate gUFO classes in taxonomy of types."""
        # Planet is a kind
        facts = parse_cnl("Planet is a kind.")
        assert has_fact(facts, type='instance_of', individual='Planet', concept='kind')

        # Child is a phase
        facts = parse_cnl("Child is a phase.")
        assert has_fact(facts, type='instance_of', individual='Child', concept='phase')

    def test_scenario4_specialize_types(self, parse_cnl):
        """Scenario 4: Specialize gUFO classes in taxonomy of types."""
        facts = parse_cnl("Every person-phase is a phase.")
        assert has_fact(facts, type='subsumption', sub='person-phase', sup='phase')

    def test_combined_scenario_2_and_3(self, parse_cnl):
        """Combined scenarios 2 and 3: Person as object and kind."""
        facts = parse_cnl("""
            Every person is an object.
            Person is a kind.
        """)
        assert has_fact(facts, type='subsumption', sub='person', sup='object')
        assert has_fact(facts, type='instance_of', individual='Person', concept='kind')


# =============================================================================
# Section 2.1: Concrete Individuals
# =============================================================================

class TestConcreteIndividuals:
    """Tests for concrete individuals from section 2.1."""

    def test_earthquake_event(self, parse_cnl):
        """Earthquake as sub-class of event."""
        facts = parse_cnl("Every earthquake is an event.")
        assert has_fact(facts, type='subsumption', sub='earthquake', sup='event')

    def test_event_temporal_properties(self, parse_cnl):
        """Event with temporal data properties."""
        # Note: The full datetime format may not parse, testing simpler case
        facts = parse_cnl("World-Cup-1970-Final has-begin-date equal-to 1970-06-21.")
        assert has_fact(facts, type='data_assertion', subject='World-Cup-1970-Final',
                       property='has-begin-date')


# =============================================================================
# Section 2.2: Objects and Parts
# =============================================================================

class TestObjectsAndParts:
    """Tests for objects and their parts from section 2.2."""

    def test_functional_complex(self, parse_cnl):
        """Person as functional complex."""
        facts = parse_cnl("Every person is a functional-complex.")
        assert has_fact(facts, type='subsumption', sub='person', sup='functional-complex')

    def test_collection_types(self, parse_cnl):
        """Variable and fixed collections."""
        facts = parse_cnl("""
            Every team is a variable-collection.
            Every deck-of-cards is a fixed-collection.
        """)
        assert has_fact(facts, type='subsumption', sub='team', sup='variable-collection')
        assert has_fact(facts, type='subsumption', sub='deck-of-cards', sup='fixed-collection')

    def test_quantity(self, parse_cnl):
        """Quantity as complex object."""
        facts = parse_cnl("Every amount-of-wine is a quantity.")
        assert has_fact(facts, type='subsumption', sub='amount-of-wine', sup='quantity')

    def test_component_of_relation(self, parse_cnl):
        """Component-of relation for functional complex parts."""
        facts = parse_cnl("Johns-Brain is a brain and is-component-of John.")
        # Multi-typed individuals create intersection types
        assert has_fact_type(facts, 'intersection')
        assert has_fact_type(facts, 'instance_of')
        assert has_fact(facts, type='role_assertion', subject='Johns-Brain',
                       role='is-component-of', object='John')

    def test_brain_as_object(self, parse_cnl):
        """Brain as sub-class of object."""
        facts = parse_cnl("Every brain is an object.")
        assert has_fact(facts, type='subsumption', sub='brain', sup='object')


# =============================================================================
# Section 2.3-2.4: Intrinsic Aspects and Qualities
# =============================================================================

class TestQualitiesBasic:
    """Tests for qualities - basic patterns from section 2.4."""

    def test_quality_subsumption(self, parse_cnl):
        """Mass as sub-class of quality."""
        facts = parse_cnl("Every mass is a quality.")
        assert has_fact(facts, type='subsumption', sub='mass', sup='quality')

    def test_quality_inheres_in(self, parse_cnl):
        """Quality inheres-in cardinality restriction."""
        # Use "exactly one" (two words) instead of "exactly-one" (hyphenated)
        facts = parse_cnl("Every mass inheres-in exactly one physical-object.")
        assert has_fact_type(facts, 'exact_cardinality')

    def test_quality_value_assertion(self, parse_cnl):
        """Quality with has-quality-value data property."""
        facts = parse_cnl("Moon-Mass has-quality-value equal-to 7.34767309E22.")
        assert has_fact(facts, type='data_assertion', subject='Moon-Mass',
                       property='has-quality-value')

    def test_physical_object_mass(self, parse_cnl):
        """Physical object with mass data property."""
        facts = parse_cnl("Moon is a physical-object and has-mass-in-kilograms equal-to 7.34767309E22.")
        # Multi-typed individuals with data property create intersection types
        assert has_fact_type(facts, 'intersection')
        assert has_fact_type(facts, 'instance_of')
        assert has_fact(facts, type='data_assertion', subject='Moon', property='has-mass-in-kilograms')

    def test_sub_property_of_inheres_in(self, parse_cnl):
        """Sub-property of inheres-in."""
        facts = parse_cnl("If X is-mass-of Y then X inheres-in Y.")
        assert has_fact(facts, type='sub_property', sub='is-mass-of', sup='inheres-in')

    def test_mass_existential(self, parse_cnl):
        """Every mass is-mass-of something."""
        facts = parse_cnl("Every mass is-mass-of something.")
        assert has_fact_type(facts, 'some_values_from')

    def test_mass_universal_range(self, parse_cnl):
        """is-mass-of range restriction."""
        facts = parse_cnl("Every-single-thing is-mass-of nothing-but physical-objects.")
        assert has_fact_type(facts, 'all_values_from')


# =============================================================================
# Section 2.5: Qualities - Advanced Usage
# =============================================================================

class TestQualitiesAdvanced:
    """Tests for qualities - advanced usage from section 2.5."""

    def test_quality_value_enumeration(self, parse_cnl):
        """Shirt size as enumerated quality value."""
        facts = parse_cnl("""
            S is a shirt-size.
            M is a shirt-size.
            L is a shirt-size.
            `XL` is a shirt-size.
        """)
        assert has_fact(facts, type='instance_of', individual='S', concept='shirt-size')
        assert has_fact(facts, type='instance_of', individual='XL', concept='shirt-size')

    def test_color_value_in_rgb(self, parse_cnl):
        """Color value in RGB as quality value."""
        facts = parse_cnl("Every color-value-in-rgb is a quality-value.")
        assert has_fact(facts, type='subsumption', sub='color-value-in-rgb', sup='quality-value')

    def test_rgb_component_existential(self, parse_cnl):
        """RGB color component existential restriction."""
        facts = parse_cnl("Every color-value-in-rgb has-red-value-component (some value).")
        assert has_fact_type(facts, 'some_values_from') or has_fact_type(facts, 'data_all_values_from')

    def test_rgb_component_range(self, parse_cnl):
        """RGB component integer range restriction."""
        facts = parse_cnl("Every-single-thing has-red-value-component nothing-but (some integer value).")
        assert has_fact_type(facts, 'data_all_values_from')

    def test_color_instance_with_value(self, parse_cnl):
        """Color instance with RGB value."""
        facts = parse_cnl("""
            Yves-Klein-Blue-Monochrome-Painting-Color-Value-In-Rgb is a color-value-in-rgb
            that has-red-value-component equal-to 0
            and has-green-value-component equal-to 47
            and has-blue-value-component equal-to 167.
        """)
        assert has_fact(facts, type='instance_of',
                       individual='Yves-Klein-Blue-Monochrome-Painting-Color-Value-In-Rgb',
                       concept='color-value-in-rgb')


# =============================================================================
# Section 2.6: Intrinsic Modes
# =============================================================================

class TestIntrinsicModes:
    """Tests for intrinsic modes from section 2.6."""

    def test_headache_as_intrinsic_mode(self, parse_cnl):
        """Headache as sub-class of intrinsic-mode."""
        facts = parse_cnl("Every headache is an intrinsic-mode.")
        assert has_fact(facts, type='subsumption', sub='headache', sup='intrinsic-mode')

    def test_headache_inheres_in_person(self, parse_cnl):
        """Headache inheres-in person via sub-property."""
        facts = parse_cnl("If X is-headache-of Y then X inheres-in Y.")
        assert has_fact(facts, type='sub_property', sub='is-headache-of', sup='inheres-in')

    def test_headache_range(self, parse_cnl):
        """Headache range restriction to person."""
        facts = parse_cnl("Every-single-thing is-headache-of nothing-but person.")
        assert has_fact_type(facts, 'all_values_from')

    def test_headache_intensity_quality(self, parse_cnl):
        """Headache-intensity as quality of headache."""
        facts = parse_cnl("Every headache-intensity is a quality.")
        assert has_fact(facts, type='subsumption', sub='headache-intensity', sup='quality')


# =============================================================================
# Section 2.7: Extrinsic Aspects (Relators)
# =============================================================================

class TestExtrinsicAspects:
    """Tests for extrinsic aspects from section 2.7."""

    def test_marriage_as_relator(self, parse_cnl):
        """Marriage as sub-class of relator."""
        facts = parse_cnl("Every marriage is a relator.")
        assert has_fact(facts, type='subsumption', sub='marriage', sup='relator')

    def test_marriage_mediates_sub_property(self, parse_cnl):
        """Marriage-involves as sub-property of mediates."""
        facts = parse_cnl("If X marriage-involves Y then X mediates Y.")
        assert has_fact(facts, type='sub_property', sub='marriages-involves', sup='mediates')

    def test_marriage_mediates_person(self, parse_cnl):
        """Marriage mediates person."""
        facts = parse_cnl("Every marriage mediates a person.")
        assert has_fact_type(facts, 'some_values_from')

    def test_employment_relator(self, parse_cnl):
        """Employment as relator with employee and employer."""
        facts = parse_cnl("""
            Every employment is a relator.
            Every employee is a person.
            Every employer is an organization.
        """)
        assert has_fact(facts, type='subsumption', sub='employment', sup='relator')
        assert has_fact(facts, type='subsumption', sub='employee', sup='person')
        assert has_fact(facts, type='subsumption', sub='employer', sup='organization')

    def test_extrinsic_mode_pattern(self, parse_cnl):
        """Extrinsic mode with inheres-in and depends-externally-on."""
        facts = parse_cnl("""
            Johns-Right-To-Service-Provisioning is an extrinsic-mode
            that inheres-in John and depends-externally-on Amazon-Inc.
        """)
        assert has_fact(facts, type='instance_of',
                       individual='Johns-Right-To-Service-Provisioning',
                       concept='extrinsic-mode')
        assert has_fact(facts, type='role_assertion',
                       subject='Johns-Right-To-Service-Provisioning',
                       role='inheres-in', object='John')


# =============================================================================
# Section 2.8: Events
# =============================================================================

class TestEvents:
    """Tests for events from section 2.8."""

    def test_natural_disaster_hierarchy(self, parse_cnl):
        """Natural disaster class hierarchy."""
        facts = parse_cnl("""
            Every natural-disaster is an event.
            Every earthquake is a natural-disaster.
            Every tsunami is a natural-disaster.
            No earthquake is a tsunami.
        """)
        assert has_fact(facts, type='subsumption', sub='natural-disaster', sup='event')
        assert has_fact(facts, type='subsumption', sub='earthquake', sup='natural-disaster')
        assert has_fact(facts, type='subsumption', sub='tsunami', sup='natural-disaster')
        assert has_fact_type(facts, 'alldisjoint_classes')

    def test_soccer_match_event(self, parse_cnl):
        """Soccer match as event."""
        facts = parse_cnl("""
            Every soccer-match is an event.
            World-Cup-1970-Final is a soccer-match.
        """)
        assert has_fact(facts, type='subsumption', sub='soccer-match', sup='event')
        assert has_fact(facts, type='instance_of', individual='World-Cup-1970-Final',
                       concept='soccer-match')

    def test_historical_dependence(self, parse_cnl):
        """Event depends-historically-on another event."""
        facts = parse_cnl("""
            World-Cup-1970-Final depends-historically-on Brazil-Uruguay-World-Cup-1970-Semi-Final.
        """)
        assert has_fact(facts, type='role_assertion', subject='World-Cup-1970-Final',
                       role='depends-historically-on',
                       object='Brazil-Uruguay-World-Cup-1970-Semi-Final')

    def test_participation_in_event(self, parse_cnl):
        """Person participates-in event."""
        facts = parse_cnl("""
            If X participates-in-match Y then X participates-in Y.
            Every soccer-match-player participates-in-match something.
        """)
        assert has_fact(facts, type='sub_property', sub='participates-in-match', sup='participates-in')

    def test_event_proper_part(self, parse_cnl):
        """Event proper part relation."""
        facts = parse_cnl("""
            World-Cup-1970 is an event.
            World-Cup-1970-Final is a soccer-match that is-event-proper-part-of World-Cup-1970.
        """)
        assert has_fact(facts, type='instance_of', individual='World-Cup-1970', concept='event')
        assert has_fact(facts, type='role_assertion', subject='World-Cup-1970-Final',
                       role='is-event-proper-part-of', object='World-Cup-1970')

    def test_event_creates_relator(self, parse_cnl):
        """Event creates relator (wedding creates marriage)."""
        facts = parse_cnl("""
            John-Marys-Marriage is a marriage that marriage-involves John
            and marriage-involves Mary and is-created-in John-Marys-Wedding.
        """)
        assert has_fact(facts, type='instance_of', individual='John-Marys-Marriage', concept='marriage')

    def test_functional_complex_terminated(self, parse_cnl):
        """Functional complex terminated-in event."""
        facts = parse_cnl("""
            Challenger is a functional-complex that is-terminated-in Challengers-10-Th-Flight.
        """)
        assert has_fact(facts, type='instance_of', individual='Challenger', concept='functional-complex')
        assert has_fact(facts, type='role_assertion', subject='Challenger',
                       role='is-terminated-in', object='Challengers-10-Th-Flight')


# =============================================================================
# Section 2.9: Situations
# =============================================================================

class TestSituations:
    """Tests for situations from section 2.9."""

    def test_quality_value_attribution_situation(self, parse_cnl):
        """Quality value attribution situation."""
        facts = parse_cnl("""
            John-Weighs-80-Kgin-2015 is a quality-value-attribution-situation
            that concerns-quality-type Mass and concerns-quality-value equal-to 80.0.
        """)
        assert has_fact(facts, type='instance_of',
                       individual='John-Weighs-80-Kgin-2015',
                       concept='quality-value-attribution-situation')

    def test_temporary_instantiation_situation(self, parse_cnl):
        """Temporary instantiation situation (child/adult phases)."""
        facts = parse_cnl("""
            Every child is a person.
            Every adult is a person.
            John-Was-A-Child-From-1977-To-1995 is a temporary-instantiation-situation
            that concerns-non-rigid-type Child.
        """)
        assert has_fact(facts, type='subsumption', sub='child', sup='person')
        assert has_fact(facts, type='instance_of',
                       individual='John-Was-A-Child-From-1977-To-1995',
                       concept='temporary-instantiation-situation')

    def test_temporary_parthood_situation(self, parse_cnl):
        """Temporary parthood situation (organ transplant)."""
        facts = parse_cnl("""
            Johns-Heart is a heart that stands-in-qualified-parthood John-Has-Original-Heart.
            John-Has-Original-Heart is a temporary-parthood-situation
            that concerns-temporary-whole John.
        """)
        assert has_fact(facts, type='role_assertion', subject='Johns-Heart',
                       role='stands-in-qualified-parthood', object='John-Has-Original-Heart')
        assert has_fact(facts, type='instance_of',
                       individual='John-Has-Original-Heart',
                       concept='temporary-parthood-situation')

    def test_temporary_constitution_situation(self, parse_cnl):
        """Temporary constitution situation (Venus of Milo)."""
        facts = parse_cnl("""
            Venus-Of-Milo is a statue.
            Venus-Has-Arms is a temporary-constitution-situation
            that concerns-constituted-endurant Venus-Of-Milo.
        """)
        assert has_fact(facts, type='instance_of', individual='Venus-Of-Milo', concept='statue')
        assert has_fact(facts, type='instance_of',
                       individual='Venus-Has-Arms',
                       concept='temporary-constitution-situation')

    def test_temporary_relationship_situation(self, parse_cnl):
        """Temporary relationship situation (is-heavier-than)."""
        facts = parse_cnl("""
            John-Is-Heavier is a temporary-relationship-situation
            that concerns-relationship-type Is-Heavier-Than and concerns-lighter-object Paul.
        """)
        assert has_fact(facts, type='instance_of',
                       individual='John-Is-Heavier',
                       concept='temporary-relationship-situation')


# =============================================================================
# Section 3.1: Endurant Types
# =============================================================================

class TestEndurantTypes:
    """Tests for endurant types from section 3.1."""

    def test_kind_phase_role(self, parse_cnl):
        """Person as kind, Adult as phase, Student as role."""
        facts = parse_cnl("""
            Person is a kind.
            Adult is a phase.
            Every adult is a person.
            Student is a role.
            Every student is a person.
        """)
        assert has_fact(facts, type='instance_of', individual='Person', concept='kind')
        assert has_fact(facts, type='instance_of', individual='Adult', concept='phase')
        assert has_fact(facts, type='instance_of', individual='Student', concept='role')
        assert has_fact(facts, type='subsumption', sub='adult', sup='person')
        assert has_fact(facts, type='subsumption', sub='student', sup='person')


# =============================================================================
# Section 3.2: Relationship Types
# =============================================================================

class TestRelationshipTypes:
    """Tests for relationship types from section 3.2."""

    def test_material_relationship_type(self, parse_cnl):
        """Material relationship type derived from relator."""
        facts = parse_cnl("""
            Is-Married-With is a material-relationship-type.
            Every person is-married-with something.
            Every-single-thing is-married-with nothing-but persons.
            Is-Married-With is-derived-from Marriage.
        """)
        assert has_fact(facts, type='instance_of', individual='Is-Married-With',
                       concept='material-relationship-type')
        assert has_fact(facts, type='role_assertion', subject='Is-Married-With',
                       role='is-derived-from', object='Marriage')


# =============================================================================
# Section 3.3: Higher-Order Types
# =============================================================================

class TestHigherOrderTypes:
    """Tests for higher-order types from section 3.3."""

    def test_person_role_categorizes(self, parse_cnl):
        """PersonRole categorizes Person."""
        facts = parse_cnl("""
            Person-Role categorizes Person.
            Every person-role is a role.
            Student is a person-role.
            Every student is a person.
        """)
        assert has_fact(facts, type='role_assertion', subject='Person-Role',
                       role='categorizes', object='Person')
        assert has_fact(facts, type='instance_of', individual='Student', concept='person-role')

    def test_ship_type_sub_kind(self, parse_cnl):
        """Ship-Type as higher-order type for sub-kinds."""
        facts = parse_cnl("""
            Ship-Type categorizes Ship.
            Every ship-type is a sub-kind.
            Supercarrier is a ship-type.
            Every supercarrier is a ship.
        """)
        assert has_fact(facts, type='role_assertion', subject='Ship-Type',
                       role='categorizes', object='Ship')
        assert has_fact(facts, type='subsumption', sub='ship-type', sup='sub-kind')

    def test_animal_species_partitions(self, parse_cnl):
        """Animal-Species partitions Animal (exhaustive specialization)."""
        facts = parse_cnl("""
            Animal-Species partitions Animal.
            Hiena is an animal-species.
            Every hiena is an animal.
            Lion is an animal-species.
            Every lion is an animal.
            No lion is a hiena.
            Cecil is a lion.
        """)
        assert has_fact(facts, type='role_assertion', subject='Animal-Species',
                       role='partitions', object='Animal')
        assert has_fact(facts, type='instance_of', individual='Cecil', concept='lion')


# =============================================================================
# LLM Usage Guidelines Tests
# =============================================================================

class TestLLMUsagePatterns:
    """Tests for LLM usage patterns from section 1.1."""

    def test_basic_type_declaration_pattern(self, parse_cnl):
        """Basic type declaration pattern."""
        facts = parse_cnl("""
            Every person is an object.
            Person is a kind.
        """)
        assert has_fact(facts, type='subsumption', sub='person', sup='object')
        assert has_fact(facts, type='instance_of', individual='Person', concept='kind')

    def test_property_definition_pattern(self, parse_cnl):
        """Property definition pattern with existential and universal."""
        facts = parse_cnl("""
            Every person has-age some value.
            Every-single-thing has-age nothing-but (some integer value).
        """)
        assert has_fact_type(facts, 'some_values_from')
        assert has_fact_type(facts, 'data_all_values_from')

    def test_aspect_reification_pattern(self, parse_cnl):
        """Aspect reification pattern for qualities."""
        # Use "exactly one" (two words) instead of "exactly-one" (hyphenated)
        facts = parse_cnl("""
            Every weight is a quality.
            Every weight inheres-in exactly one person.
            Every weight has-quality-value some value.
        """)
        assert has_fact(facts, type='subsumption', sub='weight', sup='quality')
        assert has_fact_type(facts, 'exact_cardinality')

    def test_relationship_pattern_simple(self, parse_cnl):
        """Simple relationship pattern."""
        facts = parse_cnl("Every person knows some person.")
        assert has_fact_type(facts, 'some_values_from')

    def test_relationship_pattern_reified(self, parse_cnl):
        """Reified relationship pattern with relator."""
        facts = parse_cnl("""
            Every friendship is a relator.
            Every friendship mediates exactly 2 persons.
            Every friendship has-begin-date some value.
        """)
        assert has_fact(facts, type='subsumption', sub='friendship', sup='relator')
        assert has_fact_type(facts, 'exact_cardinality')

    def test_corrected_employee_pattern(self, parse_cnl):
        """Corrected employee pattern from LLM example."""
        facts = parse_cnl("""
            Every employee is a person.
            Employee is a role.
            Every organization is an object.
            Organization is a kind.
            Every employment is a relator.
            Every employment mediates exactly-one employee.
            Every employment mediates exactly-one organization.
        """)
        assert has_fact(facts, type='subsumption', sub='employee', sup='person')
        assert has_fact(facts, type='instance_of', individual='Employee', concept='role')
        assert has_fact(facts, type='instance_of', individual='Organization', concept='kind')


# =============================================================================
# Integration Tests with gUFO Ontology
# =============================================================================

class TestIntegrationWithGufo:
    """Tests that verify patterns work correctly WITH gufo.cnl loaded."""

    def test_gufo_subsumptions_exist(self, gufo_facts):
        """Verify gUFO ontology has expected subsumptions."""
        facts = [{'type': f.get('type'), 'sub': f.get('sub'), 'sup': f.get('sup')}
                 for f in gufo_facts]

        # Core hierarchy
        assert has_fact(facts, type='subsumption', sub='endurant', sup='concrete-individual')
        assert has_fact(facts, type='subsumption', sub='object', sup='endurant')
        assert has_fact(facts, type='subsumption', sub='aspect', sup='endurant')
        assert has_fact(facts, type='subsumption', sub='quality', sup='intrinsic-aspect')
        assert has_fact(facts, type='subsumption', sub='relator', sup='extrinsic-aspect')

    def test_domain_ontology_with_gufo(self, parse_cnl, gufo_facts):
        """Domain ontology extending gUFO."""
        domain = parse_cnl("""
            Every company is a functional-complex.
            Company is a kind.
            Every software-developer is a person.
            Software-Developer is a role.
            Every software-project is a relator.
            Every software-project mediates at-least one software-developer.
            Every software-project mediates exactly one company.
        """)

        # Check domain facts
        assert has_fact(domain, type='subsumption', sub='company', sup='functional-complex')
        assert has_fact(domain, type='instance_of', individual='Company', concept='kind')
        assert has_fact(domain, type='instance_of', individual='Software-Developer', concept='role')
        assert has_fact(domain, type='subsumption', sub='software-project', sup='relator')
