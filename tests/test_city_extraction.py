from __future__ import annotations

from core.extractor import TextExtractor
from core.schemas import RawInput


class TestCityExtraction:
    def test_primary_city_strips_trailing_tokens(self) -> None:
        text = (
            "Primary City / Hauptstandort *\n"
            "Wir bieten in Düsseldorf eine spannende Aufgabe in einem innovativen Umfeld.\n"
            "Weitere Details folgen."
        )
        extractor = TextExtractor()

        result = extractor.extract(RawInput(text=text))

        assert result.location == "Düsseldorf"

    def test_multi_word_city_remains_intact(self) -> None:
        text = (
            "Standort: Frankfurt am Main\n"
            "Wir sind ein wachsendes Team und suchen Unterstützung."
        )
        extractor = TextExtractor()

        result = extractor.extract(RawInput(text=text))

        assert result.location == "Frankfurt am Main"

    def test_hyphenated_city_remains_intact(self) -> None:
        text = (
            "Location: Villingen-Schwenningen\n"
            "Bewirb dich jetzt und werde Teil unseres Teams."
        )
        extractor = TextExtractor()

        result = extractor.extract(RawInput(text=text))

        assert result.location == "Villingen-Schwenningen"
