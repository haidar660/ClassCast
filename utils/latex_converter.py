"""
LaTeX to Plain Text Converter for Math Expressions.
Converts LaTeX mathematical notation to readable plain text for text-to-speech.
"""
import re
from typing import Dict, Tuple


def latex_to_text(latex_string: str) -> str:
    """
    Convert LaTeX mathematical notation to plain text suitable for text-to-speech.

    Args:
        latex_string: String containing LaTeX markup

    Returns:
        Plain text version suitable for speech synthesis
    """
    if not latex_string:
        return ""

    text = latex_string

    # Remove LaTeX delimiters
    text = re.sub(r'\\\[|\\\]|\\\(|\\\)', '', text)  # Display/inline math delimiters
    text = re.sub(r'\$\$|\$', '', text)  # Dollar sign delimiters

    # Greek letters (common ones)
    greek_letters = {
        r'\\alpha': 'alpha',
        r'\\beta': 'beta',
        r'\\gamma': 'gamma',
        r'\\delta': 'delta',
        r'\\epsilon': 'epsilon',
        r'\\theta': 'theta',
        r'\\lambda': 'lambda',
        r'\\mu': 'mu',
        r'\\pi': 'pi',
        r'\\sigma': 'sigma',
        r'\\phi': 'phi',
        r'\\omega': 'omega',
        r'\\Delta': 'Delta',
        r'\\Sigma': 'Sigma',
        r'\\Omega': 'Omega',
    }
    for latex, plain in greek_letters.items():
        text = re.sub(latex, plain, text)

    # Fractions: \frac{a}{b} -> a over b
    def replace_frac(match):
        numerator = match.group(1).strip()
        denominator = match.group(2).strip()
        return f"{numerator} over {denominator}"
    text = re.sub(r'\\frac\{([^{}]+)\}\{([^{}]+)\}', replace_frac, text)

    # Square roots: \sqrt{x} -> square root of x
    def replace_sqrt(match):
        content = match.group(1).strip()
        return f"square root of {content}"
    text = re.sub(r'\\sqrt\{([^{}]+)\}', replace_sqrt, text)

    # Limits: \lim_{x \to a} -> limit as x approaches a
    def replace_lim(match):
        var = match.group(1).strip()
        target = match.group(2).strip()
        return f"limit as {var} approaches {target} of"
    text = re.sub(r'\\lim_\{([^}]+)\\to\s*([^}]+)\}', replace_lim, text)

    # Integrals: \int_{a}^{b} -> integral from a to b
    def replace_int(match):
        lower = match.group(1).strip() if match.group(1) else ""
        upper = match.group(2).strip() if match.group(2) else ""
        if lower and upper:
            return f"integral from {lower} to {upper} of"
        else:
            return "integral of"
    text = re.sub(r'\\int(?:_\{([^}]+)\})?\^\{([^}]+)\}', replace_int, text)
    text = re.sub(r'\\int', 'integral of', text)

    # Summation: \sum_{i=1}^{n} -> sum from i equals 1 to n
    def replace_sum(match):
        lower = match.group(1).strip() if match.group(1) else ""
        upper = match.group(2).strip() if match.group(2) else ""
        if lower and upper:
            return f"sum from {lower} to {upper} of"
        else:
            return "sum of"
    text = re.sub(r'\\sum(?:_\{([^}]+)\})?\^\{([^}]+)\}', replace_sum, text)
    text = re.sub(r'\\sum', 'sum of', text)

    # Derivatives: \frac{d}{dx} -> derivative with respect to x
    text = re.sub(r'\\frac\{d\}\{d([a-z])\}', r'derivative with respect to \1', text)

    # Superscripts: x^2 -> x squared, x^3 -> x cubed, x^n -> x to the power of n
    def replace_superscript(match):
        base = match.group(1).strip() if match.group(1) else ""
        exp = match.group(2).strip()

        # Handle common cases
        if exp == '2':
            return f"{base} squared"
        elif exp == '3':
            return f"{base} cubed"
        elif exp == '-1':
            return f"{base} to the minus 1"
        elif len(exp) == 1:
            return f"{base} to the power of {exp}"
        else:
            return f"{base} to the power of {exp}"

    # Match x^{...} or x^n with optional preceding character
    text = re.sub(r'([a-zA-Z0-9]+)\^\{([^}]+)\}', replace_superscript, text)
    text = re.sub(r'([a-zA-Z0-9]+)\^([a-zA-Z0-9])', replace_superscript, text)

    # Subscripts: x_i -> x sub i
    text = re.sub(r'([a-zA-Z0-9]+)_\{([^}]+)\}', r'\1 sub \2', text)
    text = re.sub(r'([a-zA-Z0-9]+)_([a-zA-Z0-9])', r'\1 sub \2', text)

    # Common functions
    text = re.sub(r'\\sin', 'sine', text)
    text = re.sub(r'\\cos', 'cosine', text)
    text = re.sub(r'\\tan', 'tangent', text)
    text = re.sub(r'\\log', 'log', text)
    text = re.sub(r'\\ln', 'natural log', text)
    text = re.sub(r'\\exp', 'exponential', text)

    # Parentheses and brackets
    text = re.sub(r'\\left\(', '(', text)
    text = re.sub(r'\\right\)', ')', text)
    text = re.sub(r'\\left\[', '[', text)
    text = re.sub(r'\\right\]', ']', text)
    text = re.sub(r'\\left\{', '{', text)
    text = re.sub(r'\\right\}', '}', text)

    # Remove remaining backslashes and braces for simple cases
    text = re.sub(r'\\,|\\;|\\:|\\!', ' ', text)  # Spacing commands
    text = re.sub(r'\\text\{([^}]+)\}', r'\1', text)  # Text mode
    text = re.sub(r'\\mathrm\{([^}]+)\}', r'\1', text)  # Roman text
    text = re.sub(r'\\mathbf\{([^}]+)\}', r'\1', text)  # Bold

    # Convert mathematical operators to words (for TTS)
    text = text.replace('+', ' plus ')
    text = text.replace('-', ' minus ')
    text = text.replace('*', ' times ')
    text = text.replace('×', ' times ')
    text = text.replace('/', ' divided by ')
    text = text.replace('=', ' equals ')
    text = text.replace('≠', ' not equal to ')
    text = text.replace('<', ' less than ')
    text = text.replace('>', ' greater than ')
    text = text.replace('≤', ' less than or equal to ')
    text = text.replace('≥', ' greater than or equal to ')
    # Keep parentheses minimal for natural speech
    text = text.replace('(', ' of ')
    text = text.replace(')', ' ')
    text = text.replace('[', ' ')
    text = text.replace(']', ' ')
    text = text.replace('{', ' ')
    text = text.replace('}', ' ')

    # Convert numbers adjacent to variables (e.g., "2x" -> "2 x")
    # This helps TTS read "two x" instead of "twox"
    text = re.sub(r'(\d+)([a-zA-Z])', r'\1 \2', text)

    # Clean up spacing
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    return text


def convert_ocr_result_to_text(ocr_result: Dict) -> Tuple[str, str]:
    """
    Convert OCR result containing LaTeX to plain text.

    Args:
        ocr_result: OCR result dictionary with 'text' field

    Returns:
        Tuple of (original_text, converted_plain_text)
    """
    original = ocr_result.get('text', '')
    plain_text = latex_to_text(original)

    return original, plain_text


# Test cases
if __name__ == "__main__":
    test_cases = [
        r"\( f(x) = 3x^2 + 2 \)",
        r"\frac{2x + 5}{x - 1}",
        r"\lim_{x \to 0} \frac{\sin x}{x} = 1",
        r"\frac{d}{dx} \left( x^2 \right) = 2x",
        r"\int_{0}^{1} x^{2} \, dx",
        r"MSE = \frac{1}{n} \sum_{i=1}^{n} (y_i - \hat{y}_i)^2",
    ]

    print("LaTeX to Plain Text Converter Test\n")
    print("=" * 80)

    for latex in test_cases:
        plain = latex_to_text(latex)
        print(f"\nLaTeX:  {latex}")
        print(f"Plain:  {plain}")
        print("-" * 80)
    