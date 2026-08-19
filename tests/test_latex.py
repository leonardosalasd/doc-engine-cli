import pytest

from doc_engine.converter import convert
from doc_engine.latex import to_typst

typst = pytest.importorskip("typst")


def compiles(expression: str, tmp_path) -> bool:
    """Compile a Typst math expression, so the tests check real output."""
    source = tmp_path / "probe.typ"
    source.write_text(f"$ {expression} $", encoding="utf-8")
    try:
        typst.compile(str(source), output=str(tmp_path / "probe.pdf"))
    except Exception:
        return False
    return True


class TestStructure:
    def test_fraction(self) -> None:
        assert to_typst(r"\frac{a}{b}") == "frac(a, b)"

    def test_nested_fraction(self) -> None:
        assert to_typst(r"\frac{x^2}{\sqrt{y}}") == "frac(x^2, sqrt(y))"

    def test_root_with_degree(self) -> None:
        assert to_typst(r"\sqrt[3]{x}") == "root(3, x)"

    def test_binomial(self) -> None:
        assert to_typst(r"\binom{n}{k}") == "binom(n, k)"

    def test_braces_become_grouping_parentheses(self) -> None:
        assert to_typst(r"x^{2n}") == "x^(2 n)"

    def test_left_and_right_are_dropped(self) -> None:
        assert "left" not in to_typst(r"\left( x \right)")


class TestSymbols:
    def test_greek(self) -> None:
        assert to_typst(r"\alpha \beta \gamma") == "alpha beta gamma"

    def test_variant_greek_maps_to_alternate(self) -> None:
        assert to_typst(r"\varepsilon") == "epsilon.alt"

    def test_relations(self) -> None:
        assert to_typst(r"a \leq b \neq c") == "a <= b != c"

    def test_set_operations(self) -> None:
        assert to_typst(r"A \cup B \cap C") == "A union B inter C"

    def test_mid_becomes_a_bar(self) -> None:
        assert to_typst(r"P(A \mid B)") == "P(A | B)"

    def test_unknown_command_keeps_its_name(self) -> None:
        assert to_typst(r"\zeta") == "zeta"


class TestLetterRuns:
    def test_runs_are_split_into_separate_variables(self) -> None:
        assert to_typst("xy") == "x y"

    def test_operators_stay_whole(self) -> None:
        assert to_typst(r"\sin x") == "sin x"
        assert to_typst("lim") == "lim"

    def test_symbol_does_not_merge_with_neighbour(self) -> None:
        assert to_typst(r"i\pi") == "i pi"


class TestEnvironments:
    def test_matrix_columns_and_rows(self) -> None:
        assert to_typst(r"\begin{pmatrix} a & b \\ c & d \end{pmatrix}") == "mat(a , b ; c , d)"

    def test_bracket_matrix_sets_delimiter(self) -> None:
        assert 'delim: "["' in to_typst(r"\begin{bmatrix} a \\ b \end{bmatrix}")

    def test_cases_rows_are_arguments(self) -> None:
        result = to_typst(r"\begin{cases} x & \text{if } y \\ z & \text{else} \end{cases}")
        assert result.startswith("cases(")
        assert '"if"' in result


class TestFonts:
    def test_blackboard_bold(self) -> None:
        assert to_typst(r"\mathbb{R}") == "bb(R)"

    def test_calligraphic(self) -> None:
        assert to_typst(r"\mathcal{L}") == "cal(L)"

    def test_text_becomes_a_string(self) -> None:
        assert to_typst(r"\text{if}") == '"if"'


class TestCompiles:
    """Everything above is only useful if Typst actually accepts the output."""

    @pytest.mark.parametrize(
        "expression",
        [
            r"\frac{-b \pm \sqrt{b^2-4ac}}{2a}",
            r"e^{i\pi} + 1 = 0",
            r"\int_{-\infty}^{\infty} e^{-x^2}\,dx = \sqrt{\pi}",
            r"\sum_{i=1}^{n} i = \frac{n(n+1)}{2}",
            r"\lim_{x \to 0} \frac{\sin x}{x} = 1",
            r"P(A \mid B) = \frac{P(B \mid A)P(A)}{P(B)}",
            r"\begin{pmatrix} a & b \\ c & d \end{pmatrix}",
            r"\begin{cases} x & \text{if } x > 0 \\ -x & \text{otherwise} \end{cases}",
            r"\forall \epsilon > 0, \exists \delta",
            r"x \in \mathbb{Z} \setminus \{0\}",
            r"\vec{v} \cdot \hat{n}",
            r"\max_{i} x_i",
        ],
    )
    def test_translation_compiles(self, expression: str, tmp_path) -> None:
        assert compiles(to_typst(expression), tmp_path)


class TestMarkdownIntegration:
    def test_inline_math_is_translated(self) -> None:
        assert "frac(a, b)" in convert(r"Value is $\frac{a}{b}$ here.")

    def test_block_math_is_translated(self) -> None:
        result = convert("$$\n\\frac{a}{b}\n$$\n")
        assert "$ frac(a, b) $" in result


class TestDollarsThatAreNotMath:
    """Prices and shell variables must survive having math enabled."""

    @pytest.mark.parametrize(
        "text",
        [
            "Price is $10",
            "It costs $10 and $20 total",
            "Between $5 and $500 per month",
            "Use $HOME and $PATH variables",
            "Run: export $FOO && echo $BAR",
            "A $ B $ C",
        ],
    )
    def test_literal_dollars_are_escaped_not_parsed(self, text: str) -> None:
        result = convert(text)
        assert "\\$" in result
        for word in text.replace("$", "").split():
            assert word in result

    def test_real_inline_math_still_works_alongside(self) -> None:
        result = convert(r"Costs $10 but $x^2$ is math")
        assert "\\$10" in result
        assert "$x^2$" in result
