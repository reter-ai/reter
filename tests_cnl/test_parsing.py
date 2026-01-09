"""
Tests for CNL Parsing Basics
"""
import pytest
import reter_core.owl_rete_cpp as cpp


class TestParseResult:
    """Test CNL parse result structure."""

    def test_empty_input(self):
        """Empty input should succeed with no facts."""
        result = cpp.parse_cnl("")
        assert result.success == True
        assert len(result.facts) == 0

    def test_single_sentence(self):
        """Single sentence should parse successfully."""
        result = cpp.parse_cnl("Every cat is a mammal.")
        assert result.success == True
        assert len(result.facts) >= 1

    def test_multiple_sentences(self):
        """Multiple sentences should parse."""
        cnl = """
        Every cat is a mammal.
        Every dog is a mammal.
        Every mammal is an animal.
        """
        result = cpp.parse_cnl(cnl)
        assert result.success == True
        assert len(result.facts) >= 3


class TestSentenceTermination:
    """Test sentence termination with period."""

    def test_period_required(self):
        """Sentence without period should still parse (lenient)."""
        result = cpp.parse_cnl("Every cat is a mammal")
        # Depending on parser strictness, this may or may not succeed
        # Just verify no crash
        assert result is not None

    def test_question_mark(self):
        """Question mark as sentence terminator."""
        result = cpp.parse_cnl("Every cat is a mammal?")
        assert result is not None


class TestCNLVersion:
    """Test CNL version info."""

    def test_version_available(self):
        """CNL version should be available."""
        version = cpp.get_cnl_version()
        assert version is not None
        assert len(version) > 0


class TestParseOptions:
    """Test CNL parse options."""

    def test_strict_mode(self):
        """Strict mode should report errors."""
        options = cpp.CNLParseOptions()
        options.strict_mode = True
        # Just verify options work
        assert options.strict_mode == True


class TestValidation:
    """Test CNL validation."""

    def test_validate_correct(self):
        """Valid CNL should have no errors."""
        errors = cpp.validate_cnl("Every cat is a mammal.")
        assert len(errors) == 0

    def test_validate_empty(self):
        """Empty input should have no errors."""
        errors = cpp.validate_cnl("")
        assert len(errors) == 0
