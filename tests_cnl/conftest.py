"""
CNL Parser Test Configuration
"""
import pytest
import reter_core.owl_rete_cpp as cpp


@pytest.fixture
def parse_cnl():
    """Fixture to parse CNL and return facts."""
    def _parse(cnl_text):
        result = cpp.parse_cnl(cnl_text)
        return result
    return _parse


@pytest.fixture
def get_facts():
    """Fixture to parse CNL and return list of fact dicts."""
    def _get_facts(cnl_text):
        result = cpp.parse_cnl(cnl_text)
        facts = []
        for f in result.facts:
            fact_dict = {'type': f.get('type')}
            # Add all known keys
            for key in ['sub', 'sup', 'individual', 'concept', 'subject',
                        'role', 'object', 'c1', 'c2', 'property',
                        'filler', 'cardinality', 'id', 'class', 'i1', 'i2',
                        'modality', 'chain', 'super_property', 'value', 'datatype']:
                val = f.get(key)
                if val:
                    fact_dict[key] = val
            # Handle list fields
            for key in ['classes', 'members']:
                try:
                    val = f.get_string_list(key)
                    if val:
                        fact_dict[key] = val
                except:
                    pass
            facts.append(fact_dict)
        return facts
    return _get_facts


def find_fact(facts, **criteria):
    """Find a fact matching all criteria."""
    for f in facts:
        if all(f.get(k) == v for k, v in criteria.items()):
            return f
    return None


def has_fact(facts, **criteria):
    """Check if a fact matching criteria exists."""
    return find_fact(facts, **criteria) is not None
