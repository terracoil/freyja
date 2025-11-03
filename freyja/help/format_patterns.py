import textwrap


class FormatPatterns:
    """Common formatting patterns extracted to eliminate duplication."""

    @staticmethod
    def format_section_title(title: str, style_func=None) -> str:
        """Format section title consistently."""
        return style_func(title) if style_func else title

    @staticmethod
    def format_indented_line(content: str, indent: int) -> str:
        """Format line with consistent indentation."""
        return f"{' ' * indent}{content}"

    @staticmethod
    def calculate_spacing(name_width: int, target_column: int, min_spacing: int = 4) -> int:
        """Calculate spacing needed to reach target column."""
        return min_spacing if name_width >= target_column else target_column - name_width

    @staticmethod
    def create_text_wrapper(
        width: int, initial_indent: str = "", subsequent_indent: str = ""
    ) -> textwrap.TextWrapper:
        """Create TextWrapper with consistent parameters."""
        return textwrap.TextWrapper(
            width=width,
            break_long_words=False,
            break_on_hyphens=False,
            initial_indent=initial_indent,
            subsequent_indent=subsequent_indent,
        )
