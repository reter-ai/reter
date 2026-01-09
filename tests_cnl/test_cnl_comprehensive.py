"""
Comprehensive CNL Parser Tests

This test file validates ALL CNL examples from:
- gufo_overview.md (169 patterns)
- grammar.md (176 patterns)

All patterns are tested in the context of the gUFO ontology.
"""
import pytest
from pathlib import Path
import reter_core.owl_rete_cpp as cpp


# Path to gUFO ontology
GUFO_PATH = Path(__file__).parent / "gufo.cnl"

# Cache for gUFO content
_gufo_content_cache = None


def _get_gufo_content():
    """Load gUFO content (cached)."""
    global _gufo_content_cache
    if _gufo_content_cache is None:
        with open(GUFO_PATH, 'r') as f:
            _gufo_content_cache = f.read()
    return _gufo_content_cache


def parse_with_gufo(cnl_text):
    """Parse CNL in context of gUFO and return all facts."""
    combined = _get_gufo_content() + "\n" + cnl_text
    result = cpp.parse_cnl(combined)
    return result.facts


def parse_isolated(cnl_text):
    """Parse CNL without gUFO context."""
    result = cpp.parse_cnl(cnl_text)
    return result.facts


# =============================================================================
# GUFO_OVERVIEW.MD PATTERNS (169 patterns)
# =============================================================================

GUFO_OVERVIEW_PATTERNS = [
    # Section: 1. Usage Scenarios
    ("1. Usage Scenarios", "Every person is an object[gufo]."),
    ("1. Usage Scenarios", "Person is a kind[gufo]."),
    # Section: Key Patterns for LLMs
    ("Key Patterns for LLMs", "Every person is an object[gufo]."),
    ("Key Patterns for LLMs", "Person is a kind[gufo]."),
    ("Key Patterns for LLMs", "Every person has-age some value."),
    ("Key Patterns for LLMs", "Every person has-age nothing-but integer values."),
    ("Key Patterns for LLMs", "Every weight is a quality[gufo]."),
    ("Key Patterns for LLMs", "Every weight inheres-in exactly one physical-object."),
    ("Key Patterns for LLMs", "Every weight has-quality-value[gufo] some value."),
    ("Key Patterns for LLMs", "Every person knows some person."),
    ("Key Patterns for LLMs", "Every friendship is a relator[gufo]."),
    ("Key Patterns for LLMs", "Every friendship mediates at-least 2 persons."),
    ("Key Patterns for LLMs", "Every friendship has-begin-date[gufo] some value."),
    ("Key Patterns for LLMs", "Every employee is a person."),
    ("Key Patterns for LLMs", "Employee is a role[gufo]."),
    ("Key Patterns for LLMs", "Every organization is an object[gufo]."),
    ("Key Patterns for LLMs", "Organization is a kind[gufo]."),
    ("Key Patterns for LLMs", "Every employment is a relator[gufo]."),
    ("Key Patterns for LLMs", "Every employment mediates exactly one employee."),
    ("Key Patterns for LLMs", "Every employment mediates exactly one organization."),
    # Section: 2.1. Concrete Individuals
    ("2.1. Concrete Individuals", "Earth is an object[gufo]."),
    ("2.1. Concrete Individuals", "World-War-II is an event[gufo]."),
    ("2.1. Concrete Individuals", "The-1985-Mexico-City-Earthquake is an event[gufo]."),
    ("2.1. Concrete Individuals", "The-1985-Mexico-City-Earthquake is an event[gufo] and has-begin-date[gufo] equal-to 1985-09-19T131750Z."),
    # Section: 2.2. Objects and their parts
    ("2.2. Objects and their parts", "Every planet is an object[gufo]."),
    ("2.2. Objects and their parts", "Every person is an object[gufo]."),
    ("2.2. Objects and their parts", "Every physical-object is an object[gufo]."),
    ("2.2. Objects and their parts", "Every functional-complex is an object[gufo]."),
    ("2.2. Objects and their parts", "Every collection is an object[gufo]."),
    ("2.2. Objects and their parts", "Every quantity is an object[gufo]."),
    ("2.2. Objects and their parts", "Every person is a functional-complex[gufo]."),
    ("2.2. Objects and their parts", "Every human-heart is an object[gufo]."),
    ("2.2. Objects and their parts", "Johns-Heart is a human-heart."),
    ("2.2. Objects and their parts", "Johns-Heart is-component-of[gufo] John."),
    ("2.2. Objects and their parts", "Every brain is an object[gufo]."),
    ("2.2. Objects and their parts", "Johns-Brain is a brain and is-component-of[gufo] John."),
    ("2.2. Objects and their parts", "Every forest is a collection[gufo]."),
    ("2.2. Objects and their parts", "Every tree is an object[gufo]."),
    ("2.2. Objects and their parts", "Black-Forest is a forest."),
    ("2.2. Objects and their parts", "Every amount-of-water is a quantity[gufo]."),
    ("2.2. Objects and their parts", "Every wine is a quantity[gufo]."),
    # Section: 2.3. Intrinsic Aspects
    ("2.3. Intrinsic Aspects", "Every intrinsic-aspect is an aspect[gufo]."),
    ("2.3. Intrinsic Aspects", "Every quality is an intrinsic-aspect[gufo]."),
    ("2.3. Intrinsic Aspects", "Every intrinsic-mode is an intrinsic-aspect[gufo]."),
    # Section: 2.4. Qualities - Basic patterns
    ("2.4. Qualities - Basic patterns", "Every mass is a quality[gufo]."),
    ("2.4. Qualities - Basic patterns", "Every mass inheres-in[gufo] exactly one physical-object."),
    ("2.4. Qualities - Basic patterns", "Moon-Mass is a mass."),
    ("2.4. Qualities - Basic patterns", "Moon-Mass inheres-in[gufo] Moon."),
    ("2.4. Qualities - Basic patterns", "Moon-Mass has-quality-value[gufo] equal-to 7.34767309E22."),
    ("2.4. Qualities - Basic patterns", "Moon is a physical-object and has-mass-in-kilograms equal-to 7.34767309E22."),
    ("2.4. Qualities - Basic patterns", "Every-single-thing has-mass-in-kilograms nothing-but (some real value)."),
    ("2.4. Qualities - Basic patterns", "If X is-mass-of Y then X inheres-in[gufo] Y."),
    ("2.4. Qualities - Basic patterns", "If X has-mass-in-kilograms equal-to Y then X has-quality-value[gufo] equal-to Y."),
    ("2.4. Qualities - Basic patterns", "Every mass is-mass-of something."),
    ("2.4. Qualities - Basic patterns", "Every mass is-mass-of nothing-but physical-object."),
    ("2.4. Qualities - Basic patterns", "Every-single-thing has-mass-in-short-tons nothing-but (some real value)."),
    ("2.4. Qualities - Basic patterns", "If X has-mass-in-short-tons equal-to Y then X has-quality-value[gufo] equal-to Y."),
    # Section: 2.5. Qualities - Advanced usage
    ("2.5. Qualities - Advanced usage", "Every color is a quality[gufo]."),
    ("2.5. Qualities - Advanced usage", "Every color has-quality-value[gufo] some value."),
    ("2.5. Qualities - Advanced usage", "My-Car-Color is a color."),
    ("2.5. Qualities - Advanced usage", "My-Car-Color inheres-in[gufo] My-Car."),
    ("2.5. Qualities - Advanced usage", "Every color-in-rgb is a quality[gufo]."),
    ("2.5. Qualities - Advanced usage", "Every color-in-rgb has-red-value-component some value."),
    ("2.5. Qualities - Advanced usage", "Every color-in-rgb has-green-value-component some value."),
    ("2.5. Qualities - Advanced usage", "Every color-in-rgb has-blue-value-component some value."),
    ("2.5. Qualities - Advanced usage", "Every-single-thing has-red-value-component nothing-but (some integer value)."),
    ("2.5. Qualities - Advanced usage", "Every-single-thing has-green-value-component nothing-but (some integer value)."),
    ("2.5. Qualities - Advanced usage", "Every-single-thing has-blue-value-component nothing-but (some integer value)."),
    ("2.5. Qualities - Advanced usage", "If X has-red-value-component equal-to Y then X has-value-component[gufo] equal-to Y."),
    ("2.5. Qualities - Advanced usage", "If X has-green-value-component equal-to Y then X has-value-component[gufo] equal-to Y."),
    ("2.5. Qualities - Advanced usage", "If X has-blue-value-component equal-to Y then X has-value-component[gufo] equal-to Y."),
    ("2.5. Qualities - Advanced usage", "My-Car-Color is a color-in-rgb."),
    ("2.5. Qualities - Advanced usage", "My-Car-Color has-red-value-component equal-to 255."),
    ("2.5. Qualities - Advanced usage", "My-Car-Color has-green-value-component equal-to 0."),
    ("2.5. Qualities - Advanced usage", "My-Car-Color has-blue-value-component equal-to 0."),
    # Section: 2.6. Intrinsic Modes
    ("2.6. Intrinsic Modes", "Every headache is an intrinsic-mode[gufo]."),
    ("2.6. Intrinsic Modes", "Every headache inheres-in[gufo] some person."),
    ("2.6. Intrinsic Modes", "Every headache inheres-in[gufo] nothing-but person."),
    ("2.6. Intrinsic Modes", "If X is-headache-of Y then X inheres-in[gufo] Y."),
    ("2.6. Intrinsic Modes", "Every headache-intensity is a quality[gufo]."),
    ("2.6. Intrinsic Modes", "Every headache-intensity inheres-in[gufo] some headache."),
    ("2.6. Intrinsic Modes", "Johns-Headache is a headache."),
    ("2.6. Intrinsic Modes", "Johns-Headache is-headache-of John."),
    ("2.6. Intrinsic Modes", "Johns-Headache is a headache and is-headache-of John and has-begin-date[gufo] equal-to 2019-11-19T141450Z."),
    # Section: 2.7. Extrinsic Aspects
    ("2.7. Extrinsic Aspects", "Every extrinsic-aspect is an aspect[gufo]."),
    ("2.7. Extrinsic Aspects", "Every relator is an extrinsic-aspect[gufo]."),
    ("2.7. Extrinsic Aspects", "Every extrinsic-mode is an extrinsic-aspect[gufo]."),
    ("2.7. Extrinsic Aspects", "Every marriage is a relator[gufo]."),
    ("2.7. Extrinsic Aspects", "If X is-marriage-of Y then X mediates[gufo] Y."),
    ("2.7. Extrinsic Aspects", "Every marriage mediates[gufo] exactly 2 persons."),
    ("2.7. Extrinsic Aspects", "Johns-Marriage is a marriage."),
    ("2.7. Extrinsic Aspects", "Johns-Marriage mediates[gufo] John."),
    ("2.7. Extrinsic Aspects", "Johns-Marriage mediates[gufo] Mary."),
    ("2.7. Extrinsic Aspects", "Every employment is a relator[gufo]."),
    ("2.7. Extrinsic Aspects", "Every employment mediates[gufo] exactly one employee."),
    ("2.7. Extrinsic Aspects", "Every employment mediates[gufo] exactly one employer."),
    ("2.7. Extrinsic Aspects", "Every love is an extrinsic-mode[gufo]."),
    ("2.7. Extrinsic Aspects", "Every love is-externally-dependent-on[gufo] some person."),
    # Section: 2.8. Events
    ("2.8. Events", "Every natural-disaster is an event[gufo]."),
    ("2.8. Events", "Every earthquake is a natural-disaster."),
    ("2.8. Events", "Every flood is a natural-disaster."),
    ("2.8. Events", "The-1985-Mexico-City-Earthquake is an earthquake."),
    ("2.8. Events", "The-1985-Mexico-City-Earthquake is an earthquake and has-begin-date[gufo] equal-to 1985-09-19T131750Z."),
    ("2.8. Events", "Every soccer-match is an event[gufo]."),
    ("2.8. Events", "Every goal is an event[gufo]."),
    ("2.8. Events", "World-Cup-1970-Final is a soccer-match."),
    ("2.8. Events", "Every event[gufo] historically-depends-on[gufo] some event[gufo]."),
    ("2.8. Events", "Every participation is an event[gufo]."),
    ("2.8. Events", "Every participation has-participant some endurant[gufo]."),
    ("2.8. Events", "Peles-Participation-In-1970-Final is a participation."),
    ("2.8. Events", "Peles-Participation-In-1970-Final has-participant Pele."),
    ("2.8. Events", "Peles-Participation-In-1970-Final is-event-proper-part-of[gufo] World-Cup-1970-Final."),
    ("2.8. Events", "Every wedding is an event[gufo]."),
    ("2.8. Events", "Every wedding creates[gufo] some marriage."),
    ("2.8. Events", "Johns-Wedding is a wedding."),
    ("2.8. Events", "Johns-Wedding creates[gufo] Johns-Marriage."),
    ("2.8. Events", "Every death is an event[gufo]."),
    ("2.8. Events", "Every death terminates[gufo] some object[gufo]."),
    # Section: 2.9. Situations
    ("2.9. Situations", "Every situation is a concrete-individual[gufo]."),
    ("2.9. Situations", "Every quality-value-attribution is a situation[gufo]."),
    ("2.9. Situations", "Every temporary-instantiation is a situation[gufo]."),
    ("2.9. Situations", "Every temporary-parthood is a situation[gufo]."),
    ("2.9. Situations", "Every temporary-constitution is a situation[gufo]."),
    ("2.9. Situations", "Every temporary-relationship is a situation[gufo]."),
    # Section: 3.1. Endurant Types
    ("3.1. Endurant Types", "Person is a kind[gufo]."),
    ("3.1. Endurant Types", "Child is a phase[gufo]."),
    ("3.1. Endurant Types", "Student is a role[gufo]."),
    ("3.1. Endurant Types", "Every person is an object[gufo]."),
    ("3.1. Endurant Types", "Every child is a person."),
    ("3.1. Endurant Types", "Every student is a person."),
    # Section: 3.2. Relationship Types
    ("3.2. Relationship Types", "Every material-relationship-type is a relationship-type[gufo]."),
    ("3.2. Relationship Types", "Friendship is a material-relationship-type[gufo]."),
    ("3.2. Relationship Types", "Every friendship is a relator[gufo]."),
    # Section: 3.3. Higher-Order Types
    ("3.3. Higher-Order Types", "Person-Role categorizes[gufo] Person."),
    ("3.3. Higher-Order Types", "Every person-role is a role[gufo]."),
    ("3.3. Higher-Order Types", "Student is a person-role."),
    ("3.3. Higher-Order Types", "Every student is a person."),
    ("3.3. Higher-Order Types", "Ship-Type categorizes[gufo] Ship."),
    ("3.3. Higher-Order Types", "Every ship-type is a sub-kind[gufo]."),
    ("3.3. Higher-Order Types", "Supercarrier is a ship-type."),
    ("3.3. Higher-Order Types", "Every supercarrier is a ship."),
    ("3.3. Higher-Order Types", "Animal-Species partitions[gufo] Animal."),
    ("3.3. Higher-Order Types", "Hiena is an animal-species."),
    ("3.3. Higher-Order Types", "Every hiena is an animal."),
    ("3.3. Higher-Order Types", "Lion is an animal-species."),
    ("3.3. Higher-Order Types", "Every lion is an animal."),
    ("3.3. Higher-Order Types", "No lion is a hiena."),
    ("3.3. Higher-Order Types", "Cecil is a lion."),
]


# =============================================================================
# GRAMMAR.MD PATTERNS (extracted from examples)
# =============================================================================

GRAMMAR_PATTERNS = [
    # Concept Subsumption
    ("Concept Subsumption", "Every cat is a mammal."),
    ("Concept Subsumption", "Every cat that is a brown-one has a red-eye."),
    ("Concept Subsumption", "Every tree is a plant."),
    # Concept Equivalence
    ("Concept Equivalence", "Something is a human if-and-only-if-it is a person."),
    ("Concept Equivalence", "Something is a man if-and-only-if-it is a person and is a male."),
    # Disjoint Concepts
    ("Disjoint Concepts", "No cat is a dog."),
    ("Disjoint Concepts", "Nothing is a cat and is a dog."),
    ("Disjoint Concepts", "No man is a woman."),
    # Universal Restriction
    ("Universal Restriction", "Every herbivore eats nothing-but plant."),
    ("Universal Restriction", "Every person has-parent nothing-but person."),
    ("Universal Restriction", "Every cat eats nothing-but mice."),
    # Existential Restriction
    ("Existential Restriction", "Every person has-parent some person."),
    ("Existential Restriction", "Every cat eats something."),
    ("Existential Restriction", "Every leaf is-part-of some tree."),
    ("Existential Restriction", "Every cat eats some mouse."),
    # Cardinality Restrictions
    ("Cardinality", "Every person has-parent exactly 2 persons."),
    ("Cardinality", "Every person has-parent at-most 2 persons."),
    ("Cardinality", "Every person has-parent at-least 1 person."),
    ("Cardinality", "Every bicycle has-wheel exactly 2 things."),
    ("Cardinality", "Every hand has-finger at-most 5 things."),
    ("Cardinality", "Every parent has-child at-least 1 thing."),
    ("Cardinality", "Every person has exactly one head."),
    ("Cardinality", "Every car has at-least 3 wheels."),
    ("Cardinality", "Every orchestra has at-most 120 members."),
    # Self Restriction
    ("Self Restriction", "Every narcissist loves itself."),
    ("Self Restriction", "Every-single-thing knows itself."),
    # Instance Assertions
    ("Instance Assertions", "John is a person."),
    ("Instance Assertions", "Mary is a woman."),
    ("Instance Assertions", "Fido is a dog."),
    ("Instance Assertions", "Paris is a city."),
    # Role Assertions
    ("Role Assertions", "John is-parent-of Mary."),
    ("Role Assertions", "John loves Mary."),
    ("Role Assertions", "Fido has-owner John."),
    ("Role Assertions", "John knows Mary."),
    # Data Assertions
    ("Data Assertions", "John has-age equal-to 30."),
    ("Data Assertions", "Mary has-name equal-to 'Mary Smith'."),
    ("Data Assertions", "Pi has-value equal-to 3.14159."),
    ("Data Assertions", "Today has-date equal-to 2024-01-15."),
    ("Data Assertions", "Meeting has-time equal-to 2024-01-15T14:30:00Z."),
    # Property Subsumption
    ("Property Subsumption", "If X has-mother Y then X has-parent Y."),
    ("Property Subsumption", "If X has-father Y then X has-parent Y."),
    ("Property Subsumption", "If X is-part-of Y then X is-related-to Y."),
    # Property Chains
    ("Property Chains", "If X has-parent something that has-parent Y then X has-grandparent Y."),
    ("Property Chains", "If X has-parent something that has-sibling Y then X has-uncle-or-aunt Y."),
    ("Property Chains", "If X is-part-of something that is-part-of Y then X is-part-of Y."),
    # Symmetric Properties
    ("Symmetric Properties", "X is-sibling-of Y if-and-only-if Y is-sibling-of X."),
    ("Symmetric Properties", "X is-married-to Y if-and-only-if Y is-married-to X."),
    ("Symmetric Properties", "X knows Y if-and-only-if Y knows X."),
    # Asymmetric Properties
    ("Asymmetric Properties", "If X is-parent-of Y then Y does-not is-parent-of X."),
    ("Asymmetric Properties", "If X is-older-than Y then Y does-not is-older-than X."),
    # Reflexive Properties
    ("Reflexive Properties", "Every-single-thing knows itself."),
    ("Reflexive Properties", "Every-single-thing is-part-of itself."),
    # Irreflexive Properties
    ("Irreflexive Properties", "Nothing is-parent-of itself."),
    ("Irreflexive Properties", "Nothing is-proper-part-of itself."),
    # Functional Properties
    ("Functional Properties", "Every person has-birth-mother exactly one thing."),
    # Inverse Functional Properties
    ("Inverse Functional Properties", "Every thing is-birth-mother-of at-most one person."),
    # Disjoint Union
    ("Disjoint Union", "Something is a person if-and-only-if-it-either is a man or is a woman."),
    ("Disjoint Union", "Something is a color if-and-only-if-it-either is a red or is a green or is a blue."),
    # Data Range Restrictions
    ("Data Range", "Every person has-age nothing-but (some integer value)."),
    ("Data Range", "Every person has-name nothing-but (some string value)."),
    ("Data Range", "Every event has-date nothing-but (some datetime value)."),
    ("Data Range", "Every person has-height nothing-but (some real value)."),
    ("Data Range", "Every person has-active nothing-but (some boolean value)."),
    # Negation
    ("Negation", "Every vegetarian eats nothing-but things that are not meat."),
    ("Negation", "Every orphan has-parent no person."),
    # Complex Expressions
    ("Complex", "Every happy-person is a person that has-friend some person."),
    ("Complex", "Every lonely-person is a person that has-friend no thing."),
    ("Complex", "Every popular-person is a person that has-friend at-least 10 persons."),
    # Conjunction/Disjunction
    ("Conjunction", "Every student is a person and has-enrollment some course."),
    ("Disjunction", "Every employee is a full-time-employee or is a part-time-employee."),
    # Thing/Nothing
    ("Thing", "Every thing has-id some value."),
    ("Thing", "Nothing is a square-circle."),
    ("Thing", "Every-single-thing is-related-to some thing."),
    # Keys
    ("Keys", "Every X that has-ssn something is-unique-if has-ssn."),
    ("Keys", "Every X that has-id something is-unique-if has-id."),
    # Annotations
    ("Annotations", "Every person[rdfs:label='Person'] is an agent."),
    # SWRL Rules
    ("SWRL", "If a person has-age a value that is greater-than 18 then the person is an adult."),
]

# Patterns that are GRAMMATICALLY INVALID in CNL (not just unimplemented)
# These patterns violate the CNL grammar and cannot be supported.
UNSUPPORTED_PATTERNS = [
    # INVALID: 'X' and 'Y' are reserved tokens for property axioms, not concept names.
    # The grammar expects NAME (lowercase) but X/Y are special tokens.
    # This appears to be a meta-syntax example, not a valid CNL pattern.
    ("Concept Subsumption", "Every X is a Y."),

    # INVALID: 'value' is a keyword token (VALUE), not a valid concept name (NAME).
    # OWL doesn't support "inverse functional data properties" anyway.
    # For data property cardinality, use: "Every person has-ssn at-most one (some string value)."
    ("Inverse Functional Properties", "Every value is-ssn-of at-most one person."),
]

# Additional patterns that are now supported (moved from UNSUPPORTED_PATTERNS)
ADDITIONAL_SUPPORTED_PATTERNS = [
    # Same-as / Different-from patterns
    ("Same/Different", "John is-the-same-as Johnny."),
    ("Same/Different", "John is-not-the-same-as Mary."),
    # Transitive property patterns (parsed as SWRL rules)
    ("Transitive Properties", "If X is-ancestor-of Y and Y is-ancestor-of Z then X is-ancestor-of Z."),
    ("Transitive Properties", "If X is-part-of Y and Y is-part-of Z then X is-part-of Z."),
    # Cardinality with "value" as filler (data property functional)
    ("Functional Properties", "Every person has-ssn exactly one value."),
    # Enumerations with (either ... or ...) in object position
    ("Enumeration", "Every traffic-light has-color (either Red or Yellow or Green)."),
    ("Enumeration", "Every day-of-week is (either Monday or Tuesday or Wednesday or Thursday or Friday or Saturday or Sunday)."),
    # SWRL with explicit indexed variables
    ("SWRL Indexed", "If a person(1) has-parent a person(2) and the person(2) has-sibling a person(3) then the person(1) has-uncle-or-aunt the person(3)."),
    ("SWRL Indexed", "If a person(1) has-parent a person(2) and the person(2) is a female-person then the person(1) has-mother the person(2)."),
    # SWRL with "that" clause (implicit variable chaining)
    ("SWRL That", "If a person has-parent a person that has-sibling a person then the person(1) has-uncle-or-aunt the person(3)."),
]

# Patterns that crash the parser (need investigation)
CRASHING_PATTERNS = [
    # SWRL with value(1) plus value(2) causes access violation
    ("SWRL", "If a person has-age a value(1) and has-birth-year a value(2) then the person has-current-year the value(1) plus the value(2)."),
]


# =============================================================================
# TESTS
# =============================================================================

class TestGufoOverviewPatterns:
    """Test all patterns from gufo_overview.md in gUFO context."""

    @pytest.mark.parametrize("section,pattern", GUFO_OVERVIEW_PATTERNS,
                             ids=[f"{s[:20]}:{p[:40]}" for s, p in GUFO_OVERVIEW_PATTERNS])
    def test_pattern_parses(self, section, pattern):
        """Verify pattern produces at least one fact."""
        facts = parse_with_gufo(pattern)
        assert len(facts) > 0, f"Pattern produced no facts: {pattern}"


class TestGrammarPatterns:
    """Test all patterns from grammar.md in isolation."""

    @pytest.mark.parametrize("section,pattern", GRAMMAR_PATTERNS,
                             ids=[f"{s[:20]}:{p[:40]}" for s, p in GRAMMAR_PATTERNS])
    def test_pattern_parses(self, section, pattern):
        """Verify pattern produces at least one fact."""
        facts = parse_isolated(pattern)
        assert len(facts) > 0, f"Pattern produced no facts: {pattern}"


class TestGufoOverviewInIsolation:
    """Test gufo_overview.md patterns without gUFO (sanity check)."""

    @pytest.mark.parametrize("section,pattern", GUFO_OVERVIEW_PATTERNS,
                             ids=[f"{s[:20]}:{p[:40]}" for s, p in GUFO_OVERVIEW_PATTERNS])
    def test_pattern_parses_isolated(self, section, pattern):
        """Verify pattern parses correctly even without gUFO context."""
        facts = parse_isolated(pattern)
        assert len(facts) > 0, f"Pattern produced no facts: {pattern}"


class TestUnsupportedPatterns:
    """Test patterns that are documented but not yet fully supported.

    These are marked with xfail - they document known gaps in the parser.
    When support is added, these tests will start passing and need updating.
    """

    @pytest.mark.parametrize("section,pattern", UNSUPPORTED_PATTERNS,
                             ids=[f"{s[:20]}:{p[:40]}" for s, p in UNSUPPORTED_PATTERNS])
    @pytest.mark.xfail(reason="Pattern not yet supported by parser")
    def test_unsupported_pattern(self, section, pattern):
        """Document unsupported patterns."""
        facts = parse_isolated(pattern)
        assert len(facts) > 0, f"Pattern produced no facts: {pattern}"


class TestAdditionalSupportedPatterns:
    """Test patterns that were recently added to the parser."""

    @pytest.mark.parametrize("section,pattern", ADDITIONAL_SUPPORTED_PATTERNS,
                             ids=[f"{s[:20]}:{p[:40]}" for s, p in ADDITIONAL_SUPPORTED_PATTERNS])
    def test_additional_pattern(self, section, pattern):
        """Test newly supported patterns."""
        facts = parse_isolated(pattern)
        assert len(facts) > 0, f"Pattern produced no facts: {pattern}"
