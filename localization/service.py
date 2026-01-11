import json
from pathlib import Path
from typing import Any

from utils.logger import get_logger

logger = get_logger(__name__)


class LocalizationService:
    """Service for managing multi-language support.

    Loads translations from JSON files and provides methods to get localized strings.
    """

    def __init__(self, translations_dir: str = "localization/translations") -> None:
        """Initialize localization service.

        Args:
            translations_dir: Directory containing translation JSON files
        """
        self.translations_dir = Path(translations_dir)
        self.translations: dict[str, dict[str, Any]] = {}
        self.supported_languages = ["en", "ru", "et"]
        self.default_language = "en"
        self._load_translations()

    def _load_translations(self) -> None:
        """Load all translation files from the translations directory."""
        for lang_code in self.supported_languages:
            file_path = self.translations_dir / f"{lang_code}.json"
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.translations[lang_code] = json.load(f)
                logger.info(
                    "translation_loaded", language=lang_code, file=str(file_path)
                )
            except FileNotFoundError:
                logger.error(
                    "translation_file_not_found",
                    language=lang_code,
                    file=str(file_path),
                )
                self.translations[lang_code] = {}
            except json.JSONDecodeError as e:
                logger.error(
                    "translation_json_error",
                    language=lang_code,
                    file=str(file_path),
                    error=str(e),
                )
                self.translations[lang_code] = {}

    def get(self, key: str, language: str, **kwargs: Any) -> str:
        """Get localized string by key.

        Args:
            key: Translation key (dot-notation supported, e.g., 'commands.start.welcome')
            language: Language code (en, ru, et)
            **kwargs: Variables to format into the translation string

        Returns:
            Localized string, or the key itself if translation not found

        Example:
            >>> loc = LocalizationService()
            >>> loc.get('commands.start.welcome', 'en', username='John')
            'Welcome, John!'
        """
        # Fallback to default language if requested language not supported
        if language not in self.supported_languages:
            logger.warning(
                "unsupported_language",
                requested=language,
                fallback=self.default_language,
            )
            language = self.default_language

        # Navigate through nested keys
        keys = key.split(".")
        value = self.translations.get(language, {})

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                value = None
                break

        # If translation not found, try default language
        if value is None:
            logger.warning(
                "translation_key_not_found",
                key=key,
                language=language,
                fallback_to=self.default_language,
            )
            value = self.translations.get(self.default_language, {})
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                else:
                    value = None
                    break

        # If still not found, return the key itself
        if value is None:
            logger.error("translation_missing", key=key, language=language)
            return key

        # Format string with provided kwargs
        if isinstance(value, str) and kwargs:
            try:
                return value.format(**kwargs)
            except KeyError as e:
                logger.error(
                    "translation_format_error",
                    key=key,
                    language=language,
                    missing_var=str(e),
                )
                return value
        return str(value)

    def get_language_name(self, language_code: str) -> str:
        """Get human-readable language name.

        Args:
            language_code: Language code (en, ru, et)

        Returns:
            Language name in its own language
        """
        names = {"en": "English", "ru": "Русский", "et": "Eesti"}
        return names.get(language_code, language_code)

    def is_supported(self, language_code: str) -> bool:
        """Check if language is supported.

        Args:
            language_code: Language code to check

        Returns:
            True if language is supported
        """
        return language_code in self.supported_languages


# Global localization service instance
localization = LocalizationService()
