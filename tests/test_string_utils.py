from auto_cli.string_utils import StringUtils


class TestStringUtils:
  """Test cases for StringUtils class."""

  def test_kebab_case_pascal_case(self):
    """Test conversion of PascalCase strings."""
    assert StringUtils.kebab_case("FooBarBaz") == "foo-bar-baz"
    assert StringUtils.kebab_case("XMLHttpRequest") == "xml-http-request"
    assert StringUtils.kebab_case("HTMLParser") == "html-parser"

  def test_kebab_case_camel_case(self):
    """Test conversion of camelCase strings."""
    assert StringUtils.kebab_case("fooBarBaz") == "foo-bar-baz"
    assert StringUtils.kebab_case("getUserName") == "get-user-name"
    assert StringUtils.kebab_case("processDataFiles") == "process-data-files"

  def test_kebab_case_single_word(self):
    """Test single word inputs."""
    assert StringUtils.kebab_case("simple") == "simple"
    assert StringUtils.kebab_case("SIMPLE") == "simple"
    assert StringUtils.kebab_case("Simple") == "simple"

  def test_kebab_case_with_numbers(self):
    """Test strings containing numbers."""
    assert StringUtils.kebab_case("foo2Bar") == "foo2-bar"
    assert StringUtils.kebab_case("getV2APIResponse") == "get-v2-api-response"
    assert StringUtils.kebab_case("parseHTML5Document") == "parse-html5-document"

  def test_kebab_case_already_kebab_case(self):
    """Test strings that are already in kebab-case."""
    assert StringUtils.kebab_case("foo-bar-baz") == "foo-bar-baz"
    assert StringUtils.kebab_case("simple-case") == "simple-case"

  def test_kebab_case_edge_cases(self):
    """Test edge cases."""
    assert StringUtils.kebab_case("") == ""
    assert StringUtils.kebab_case("A") == "a"
    assert StringUtils.kebab_case("AB") == "ab"
    assert StringUtils.kebab_case("ABC") == "abc"

  def test_kebab_case_consecutive_capitals(self):
    """Test strings with consecutive capital letters."""
    assert StringUtils.kebab_case("JSONParser") == "json-parser"
    assert StringUtils.kebab_case("XMLHTTPRequest") == "xmlhttp-request"
    assert StringUtils.kebab_case("PDFDocument") == "pdf-document"

  def test_kebab_case_mixed_separators(self):
    """Test strings with existing separators."""
    assert StringUtils.kebab_case("foo_bar_baz") == "foo-bar-baz"
    assert StringUtils.kebab_case("FooBar_Baz") == "foo-bar-baz"
