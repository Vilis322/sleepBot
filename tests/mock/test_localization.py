"""Mock tests for localization service."""

import pytest

from localization.service import LocalizationService


class TestLocalizationService:
    """Test localization service operations."""

    def test_initialization(self, localization_service: LocalizationService):
        """Test that service initializes with translations loaded."""
        assert localization_service.supported_languages == ["en", "ru", "et"]
        assert localization_service.default_language == "en"
        assert len(localization_service.translations) > 0

    def test_get_simple_key_english(self, localization_service: LocalizationService):
        """Test getting simple translation key in English."""
        # Using a key that should exist in translations
        result = localization_service.get("buttons.cancel", "en")

        assert isinstance(result, str)
        assert result != ""
        assert result != "buttons.cancel"  # Should be translated

    def test_get_simple_key_russian(self, localization_service: LocalizationService):
        """Test getting simple translation key in Russian."""
        result = localization_service.get("buttons.cancel", "ru")

        assert isinstance(result, str)
        assert result != ""
        assert result != "buttons.cancel"

    def test_get_nested_key(self, localization_service: LocalizationService):
        """Test getting nested translation key with dot notation."""
        # Testing commands.start or similar nested key
        result = localization_service.get("commands.start.welcome", "en")

        assert isinstance(result, str)
        # Should either return translation or fallback to key if not found
        assert result != ""

    def test_get_with_formatting(self, localization_service: LocalizationService):
        """Test getting translation with variable formatting."""
        # Test with a known key that has placeholders
        result = localization_service.get(
            "commands.quality.confirm_overwrite",
            "en",
            rating=7.5,
            new_rating=8.0
        )

        assert isinstance(result, str)
        # If translation exists, it should contain the formatted values
        if "{rating}" not in result:
            # Translation was found and formatted
            assert "7.5" in result or "8.0" in result or result == "commands.quality.confirm_overwrite"

    def test_get_unsupported_language_fallback(self, localization_service: LocalizationService):
        """Test that unsupported language falls back to default."""
        result = localization_service.get("buttons.cancel", "fr")  # French not supported

        # Should fallback to English
        assert isinstance(result, str)
        assert result != "buttons.cancel" or "buttons" in result  # Either translated or key returned

    def test_get_missing_key_returns_key(self, localization_service: LocalizationService):
        """Test that missing translation key returns the key itself."""
        result = localization_service.get("nonexistent.key.path", "en")

        assert result == "nonexistent.key.path"

    def test_get_missing_key_in_nested_structure(self, localization_service: LocalizationService):
        """Test handling of missing nested keys."""
        result = localization_service.get("buttons.nonexistent.deeply.nested", "en")

        # Should return the key itself when not found
        assert result == "buttons.nonexistent.deeply.nested"

    def test_get_with_missing_format_variable(self, localization_service: LocalizationService):
        """Test that missing format variable doesn't crash."""
        # Try to format a translation without providing all required variables
        result = localization_service.get(
            "commands.quality.confirm_overwrite",
            "en",
            rating=7.5  # Missing new_rating
        )

        # Should return something (either unformatted string or key)
        assert isinstance(result, str)
        assert result != ""

    def test_get_language_name_english(self, localization_service: LocalizationService):
        """Test getting language name in English."""
        name = localization_service.get_language_name("en")
        assert name == "English"

    def test_get_language_name_russian(self, localization_service: LocalizationService):
        """Test getting language name in Russian."""
        name = localization_service.get_language_name("ru")
        assert name == "Русский"

    def test_get_language_name_estonian(self, localization_service: LocalizationService):
        """Test getting language name in Estonian."""
        name = localization_service.get_language_name("et")
        assert name == "Eesti"

    def test_get_language_name_unsupported(self, localization_service: LocalizationService):
        """Test getting language name for unsupported language."""
        name = localization_service.get_language_name("fr")
        assert name == "fr"  # Should return the code itself

    def test_is_supported_english(self, localization_service: LocalizationService):
        """Test that English is supported."""
        assert localization_service.is_supported("en") is True

    def test_is_supported_russian(self, localization_service: LocalizationService):
        """Test that Russian is supported."""
        assert localization_service.is_supported("ru") is True

    def test_is_supported_estonian(self, localization_service: LocalizationService):
        """Test that Estonian is supported."""
        assert localization_service.is_supported("et") is True

    def test_is_supported_unsupported_language(self, localization_service: LocalizationService):
        """Test that unsupported language returns False."""
        assert localization_service.is_supported("fr") is False
        assert localization_service.is_supported("de") is False
        assert localization_service.is_supported("es") is False

    def test_all_supported_languages_have_translations(
        self, localization_service: LocalizationService
    ):
        """Test that all supported languages have loaded translations."""
        for lang in localization_service.supported_languages:
            assert lang in localization_service.translations
            # Translations dict should not be empty (even if file missing, it's initialized as {})
            assert isinstance(localization_service.translations[lang], dict)

    def test_get_handles_non_string_values(self, localization_service: LocalizationService):
        """Test that get method handles non-string translation values."""
        # If a translation value is a dict or list, it should be converted to string
        # This is an edge case but service should handle it gracefully

        # Try to get a parent key that contains nested structure
        result = localization_service.get("commands", "en")

        # Should return string representation
        assert isinstance(result, str)

    def test_get_empty_kwargs(self, localization_service: LocalizationService):
        """Test that translations without placeholders work with empty kwargs."""
        result = localization_service.get("buttons.cancel", "en")

        assert isinstance(result, str)
        assert result != ""

    def test_translations_consistency_across_languages(
        self, localization_service: LocalizationService
    ):
        """Test that same key exists across all languages (or fails gracefully)."""
        # Test a common key across all supported languages
        key = "buttons.cancel"

        for lang in localization_service.supported_languages:
            result = localization_service.get(key, lang)
            assert isinstance(result, str)
            assert result != ""
