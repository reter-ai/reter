"""
Tests for CNL gUFO (Unified Foundational Ontology) Patterns
Based on gufo_overview.md examples
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


class TestGufoTypeDeclarations:
    """Test gUFO type declarations: kind, phase, role, category."""

    def test_person_is_kind(self, get_facts):
        """Person is a kind[gufo]."""
        facts = get_facts("Person is a kind.")
        assert has_fact(facts, type='instance_of', individual='Person', concept='kind')

    def test_adult_is_phase(self, get_facts):
        """Adult is a phase[gufo]."""
        facts = get_facts("Adult is a phase.")
        assert has_fact(facts, type='instance_of', individual='Adult', concept='phase')

    def test_student_is_role(self, get_facts):
        """Student is a role[gufo]."""
        facts = get_facts("Student is a role.")
        assert has_fact(facts, type='instance_of', individual='Student', concept='role')

    def test_physical_object_is_category(self, get_facts):
        """Physical-Object is a category[gufo]."""
        facts = get_facts("Physical-Object is a category.")
        assert has_fact(facts, type='instance_of', individual='Physical-Object', concept='category')

    def test_sub_kind(self, get_facts):
        """Supercarrier is a sub-kind[gufo]."""
        facts = get_facts("Supercarrier is a sub-kind.")
        assert has_fact(facts, type='instance_of', individual='Supercarrier', concept='sub-kind')


class TestGufoEndurantSpecialization:
    """Test specialization of gUFO endurant types."""

    def test_every_person_is_object(self, get_facts):
        """Every person is an object[gufo]."""
        facts = get_facts("Every person is an object.")
        assert has_fact(facts, type='subsumption', sub='person', sup='object')

    def test_every_earthquake_is_event(self, get_facts):
        """Every earthquake is an event[gufo]."""
        facts = get_facts("Every earthquake is an event.")
        assert has_fact(facts, type='subsumption', sub='earthquake', sup='event')

    def test_every_mass_is_quality(self, get_facts):
        """Every mass is a quality[gufo]."""
        facts = get_facts("Every mass is a quality.")
        assert has_fact(facts, type='subsumption', sub='mass', sup='quality')

    def test_every_headache_is_intrinsic_mode(self, get_facts):
        """Every headache is an intrinsic-mode[gufo]."""
        facts = get_facts("Every headache is an intrinsic-mode.")
        assert has_fact(facts, type='subsumption', sub='headache', sup='intrinsic-mode')

    def test_every_marriage_is_relator(self, get_facts):
        """Every marriage is a relator[gufo]."""
        facts = get_facts("Every marriage is a relator.")
        assert has_fact(facts, type='subsumption', sub='marriage', sup='relator')


class TestGufoObjectTypes:
    """Test gUFO object subtypes: functional-complex, collection, quantity."""

    def test_functional_complex(self, get_facts):
        """Challenger is a functional-complex[gufo]."""
        facts = get_facts("Challenger is a functional-complex.")
        assert has_fact(facts, type='instance_of', individual='Challenger', concept='functional-complex')

    def test_every_person_functional_complex(self, get_facts):
        """Every person is a functional-complex[gufo]."""
        facts = get_facts("Every person is a functional-complex.")
        assert has_fact(facts, type='subsumption', sub='person', sup='functional-complex')

    def test_collection(self, get_facts):
        """Every forest is a collection[gufo]."""
        facts = get_facts("Every forest is a collection.")
        assert has_fact(facts, type='subsumption', sub='forest', sup='collection')

    def test_quantity(self, get_facts):
        """Every amount-of-marble is a quantity[gufo]."""
        facts = get_facts("Every amount-of-marble is a quantity.")
        assert has_fact(facts, type='subsumption', sub='amount-of-marble', sup='quantity')


class TestGufoPartWholeRelations:
    """Test gUFO part-whole relations."""

    def test_is_component_of(self, get_facts):
        """Johns-Brain is-component-of[gufo] John."""
        facts = get_facts("Johns-Brain is-component-of John.")
        assert has_fact(facts, type='role_assertion', subject='Johns-Brain',
                       role='is-component-of', object='John')

    def test_is_collection_member_of(self, get_facts):
        """Tree-1 is-collection-member-of[gufo] Forest-1."""
        facts = get_facts("Tree-1 is-collection-member-of Forest-1.")
        assert has_fact(facts, type='role_assertion', subject='Tree-1',
                       role='is-collection-member-of', object='Forest-1')

    def test_is_sub_quantity_of(self, get_facts):
        """Small-Portion is-sub-quantity-of[gufo] Large-Portion."""
        facts = get_facts("Small-Portion is-sub-quantity-of Large-Portion.")
        assert has_fact(facts, type='role_assertion', subject='Small-Portion',
                       role='is-sub-quantity-of', object='Large-Portion')


class TestGufoInheresIn:
    """Test gUFO inheres-in property for aspects."""

    def test_quality_inheres_in(self, get_facts):
        """Moon-Mass inheres-in[gufo] Moon."""
        facts = get_facts("Moon-Mass inheres-in Moon.")
        assert has_fact(facts, type='role_assertion', subject='Moon-Mass',
                       role='inheres-in', object='Moon')

    def test_every_mass_inheres_in_physical_object(self, get_facts):
        """Every mass inheres-in[gufo] exactly-one physical-object."""
        facts = get_facts("Every mass inheres-in exactly-one physical-object.")
        # Should create cardinality restriction
        assert len(facts) >= 1

    def test_headache_inheres_in_person(self, get_facts):
        """Johns-Headache inheres-in[gufo] John."""
        facts = get_facts("Johns-Headache inheres-in John.")
        assert has_fact(facts, type='role_assertion', subject='Johns-Headache',
                       role='inheres-in', object='John')


class TestGufoMediates:
    """Test gUFO mediates property for relators."""

    def test_marriage_mediates_persons(self, get_facts):
        """Every marriage mediates[gufo] a person."""
        facts = get_facts("Every marriage mediates a person.")
        svf = find_fact(facts, type='some_values_from', property='mediates', filler='person')
        assert svf is not None

    def test_specific_marriage_mediates(self, get_facts):
        """John-Mary-Marriage mediates[gufo] John."""
        facts = get_facts("John-Mary-Marriage mediates John.")
        assert has_fact(facts, type='role_assertion', subject='John-Mary-Marriage',
                       role='mediates', object='John')


class TestGufoQualityValues:
    """Test gUFO quality value patterns."""

    def test_has_quality_value(self, get_facts):
        """Moon-Mass has-quality-value[gufo] equal-to 7.34767309E22."""
        facts = get_facts("Moon-Mass has-quality-value equal-to 7.34767309E22.")
        data = find_fact(facts, type='data_assertion', subject='Moon-Mass', property='has-quality-value')
        assert data is not None
        assert data.get('value') == '7.34767309E22'

    def test_has_mass_in_kilograms(self, get_facts):
        """Moon has-mass-in-kilograms equal-to 7.34767309E22."""
        facts = get_facts("Moon has-mass-in-kilograms equal-to 7.34767309E22.")
        # Note: morphology normalizes 'kilograms' -> 'kilogram'
        data = find_fact(facts, type='data_assertion', subject='Moon', property='has-mass-in-kilograms')
        assert data is not None
        assert data.get('value') == '7.34767309E22'


class TestGufoEvents:
    """Test gUFO event patterns."""

    def test_event_instance(self, get_facts):
        """World-Cup-1970-Final is a soccer-match."""
        facts = get_facts("World-Cup-1970-Final is a soccer-match.")
        assert has_fact(facts, type='instance_of', individual='World-Cup-1970-Final',
                       concept='soccer-match')

    def test_every_soccer_match_is_event(self, get_facts):
        """Every soccer-match is an event[gufo]."""
        facts = get_facts("Every soccer-match is an event.")
        assert has_fact(facts, type='subsumption', sub='soccer-match', sup='event')

    def test_participates_in(self, get_facts):
        """Pele participates-in[gufo] World-Cup-1970-Final."""
        facts = get_facts("Pele participates-in World-Cup-1970-Final.")
        # Predicate may be normalized to 'participates-in' or 'participate-in'
        role = find_fact(facts, type='role_assertion', subject='Pele', object='World-Cup-1970-Final')
        assert role is not None

    def test_is_event_proper_part_of(self, get_facts):
        """World-Cup-1970-Final is-event-proper-part-of[gufo] World-Cup-1970."""
        facts = get_facts("World-Cup-1970-Final is-event-proper-part-of World-Cup-1970.")
        assert has_fact(facts, type='role_assertion', subject='World-Cup-1970-Final',
                       role='is-event-proper-part-of', object='World-Cup-1970')


class TestGufoTemporalProperties:
    """Test gUFO temporal data properties."""

    def test_has_begin_date(self, get_facts):
        """The-1985-Mexico-City-Earthquake has-begin-date[gufo] equal-to 1985-09-19."""
        facts = get_facts("The-1985-Mexico-City-Earthquake has-begin-date equal-to 1985-09-19.")
        data = find_fact(facts, type='data_assertion', subject='The-1985-Mexico-City-Earthquake',
                        property='has-begin-date')
        assert data is not None
        assert data.get('value') == '1985-09-19'

    def test_has_end_date(self, get_facts):
        """John-Marys-Wedding has-end-date[gufo] equal-to 2001-12-12."""
        facts = get_facts("John-Marys-Wedding has-end-date equal-to 2001-12-12.")
        data = find_fact(facts, type='data_assertion', subject='John-Marys-Wedding',
                        property='has-end-date')
        assert data is not None
        assert data.get('value') == '2001-12-12'


class TestGufoSituations:
    """Test gUFO situation patterns."""

    def test_quality_value_attribution_situation(self, get_facts):
        """John-Weighs-80-Kg is a quality-value-attribution-situation."""
        facts = get_facts("John-Weighs-80-Kg is a quality-value-attribution-situation.")
        assert has_fact(facts, type='instance_of', individual='John-Weighs-80-Kg',
                       concept='quality-value-attribution-situation')

    def test_temporary_instantiation_situation(self, get_facts):
        """John-Was-A-Child is a temporary-instantiation-situation."""
        facts = get_facts("John-Was-A-Child is a temporary-instantiation-situation.")
        assert has_fact(facts, type='instance_of', individual='John-Was-A-Child',
                       concept='temporary-instantiation-situation')

    def test_temporary_parthood_situation(self, get_facts):
        """John-Has-Original-Heart is a temporary-parthood-situation."""
        facts = get_facts("John-Has-Original-Heart is a temporary-parthood-situation.")
        assert has_fact(facts, type='instance_of', individual='John-Has-Original-Heart',
                       concept='temporary-parthood-situation')


class TestGufoDisjointness:
    """Test gUFO disjoint patterns."""

    def test_no_earthquake_is_tsunami(self, get_facts):
        """No earthquake is a tsunami."""
        facts = get_facts("No earthquake is a tsunami.")
        disjoint = find_fact(facts, type='alldisjoint_classes')
        assert disjoint is not None

    def test_no_phase_is_role(self, get_facts):
        """No phase is a role."""
        facts = get_facts("No phase is a role.")
        disjoint = find_fact(facts, type='alldisjoint_classes')
        assert disjoint is not None


class TestGufoHigherOrderTypes:
    """Test gUFO higher-order type patterns: categorizes, partitions."""

    def test_categorizes(self, get_facts):
        """Person-Role categorizes[gufo] Person."""
        facts = get_facts("Person-Role categorizes Person.")
        # Check for any role_assertion between these individuals
        role = find_fact(facts, type='role_assertion', subject='Person-Role', object='Person')
        assert role is not None

    def test_partitions(self, get_facts):
        """Animal-Species partitions[gufo] Animal."""
        facts = get_facts("Animal-Species partitions Animal.")
        assert has_fact(facts, type='role_assertion', subject='Animal-Species',
                       role='partitions', object='Animal')


class TestGufoRelationshipTypes:
    """Test gUFO relationship type patterns."""

    def test_material_relationship_type(self, get_facts):
        """Is-Married-With is a material-relationship-type."""
        facts = get_facts("Is-Married-With is a material-relationship-type.")
        assert has_fact(facts, type='instance_of', individual='Is-Married-With',
                       concept='material-relationship-type')

    def test_is_derived_from(self, get_facts):
        """Is-Married-With is-derived-from[gufo] Marriage."""
        facts = get_facts("Is-Married-With is-derived-from Marriage.")
        assert has_fact(facts, type='role_assertion', subject='Is-Married-With',
                       role='is-derived-from', object='Marriage')


class TestGufoExtrinsicModes:
    """Test gUFO extrinsic mode patterns."""

    def test_extrinsic_mode_inheres_and_depends(self, get_facts):
        """Johns-Right-To-Service is an extrinsic-mode that inheres-in John."""
        facts = get_facts("Johns-Right-To-Service is an extrinsic-mode that inheres-in John.")
        assert has_fact(facts, type='instance_of', individual='Johns-Right-To-Service',
                       concept='extrinsic-mode')
        assert has_fact(facts, type='role_assertion', subject='Johns-Right-To-Service',
                       role='inheres-in', object='John')

    def test_depends_externally_on(self, get_facts):
        """Johns-Right-To-Service depends-externally-on[gufo] Amazon-Inc."""
        facts = get_facts("Johns-Right-To-Service depends-externally-on Amazon-Inc.")
        # Check for role_assertion between these individuals
        role = find_fact(facts, type='role_assertion', subject='Johns-Right-To-Service', object='Amazon-Inc')
        assert role is not None


class TestGufoPropertySubsumption:
    """Test gUFO property subsumption patterns."""

    def test_property_subsumption(self, get_facts):
        """If X is-mass-of Y then X inheres-in Y."""
        facts = get_facts("If X is-mass-of Y then X inheres-in Y.")
        sub = find_fact(facts, type='sub_property')
        assert sub is not None

    def test_property_chain_transitivity(self, get_facts):
        """If X is-object-proper-part-of something that is-object-proper-part-of Y then X is-object-proper-part-of Y."""
        facts = get_facts("If X is-object-proper-part-of something that is-object-proper-part-of Y then X is-object-proper-part-of Y.")
        # Should create property chain or transitive property
        assert len(facts) >= 1


class TestGufoComplexPatterns:
    """Test complex gUFO patterns combining multiple constructs."""

    def test_type_and_specialization(self, get_facts):
        """Every person is an object. Person is a kind."""
        facts = get_facts("Every person is an object. Person is a kind.")
        assert has_fact(facts, type='subsumption', sub='person', sup='object')
        assert has_fact(facts, type='instance_of', individual='Person', concept='kind')

    def test_role_hierarchy(self, get_facts):
        """Every student is a person. Student is a role."""
        facts = get_facts("Every student is a person. Student is a role.")
        assert has_fact(facts, type='subsumption', sub='student', sup='person')
        assert has_fact(facts, type='instance_of', individual='Student', concept='role')

    def test_quality_with_domain(self, get_facts):
        """Every mass inheres-in something. Every-single-thing is-mass-of nothing-but physical-objects."""
        facts = get_facts("Every mass inheres-in something. Every-single-thing is-mass-of nothing-but physical-objects.")
        svf = find_fact(facts, type='some_values_from', property='inheres-in')
        avf = find_fact(facts, type='all_values_from', property='is-mass-of', filler='physical-object')
        assert svf is not None
        assert avf is not None


class TestGufoEnumeratedValues:
    """Test gUFO enumerated quality value patterns."""

    def test_oneOf_pattern(self, get_facts):
        """Something is a shirt-size if-and-only-if-it is either S, M, L or XL."""
        facts = get_facts("Something is a shirt-size if-and-only-if-it is either S, M, L or XL.")
        # Should create one_of or enumeration pattern
        assert len(facts) >= 1

    def test_individual_in_enumeration(self, get_facts):
        """S is a shirt-size."""
        facts = get_facts("S is a shirt-size.")
        assert has_fact(facts, type='instance_of', individual='S', concept='shirt-size')


class TestGufoDatetimeWithTimestamp:
    """Test gUFO datetime patterns with full timestamps."""

    @pytest.mark.xfail(reason="Full datetime with time component not yet implemented")
    def test_has_begin_date_with_time(self, get_facts):
        """The-1985-Mexico-City-Earthquake has-begin-date equal-to 1985-09-19T131750Z."""
        facts = get_facts("The-1985-Mexico-City-Earthquake has-begin-date equal-to 1985-09-19T131750Z.")
        data = find_fact(facts, type='data_assertion', subject='The-1985-Mexico-City-Earthquake',
                        property='has-begin-date')
        assert data is not None
        assert 'T' in data.get('value', '')

    @pytest.mark.xfail(reason="Full datetime with timezone not yet implemented")
    def test_datetime_with_timezone(self, get_facts):
        """Johns-Headache has-begin-date equal-to 2019-11-19T141450Z."""
        facts = get_facts("Johns-Headache has-begin-date equal-to 2019-11-19T141450Z.")
        data = find_fact(facts, type='data_assertion', subject='Johns-Headache',
                        property='has-begin-date')
        assert data is not None


class TestGufoConjunctions:
    """Test gUFO patterns with 'and' conjunctions in assertions."""

    def test_instance_with_role_conjunction(self, get_facts):
        """Johns-Brain is a brain and is-component-of John."""
        facts = get_facts("Johns-Brain is a brain and is-component-of John.")
        # Creates intersection concept + role_assertion
        assert has_fact(facts, type='role_assertion', subject='Johns-Brain',
                       role='is-component-of', object='John')
        # Instance is of intersection type (combining 'brain' and role restriction)
        inst = find_fact(facts, type='instance_of', individual='Johns-Brain')
        assert inst is not None
        assert has_fact(facts, type='intersection')

    def test_instance_with_data_conjunction(self, get_facts):
        """Moon is a physical-object and has-mass-in-kilograms equal-to 7.34767309E22."""
        facts = get_facts("Moon is a physical-object and has-mass-in-kilograms equal-to 7.34767309E22.")
        # Note: morphology normalizes 'kilograms' -> 'kilogram'
        data = find_fact(facts, type='data_assertion', subject='Moon', property='has-mass-in-kilograms')
        assert data is not None
        # Instance is of intersection type
        inst = find_fact(facts, type='instance_of', individual='Moon')
        assert inst is not None

    def test_quality_with_inheres_and_value(self, get_facts):
        """Moon-Mass is a mass that inheres-in Moon and has-quality-value equal-to 7.34767309E22."""
        facts = get_facts("Moon-Mass is a mass that inheres-in Moon and has-quality-value equal-to 7.34767309E22.")
        assert has_fact(facts, type='instance_of', individual='Moon-Mass', concept='mass')
        assert has_fact(facts, type='role_assertion', subject='Moon-Mass',
                       role='inheres-in', object='Moon')
        data = find_fact(facts, type='data_assertion', subject='Moon-Mass', property='has-quality-value')
        assert data is not None

    def test_multiple_data_properties(self, get_facts):
        """Moons-Mass has-mass-in-kilograms equal-to 7.34767309E22 and has-mass-in-short-tons equal-to 8.1E19."""
        facts = get_facts("Moons-Mass has-mass-in-kilograms equal-to 7.34767309E22 and has-mass-in-short-tons equal-to 8.1E19.")
        kg = find_fact(facts, type='data_assertion', subject='Moons-Mass', property='has-mass-in-kilograms')
        tons = find_fact(facts, type='data_assertion', subject='Moons-Mass', property='has-mass-in-short-tons')
        assert kg is not None
        assert tons is not None


class TestGufoEventDependencies:
    """Test gUFO event dependency patterns."""

    def test_depends_historically_on(self, get_facts):
        """World-Cup-1970-Final depends-historically-on Brazil-Uruguay-World-Cup-1970-Semi-Final."""
        facts = get_facts("World-Cup-1970-Final depends-historically-on Brazil-Uruguay-World-Cup-1970-Semi-Final.")
        role = find_fact(facts, type='role_assertion', subject='World-Cup-1970-Final',
                        object='Brazil-Uruguay-World-Cup-1970-Semi-Final')
        assert role is not None

    def test_is_created_in(self, get_facts):
        """John-Marys-Marriage is-created-in John-Marys-Wedding."""
        facts = get_facts("John-Marys-Marriage is-created-in John-Marys-Wedding.")
        role = find_fact(facts, type='role_assertion', subject='John-Marys-Marriage',
                        object='John-Marys-Wedding')
        assert role is not None

    def test_is_terminated_in(self, get_facts):
        """Challenger is-terminated-in Challengers-10-Th-Flight."""
        facts = get_facts("Challenger is-terminated-in Challengers-10-Th-Flight.")
        role = find_fact(facts, type='role_assertion', subject='Challenger',
                        object='Challengers-10-Th-Flight')
        assert role is not None

    def test_is_manifested_in(self, get_facts):
        """Challenger-Right-Booster-Seal-Flaw is-manifested-in Challengers-10-Th-Launch."""
        facts = get_facts("Challenger-Right-Booster-Seal-Flaw is-manifested-in Challengers-10-Th-Launch.")
        role = find_fact(facts, type='role_assertion', subject='Challenger-Right-Booster-Seal-Flaw',
                        object='Challengers-10-Th-Launch')
        assert role is not None


class TestGufoSituationDetails:
    """Test gUFO situation property patterns."""

    def test_concerns_quality_type(self, get_facts):
        """John-Weighs-80-Kg concerns-quality-type Mass."""
        facts = get_facts("John-Weighs-80-Kg concerns-quality-type Mass.")
        role = find_fact(facts, type='role_assertion', subject='John-Weighs-80-Kg',
                        object='Mass')
        assert role is not None

    def test_concerns_quality_value(self, get_facts):
        """John-Weighs-80-Kg concerns-quality-value equal-to 80.0."""
        facts = get_facts("John-Weighs-80-Kg concerns-quality-value equal-to 80.0.")
        data = find_fact(facts, type='data_assertion', subject='John-Weighs-80-Kg',
                        property='concerns-quality-value')
        assert data is not None

    def test_concerns_non_rigid_type(self, get_facts):
        """John-Was-A-Child concerns-non-rigid-type Child."""
        facts = get_facts("John-Was-A-Child concerns-non-rigid-type Child.")
        role = find_fact(facts, type='role_assertion', subject='John-Was-A-Child',
                        object='Child')
        assert role is not None

    def test_concerns_temporary_whole(self, get_facts):
        """John-Has-Original-Heart concerns-temporary-whole John."""
        facts = get_facts("John-Has-Original-Heart concerns-temporary-whole John.")
        role = find_fact(facts, type='role_assertion', subject='John-Has-Original-Heart',
                        object='John')
        assert role is not None


class TestGufoQualifiedRelations:
    """Test gUFO qualified relation patterns."""

    def test_stands_in_qualified_attribution(self, get_facts):
        """John stands-in-qualified-attribution John-Weighs-80-Kg."""
        facts = get_facts("John stands-in-qualified-attribution John-Weighs-80-Kg.")
        role = find_fact(facts, type='role_assertion', subject='John',
                        object='John-Weighs-80-Kg')
        assert role is not None

    def test_stands_in_qualified_parthood(self, get_facts):
        """Johns-Heart stands-in-qualified-parthood John-Has-Original-Heart."""
        facts = get_facts("Johns-Heart stands-in-qualified-parthood John-Has-Original-Heart.")
        role = find_fact(facts, type='role_assertion', subject='Johns-Heart',
                        object='John-Has-Original-Heart')
        assert role is not None

    def test_stands_in_qualified_constitution(self, get_facts):
        """Original-Quantity-Of-Marble stands-in-qualified-constitution Venus-Has-Arms."""
        facts = get_facts("Original-Quantity-Of-Marble stands-in-qualified-constitution Venus-Has-Arms.")
        role = find_fact(facts, type='role_assertion', subject='Original-Quantity-Of-Marble',
                        object='Venus-Has-Arms')
        assert role is not None

    def test_concerns_constituted_endurant(self, get_facts):
        """Venus-Has-Arms concerns-constituted-endurant Venus-Of-Milo."""
        facts = get_facts("Venus-Has-Arms concerns-constituted-endurant Venus-Of-Milo.")
        role = find_fact(facts, type='role_assertion', subject='Venus-Has-Arms',
                        object='Venus-Of-Milo')
        assert role is not None


class TestGufoTemporaryRelationships:
    """Test gUFO temporary relationship situation patterns."""

    def test_temporary_relationship_situation(self, get_facts):
        """John-Is-Heavier is a temporary-relationship-situation."""
        facts = get_facts("John-Is-Heavier is a temporary-relationship-situation.")
        assert has_fact(facts, type='instance_of', individual='John-Is-Heavier',
                       concept='temporary-relationship-situation')

    def test_concerns_relationship_type(self, get_facts):
        """John-Is-Heavier concerns-relationship-type Is-Heavier-Than."""
        facts = get_facts("John-Is-Heavier concerns-relationship-type Is-Heavier-Than.")
        role = find_fact(facts, type='role_assertion', subject='John-Is-Heavier',
                        object='Is-Heavier-Than')
        assert role is not None

    def test_stands_in_qualified_relationship(self, get_facts):
        """John stands-in-qualified-relationship John-Is-Heavier."""
        facts = get_facts("John stands-in-qualified-relationship John-Is-Heavier.")
        role = find_fact(facts, type='role_assertion', subject='John',
                        object='John-Is-Heavier')
        assert role is not None


class TestGufoCausation:
    """Test gUFO causation patterns."""

    def test_is_brought_about_by(self, get_facts):
        """John-To-Paul-Heart-Transplant is-brought-about-by Paul-Has-Johns-Heart."""
        facts = get_facts("John-To-Paul-Heart-Transplant is-brought-about-by Paul-Has-Johns-Heart.")
        role = find_fact(facts, type='role_assertion', subject='John-To-Paul-Heart-Transplant',
                        object='Paul-Has-Johns-Heart')
        assert role is not None

    def test_contributes_to_trigger(self, get_facts):
        """Host-1234-Vulnerable contributes-to-trigger Wanna-Cry-Attack."""
        facts = get_facts("Host-1234-Vulnerable contributes-to-trigger Wanna-Cry-Attack.")
        role = find_fact(facts, type='role_assertion', subject='Host-1234-Vulnerable',
                        object='Wanna-Cry-Attack')
        assert role is not None


class TestGufoReifiedValues:
    """Test gUFO reified quality value patterns."""

    def test_quality_value_type(self, get_facts):
        """Every color-value-in-rgb is a quality-value."""
        facts = get_facts("Every color-value-in-rgb is a quality-value.")
        assert has_fact(facts, type='subsumption', sub='color-value-in-rgb', sup='quality-value')

    def test_has_reified_quality_value(self, get_facts):
        """Painting-Color has-reified-quality-value Painting-Color-Value."""
        facts = get_facts("Painting-Color has-reified-quality-value Painting-Color-Value.")
        role = find_fact(facts, type='role_assertion', subject='Painting-Color',
                        object='Painting-Color-Value')
        assert role is not None

    @pytest.mark.xfail(reason="has-value-component data property subsumption not yet implemented")
    def test_has_value_component(self, get_facts):
        """If X has-red-value-component equal-to Y then X has-value-component equal-to Y."""
        facts = get_facts("If X has-red-value-component equal-to Y then X has-value-component equal-to Y.")
        # Should create property subsumption
        assert len(facts) >= 1

    def test_color_value_components(self, get_facts):
        """Yves-Klein-Blue has-red-value-component equal-to 0."""
        facts = get_facts("Yves-Klein-Blue has-red-value-component equal-to 0.")
        data = find_fact(facts, type='data_assertion', subject='Yves-Klein-Blue',
                        property='has-red-value-component')
        assert data is not None
        assert data.get('value') == '0'


class TestGufoAspectProperPart:
    """Test gUFO aspect proper part patterns."""

    def test_is_aspect_proper_part_of(self, get_facts):
        """Johns-Right-To-Service is-aspect-proper-part-of John-Amazon-Agreement."""
        facts = get_facts("Johns-Right-To-Service is-aspect-proper-part-of John-Amazon-Agreement.")
        role = find_fact(facts, type='role_assertion', subject='Johns-Right-To-Service',
                        role='is-aspect-proper-part-of', object='John-Amazon-Agreement')
        assert role is not None


class TestGufoComplexExtrinsicModes:
    """Test complex gUFO extrinsic mode patterns with multiple properties."""

    def test_extrinsic_mode_full_pattern(self, get_facts):
        """Johns-Right-To-Service is an extrinsic-mode that inheres-in John and depends-externally-on Amazon-Inc."""
        facts = get_facts("Johns-Right-To-Service is an extrinsic-mode that inheres-in John and depends-externally-on Amazon-Inc.")
        assert has_fact(facts, type='instance_of', individual='Johns-Right-To-Service',
                       concept='extrinsic-mode')
        assert has_fact(facts, type='role_assertion', subject='Johns-Right-To-Service',
                       role='inheres-in', object='John')
        role = find_fact(facts, type='role_assertion', subject='Johns-Right-To-Service',
                        object='Amazon-Inc')
        assert role is not None
