from freyja.utils import TextUtil


class TestStringUtils:
  """Test cases for TextUtil class."""

  def test_kebab_case_pascal_case(self):
    """Test conversion of PascalCase strings."""
    assert TextUtil.kebab_case("FooBarBaz") == "foo-bar-baz"
    assert TextUtil.kebab_case("XMLHttpRequest") == "xml-http-request"
    assert TextUtil.kebab_case("HTMLParser") == "html-parser"

  def test_kebab_case_camel_case(self):
    """Test conversion of camelCase strings."""
    assert TextUtil.kebab_case("fooBarBaz") == "foo-bar-baz"
    assert TextUtil.kebab_case("getUserName") == "get-user-name"
    assert TextUtil.kebab_case("processDataFiles") == "process-data-files"

  def test_kebab_case_single_word(self):
    """Test single word inputs."""
    assert TextUtil.kebab_case("simple") == "simple"
    assert TextUtil.kebab_case("SIMPLE") == "simple"
    assert TextUtil.kebab_case("Simple") == "simple"

  def test_kebab_case_with_numbers(self):
    """Test strings containing numbers."""
    assert TextUtil.kebab_case("foo2Bar") == "foo2-bar"
    assert TextUtil.kebab_case("getV2APIResponse") == "get-v2-api-response"
    assert TextUtil.kebab_case("parseHTML5Document") == "parse-html5-document"

  def test_kebab_case_already_kebab_case(self):
    """Test strings that are already in kebab-case."""
    assert TextUtil.kebab_case("foo-bar-baz") == "foo-bar-baz"
    assert TextUtil.kebab_case("simple-case") == "simple-case"

  def test_kebab_case_edge_cases(self):
    """Test edge cases."""
    assert TextUtil.kebab_case("") == ""
    assert TextUtil.kebab_case("A") == "a"
    assert TextUtil.kebab_case("AB") == "ab"
    assert TextUtil.kebab_case("ABC") == "abc"

  def test_kebab_case_consecutive_capitals(self):
    """Test strings with consecutive capital letters."""
    assert TextUtil.kebab_case("JSONParser") == "json-parser"
    assert TextUtil.kebab_case("XMLHTTPRequest") == "xmlhttp-request"
    assert TextUtil.kebab_case("PDFDocument") == "pdf-document"

  def test_kebab_case_mixed_separators(self):
    """Test strings with existing separators."""
    assert TextUtil.kebab_case("foo_bar_baz") == "foo-bar-baz"
    assert TextUtil.kebab_case("FooBar_Baz") == "foo-bar-baz"
