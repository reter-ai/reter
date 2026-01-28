"""
Tests for CNL Parser with gUFO Ontology

This test file loads the gUFO (Unified Foundational Ontology) and tests
that domain-specific examples can be parsed correctly when built on top of gUFO.
"""
import pytest
from pathlib import Path
import reter_core.owl_rete_cpp as cpp


# Path to gUFO ontology
GUFO_PATH = Path(__file__).parent / "gufo.cnl"


@pytest.fixture(scope="module")
def gufo_facts():
    """Load gUFO ontology facts."""
    with open(GUFO_PATH, 'r') as f:
        content = f.read()
    result = cpp.parse_cnl(content)
    return result.facts


@pytest.fixture
def parse_with_gufo(gufo_facts):
    """Parse CNL and return combined facts with gUFO ontology."""
    def _parse(cnl_text):
        result = cpp.parse_cnl(cnl_text)
        # Return list of fact dicts for easier testing
        facts = []
        for f in result.facts:
            fact_dict = {}
            for key in ['type', 'sub', 'sup', 'individual', 'concept', 'subject',
                        'role', 'object', 'c1', 'c2', 'property', 'filler',
                        'cardinality', 'id', 'class', 'i1', 'i2', 'modality',
                        'chain', 'super_property', 'value', 'datatype']:
                val = f.get(key)
                if val:
                    fact_dict[key] = val
            facts.append(fact_dict)
        return facts
    return _parse


def find_fact(facts, **criteria):
    """Find a fact matching all criteria."""
    for f in facts:
        if all(f.get(k) == v for k, v in criteria.items()):
            return f
    return None


def has_fact(facts, **criteria):
    """Check if a fact matching criteria exists."""
    return find_fact(facts, **criteria) is not None


class TestGufoLoading:
    """Tests for loading the gUFO ontology."""

    def test_gufo_file_exists(self):
        """Verify gufo.cnl exists."""
        assert GUFO_PATH.exists(), f"gUFO ontology not found at {GUFO_PATH}"

    def test_gufo_parses(self, gufo_facts):
        """Verify gUFO ontology parses successfully."""
        assert len(gufo_facts) > 0

    def test_gufo_subsumptions(self, gufo_facts):
        """Verify gUFO contains expected subsumption facts."""
        # Convert to dict format for testing
        facts = []
        for f in gufo_facts:
            facts.append({'type': f.get('type'), 'sub': f.get('sub'), 'sup': f.get('sup')})

        # Core gUFO hierarchy
        assert has_fact(facts, type='subsumption', sub='endurant', sup='concrete-individual')
        assert has_fact(facts, type='subsumption', sub='object', sup='endurant')
        assert has_fact(facts, type='subsumption', sub='aspect', sup='endurant')
        assert has_fact(facts, type='subsumption', sub='event', sup='concrete-individual')

    def test_gufo_disjoints(self, gufo_facts):
        """Verify gUFO contains expected disjoint axioms."""
        type_counts = {}
        for f in gufo_facts:
            t = f.get('type')
            type_counts[t] = type_counts.get(t, 0) + 1

        assert type_counts.get('alldisjoint_classes', 0) > 0


class TestGufoPersonExample:
    """Test Person domain extending gUFO."""

    def test_person_is_functional_complex(self, parse_with_gufo):
        """Person as a functional complex (gUFO pattern)."""
        facts = parse_with_gufo("Every person is a functional-complex.")
        assert has_fact(facts, type='subsumption', sub='person', sup='functional-complex')

    def test_student_role(self, parse_with_gufo):
        """Student as a role (gUFO anti-rigid type)."""
        facts = parse_with_gufo("Every student is a person.")
        assert has_fact(facts, type='subsumption', sub='student', sup='person')

    def test_person_instance(self, parse_with_gufo):
        """John as an instance of person."""
        facts = parse_with_gufo("John is a person.")
        assert has_fact(facts, type='instance_of', individual='John', concept='person')

    def test_person_with_quality(self, parse_with_gufo):
        """Person with quality (weight as intrinsic aspect)."""
        # Quality inheres in person
        facts = parse_with_gufo("Johns-Weight inheres-in John.")
        assert has_fact(facts, type='role_assertion', subject='Johns-Weight',
                       role='inheres-in', object='John')

    def test_person_age(self, parse_with_gufo):
        """Person with data property."""
        facts = parse_with_gufo("John has-age equal-to 30.")
        assert has_fact(facts, type='data_assertion', subject='John',
                       property='has-age', value='30')


class TestGufoEventExample:
    """Test Event domain extending gUFO."""

    def test_meeting_is_event(self, parse_with_gufo):
        """Meeting as an event type."""
        facts = parse_with_gufo("Every meeting is an event.")
        assert has_fact(facts, type='subsumption', sub='meeting', sup='event')

    def test_meeting_instance(self, parse_with_gufo):
        """Specific meeting instance."""
        facts = parse_with_gufo("Board-Meeting-2024-01 is a meeting.")
        assert has_fact(facts, type='instance_of',
                       individual='Board-Meeting-2024-01', concept='meeting')

    def test_participation_pattern(self, parse_with_gufo):
        """Participation in event (gUFO pattern)."""
        facts = parse_with_gufo("Johns-Participation is a participation.")
        assert has_fact(facts, type='instance_of',
                       individual='Johns-Participation', concept='participation')


class TestGufoRelatorExample:
    """Test Relator patterns from gUFO."""

    def test_marriage_is_relator(self, parse_with_gufo):
        """Marriage as a relator type."""
        facts = parse_with_gufo("Every marriage is a relator.")
        assert has_fact(facts, type='subsumption', sub='marriage', sup='relator')

    def test_marriage_instance(self, parse_with_gufo):
        """Specific marriage instance."""
        facts = parse_with_gufo("Johns-Marriage is a marriage.")
        assert has_fact(facts, type='instance_of',
                       individual='Johns-Marriage', concept='marriage')

    def test_marriage_mediates(self, parse_with_gufo):
        """Marriage mediates persons (gUFO pattern)."""
        facts = parse_with_gufo("Johns-Marriage mediates John.")
        assert has_fact(facts, type='role_assertion',
                       subject='Johns-Marriage', role='mediates', object='John')


class TestGufoQualityExample:
    """Test Quality patterns from gUFO."""

    def test_weight_is_quality(self, parse_with_gufo):
        """Weight as a quality type."""
        facts = parse_with_gufo("Every weight is a quality.")
        assert has_fact(facts, type='subsumption', sub='weight', sup='quality')

    def test_quality_instance_with_value(self, parse_with_gufo):
        """Quality instance with value."""
        facts = parse_with_gufo("Johns-Weight has-quality-value equal-to 80.")
        assert has_fact(facts, type='data_assertion', subject='Johns-Weight',
                       property='has-quality-value', value='80')


class TestGufoSituationExample:
    """Test Situation patterns from gUFO."""

    def test_situation_type(self, parse_with_gufo):
        """Custom situation type."""
        facts = parse_with_gufo("Every employment-situation is a temporary-relationship-situation.")
        assert has_fact(facts, type='subsumption',
                       sub='employment-situation', sup='temporary-relationship-situation')

    def test_situation_instance(self, parse_with_gufo):
        """Situation instance."""
        facts = parse_with_gufo("Johns-Employment-At-Nasa is an employment-situation.")
        assert has_fact(facts, type='instance_of',
                       individual='Johns-Employment-At-Nasa', concept='employment-situation')


class TestGufoCollectionExample:
    """Test Collection patterns from gUFO."""

    def test_team_is_collection(self, parse_with_gufo):
        """Team as a variable collection."""
        facts = parse_with_gufo("Every team is a variable-collection.")
        assert has_fact(facts, type='subsumption', sub='team', sup='variable-collection')

    def test_team_instance(self, parse_with_gufo):
        """Team instance."""
        facts = parse_with_gufo("The-Beatles is a team.")
        assert has_fact(facts, type='instance_of',
                       individual='The-Beatles', concept='team')


class TestGufoPropertyAxioms:
    """Test property axioms from gUFO."""

    def test_transitivity_parsed(self):
        """Verify transitivity axiom parses."""
        result = cpp.parse_cnl(
            "If X is-proper-part-of something that is-proper-part-of Y "
            "then X is-proper-part-of Y."
        )
        facts = [{'type': f.get('type'), 'super_property': f.get('super_property')}
                 for f in result.facts]
        assert has_fact(facts, type='property_chain', super_property='is-proper-part-of')

    def test_asymmetry_parsed(self):
        """Verify asymmetry axiom parses."""
        result = cpp.parse_cnl(
            "If X inheres-in Y then Y does-not inhere-in X."
        )
        facts = [{'type': f.get('type')} for f in result.facts]
        assert has_fact(facts, type='asymmetric_property')

    def test_irreflexivity_parsed(self):
        """Verify irreflexivity axiom parses."""
        result = cpp.parse_cnl("Nothing inheres-in itself.")
        facts = [{'type': f.get('type')} for f in result.facts]
        assert has_fact(facts, type='has_self')


class TestGufoComplexPatterns:
    """Test complex gUFO patterns."""

    def test_qualified_parthood_situation(self, parse_with_gufo):
        """Temporary parthood with situation."""
        facts = parse_with_gufo("""
            Uk-In-Eu is a temporary-parthood-situation.
            Uk-In-Eu concerns-temporary-whole European-Union.
        """)
        assert has_fact(facts, type='instance_of',
                       individual='Uk-In-Eu', concept='temporary-parthood-situation')
        assert has_fact(facts, type='role_assertion',
                       subject='Uk-In-Eu', role='concerns-temporary-whole',
                       object='European-Union')

    def test_quality_value_attribution(self, parse_with_gufo):
        """Quality value attribution situation."""
        facts = parse_with_gufo("""
            Tysons-Weight-2020 is a quality-value-attribution-situation.
            Tysons-Weight-2020 has-quality-value equal-to 100.
        """)
        assert has_fact(facts, type='instance_of',
                       individual='Tysons-Weight-2020',
                       concept='quality-value-attribution-situation')
        assert has_fact(facts, type='data_assertion',
                       subject='Tysons-Weight-2020',
                       property='has-quality-value', value='100')

    def test_extrinsic_mode_pattern(self, parse_with_gufo):
        """Extrinsic mode (one-sided relationship)."""
        facts = parse_with_gufo("""
            Every admiration is an extrinsic-mode.
            Johns-Admiration-For-Obama is an admiration.
            Johns-Admiration-For-Obama inheres-in John.
            Johns-Admiration-For-Obama depends-externally-on Obama.
        """)
        assert has_fact(facts, type='subsumption', sub='admiration', sup='extrinsic-mode')
        assert has_fact(facts, type='instance_of',
                       individual='Johns-Admiration-For-Obama', concept='admiration')
        assert has_fact(facts, type='role_assertion',
                       subject='Johns-Admiration-For-Obama', role='inheres-in',
                       object='John')


class TestGufoRealWorldExample:
    """Test real-world domain ontology using gUFO."""

    def test_organization_ontology(self, parse_with_gufo):
        """Organization domain ontology."""
        domain_ontology = """
            Every organization is a functional-complex.
            Every company is an organization.
            Every employee is a person.
            Every employment is a relator.
            Every employment mediates something.
            Acme-Corp is a company.
            John is an employee.
            Johns-Employment is an employment.
            Johns-Employment mediates John.
            Johns-Employment mediates Acme-Corp.
        """
        facts = parse_with_gufo(domain_ontology)

        # Verify class hierarchy
        assert has_fact(facts, type='subsumption', sub='organization', sup='functional-complex')
        assert has_fact(facts, type='subsumption', sub='company', sup='organization')
        assert has_fact(facts, type='subsumption', sub='employee', sup='person')

        # Verify instances
        assert has_fact(facts, type='instance_of', individual='Acme-Corp', concept='company')
        assert has_fact(facts, type='instance_of', individual='John', concept='employee')

        # Verify relator pattern
        assert has_fact(facts, type='role_assertion',
                       subject='Johns-Employment', role='mediates', object='John')
        assert has_fact(facts, type='role_assertion',
                       subject='Johns-Employment', role='mediates', object='Acme-Corp')

    def test_event_domain(self, parse_with_gufo):
        """Event-centric domain ontology."""
        domain_ontology = """
            Every soccer-match is an event.
            Every goal is an event.
            World-Cup-Final-2022 is a soccer-match.
            Messis-Goal is a goal.
            Messis-Goal is-event-proper-part-of World-Cup-Final-2022.
        """
        facts = parse_with_gufo(domain_ontology)

        assert has_fact(facts, type='subsumption', sub='soccer-match', sup='event')
        assert has_fact(facts, type='instance_of',
                       individual='World-Cup-Final-2022', concept='soccer-match')
        assert has_fact(facts, type='role_assertion',
                       subject='Messis-Goal', role='is-event-proper-part-of',
                       object='World-Cup-Final-2022')
