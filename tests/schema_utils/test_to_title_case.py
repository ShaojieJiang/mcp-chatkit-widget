"""Unit tests for `_to_title_case` helper."""

from mcp_chatkit_widget.schema_utils import _to_title_case


class TestToTitleCase:
    """Tests for _to_title_case function."""

    def test_snake_case_conversion(self) -> None:
        """Test conversion of snake_case strings."""
        assert _to_title_case("flight_tracker") == "FlightTracker"
        assert _to_title_case("create_event") == "CreateEvent"
        assert _to_title_case("multi_word_name") == "MultiWordName"

    def test_single_word_conversion(self) -> None:
        """Test conversion of single word strings (line 28)."""
        assert _to_title_case("date") == "Date"
        assert _to_title_case("name") == "Name"
        assert _to_title_case("widget") == "Widget"
