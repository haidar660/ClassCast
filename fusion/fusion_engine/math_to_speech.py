"""
    Math-to-speech conversion module for creating natural-sounding TTS from mathematical content.

Converts mathematical symbols and notation into natural English for spoken audio.
Based on CLAUDE.md specifications.
"""
import re
from typing import Dict

from utils.logging_utils import setup_logger

logger = setup_logger(__name__)


# Symbol mappings for math-to-speech conversion
MATH_SYMBOLS = {
    '=': ' equals ',
    '≈': ' approximately equals ',
    '≠': ' does not equal ',
    '≡': ' is equivalent to ',
    '+': ' plus ',
    '-': ' minus ',
    '−': ' minus ',  # Unicode minus
    '×': ' times ',
    '*': ' times ',
    '÷': ' divided by ',
    '/': ' divided by ',
    '±': ' plus or minus ',
    '∓': ' minus or plus ',
    '<': ' is less than ',
    '>': ' is greater than ',
    '≤': ' is less than or equal to ',
    '≥': ' is greater than or equal to ',
    '≪': ' is much less than ',
    '≫': ' is much greater than ',
    '∞': ' infinity ',
    '∑': ' sum ',
    '∏': ' product ',
    '∫': ' integral ',
    '∂': ' partial derivative ',
    '∇': ' del ',
    '√': ' square root of ',
    '∛': ' cube root of ',
    '∈': ' is in ',
    '∉': ' is not in ',
    '⊂': ' is a subset of ',
    '⊃': ' is a superset of ',
    '∪': ' union ',
    '∩': ' intersection ',
    '∧': ' and ',
    '∨': ' or ',
    '¬': ' not ',
    '⇒': ' implies ',
    '⇔': ' if and only if ',
    '∀': ' for all ',
    '∃': ' there exists ',
    'π': ' pi ',
    'Δ': ' delta ',
    'α': ' alpha ',
    'β': ' beta ',
    'γ': ' gamma ',
    'θ': ' theta ',
    'λ': ' lambda ',
    'μ': ' mu ',
    'σ': ' sigma ',
    'φ': ' phi ',
    'ω': ' omega ',
}


def convert_exponents_to_speech(text: str) -> str:
    """
    Convert exponent notation to natural speech.

    Examples:
        x^2 -> x to the power of two
        x² -> x squared
        x³ -> x cubed
        x^4 -> x to the power of four
        2^n -> two to the power of n

    Args:
        text: Input text with exponent notation

    Returns:
        Text with exponents converted to speech
    """
    # Handle superscript Unicode characters
    superscript_map = {
        '⁰': 'zero', '¹': 'one', '²': 'two', '³': 'three', '⁴': 'four',
        '⁵': 'five', '⁶': 'six', '⁷': 'seven', '⁸': 'eight', '⁹': 'nine'
    }

    # Convert Unicode superscripts
    for sup, word in superscript_map.items():
        if sup == '²':
            text = text.replace(sup, ' squared')
        elif sup == '³':
            text = text.replace(sup, ' cubed')
        else:
            text = text.replace(sup, f' to the power of {word}')

    # Convert caret notation (x^2)
    # Match patterns like x^2, x^n, (x+1)^2, etc.
    def replace_caret(match):
        base = match.group(1)
        exp = match.group(2)

        # Special cases
        if exp == '2':
            return f"{base} squared"
        elif exp == '3':
            return f"{base} cubed"
        elif exp == '1':
            return base  # x^1 is just x
        else:
            return f"{base} to the power of {exp}"

    # Pattern: capture base (variable or parenthesized expression) and exponent
    text = re.sub(r'([a-zA-Z0-9\)]+)\^([a-zA-Z0-9\-\+]+)', replace_caret, text)

    return text


def convert_fractions_to_speech(text: str) -> str:
    """
    Convert fraction notation to natural speech.

    Examples:
        1/2 -> one half
        3/4 -> three quarters
        a/b -> a over b
        (x+1)/(y-2) -> x plus one over y minus two

    Args:
        text: Input text with fraction notation

    Returns:
        Text with fractions converted to speech
    """
    # Common fractions with special names
    special_fractions = {
        '1/2': 'one half',
        '1/3': 'one third',
        '2/3': 'two thirds',
        '1/4': 'one quarter',
        '3/4': 'three quarters',
        '1/5': 'one fifth',
        '1/8': 'one eighth',
    }

    # Replace special fractions first
    for frac, speech in special_fractions.items():
        text = text.replace(frac, speech)

    # General pattern: numerator/denominator
    # For simple cases, use "over"
    def replace_fraction(match):
        num = match.group(1)
        den = match.group(2)
        return f"{num} over {den}"

    # Pattern: number or variable / number or variable
    text = re.sub(r'([a-zA-Z0-9\+\-\*]+)/([a-zA-Z0-9\+\-\*]+)', replace_fraction, text)

    return text


def convert_parentheses_to_speech(text: str) -> str:
    """
    Convert parentheses to natural speech descriptions.

    Examples:
        (x+1) -> open parenthesis x plus one close parenthesis (for complex expressions)
        For simple cases, keep them implicit

    Args:
        text: Input text with parentheses

    Returns:
        Text with parentheses handled naturally
    """
    # For TTS, we generally keep parentheses implicit in the flow
    # Only make them explicit if they're complex nested expressions

    # Count nesting level - if simple, remove parens, if complex, keep
    # For now, we'll keep them as they help with pacing in TTS
    return text


def convert_functions_to_speech(text: str) -> str:
    """
    Convert mathematical functions to natural speech.

    Examples:
        f(x) -> f of x
        sin(x) -> sine of x
        log(x) -> logarithm of x

    Args:
        text: Input text with function notation

    Returns:
        Text with functions converted to speech
    """
    function_names = {
        'sin': 'sine',
        'cos': 'cosine',
        'tan': 'tangent',
        'arcsin': 'arc sine',
        'arccos': 'arc cosine',
        'arctan': 'arc tangent',
        'sinh': 'hyperbolic sine',
        'cosh': 'hyperbolic cosine',
        'tanh': 'hyperbolic tangent',
        'log': 'logarithm',
        'ln': 'natural logarithm',
        'exp': 'exponential',
        'sqrt': 'square root',
    }

    for func, speech in function_names.items():
        # Replace function(arg) with "function of arg"
        text = re.sub(rf'\b{func}\(', f'{speech} of (', text, flags=re.IGNORECASE)

    # Generic function notation f(x) -> f of x
    text = re.sub(r'([a-zA-Z])\(', r'\1 of (', text)

    return text


def convert_subscripts_to_speech(text: str) -> str:
    """
    Convert subscript notation to natural speech.

    Examples:
        x_1 -> x sub one
        a_n -> a sub n
        y_i -> y sub i

    Args:
        text: Input text with subscript notation

    Returns:
        Text with subscripts converted to speech
    """
    # Pattern: variable_subscript
    text = re.sub(r'([a-zA-Z])_([a-zA-Z0-9]+)', r'\1 sub \2', text)

    return text


def convert_special_numbers_to_speech(text: str) -> str:
    """
    Convert decimal numbers and special formats to speech.

    Examples:
        0.4 -> zero point four
        0.24 -> zero point two four
        1.5 -> one point five

    Args:
        text: Input text with numbers

    Returns:
        Text with numbers converted to speech
    """
    # Pattern: decimal numbers
    def replace_decimal(match):
        whole = match.group(1)
        decimal = match.group(2)

        num_words = {
            '0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four',
            '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'
        }

        whole_word = num_words.get(whole, whole)
        decimal_words = ' '.join(num_words.get(d, d) for d in decimal)

        return f"{whole_word} point {decimal_words}"

    # Match decimal numbers like 0.4, 1.5, etc.
    text = re.sub(r'\b(\d+)\.(\d+)\b', replace_decimal, text)

    return text


def convert_hat_notation_to_speech(text: str) -> str:
    """
    Convert hat notation (predictions) to speech.

    Examples:
        y_hat -> y hat
        ŷ -> y hat

    Args:
        text: Input text with hat notation

    Returns:
        Text with hat notation converted
    """
    # Unicode hat symbols
    text = text.replace('ŷ', 'y hat')
    text = text.replace('x̂', 'x hat')

    # Underscore hat notation
    text = re.sub(r'([a-zA-Z])_hat', r'\1 hat', text)

    return text


def convert_arrows_to_speech(text: str) -> str:
    """
    Convert arrow notation to speech.

    Examples:
        → -> approaches
        x → 0 -> x approaches zero

    Args:
        text: Input text with arrows

    Returns:
        Text with arrows converted to speech
    """
    text = text.replace('→', ' approaches ')
    text = text.replace('←', ' comes from ')
    text = text.replace('↔', ' corresponds to ')

    return text


def clean_multiple_spaces(text: str) -> str:
    """Clean up multiple consecutive spaces."""
    return re.sub(r'\s+', ' ', text).strip()


def convert_coefficients_to_speech(text: str) -> str:
    """
    Convert coefficient-variable products to natural speech.

    Examples:
        3x -> three times x
        2y -> two times y
        -5a -> negative five times a

    Args:
        text: Input text with coefficient-variable notation

    Returns:
        Text with coefficients converted to speech
    """
    # Pattern: number followed by variable (with optional sign)
    # Match: 3x, -2y, 10z, etc.
    def replace_coefficient(match):
        sign = match.group(1) if match.group(1) else ""
        coeff = match.group(2)
        var = match.group(3)

        # Convert coefficient to words for single digits
        num_words = {
            '0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four',
            '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine',
            '10': 'ten'
        }

        sign_word = "negative " if sign == "-" else ""
        coeff_word = num_words.get(coeff, coeff)

        # Special case: coefficient of 1 is usually omitted
        if coeff == '1':
            return f"{sign_word}{var}"

        return f"{sign_word}{coeff_word} times {var}"

    # Pattern: optional sign, number, variable letter
    text = re.sub(r'([+-]?)(\d+)([a-zA-Z])', replace_coefficient, text)

    return text


def math_to_speech(text: str, verbose: bool = False) -> str:
    """
    Convert mathematical text to natural speech.

    Main conversion function that applies all transformations.

    Args:
        text: Input text with mathematical notation
        verbose: Whether to preserve some math notation for clarity

    Returns:
        Text optimized for spoken audio (TTS)
    """
    if not text:
        return text

    original_text = text

    # Apply conversions in order
    # 1. Hat notation (predictions) - before subscripts
    text = convert_hat_notation_to_speech(text)

    # 2. Arrows (limit notation) - before functions
    text = convert_arrows_to_speech(text)

    # 3. Functions (before parentheses)
    text = convert_functions_to_speech(text)

    # 4. Exponents (before coefficients to handle x^2 correctly)
    text = convert_exponents_to_speech(text)

    # 5. Coefficients (like 3x -> three times x)
    text = convert_coefficients_to_speech(text)

    # 6. Fractions (before symbols to handle /)
    text = convert_fractions_to_speech(text)

    # 7. Subscripts
    text = convert_subscripts_to_speech(text)

    # 8. Special numbers (decimals)
    text = convert_special_numbers_to_speech(text)

    # 9. Math symbols
    for symbol, speech in MATH_SYMBOLS.items():
        text = text.replace(symbol, speech)

    # 10. Clean up spacing
    text = clean_multiple_spaces(text)

    if verbose:
        logger.debug(f"Math-to-speech conversion: '{original_text}' -> '{text}'")

    return text


def create_fused_explanation(speech_text: str, board_text: str, board_markdown: str = "") -> str:
    """
    Create a fused explanation for UI display.

    Combines spoken content with board content in a natural way.
    This is for reading/display, not for TTS.

    Example:
        Speech: "Here we have the function f of x equals three x squared plus one"
        Board: "f(x) = 3x^2 + 1"
        Output: "Here we have the function f of x equals three x squared plus one.
                 On the board, the equation is f(x) = 3x^2 + 1."

    Args:
        speech_text: What the teacher said (ASR output)
        board_text: What's on the board (OCR output)
        board_markdown: Structured markdown version if available

    Returns:
        Fused explanation string
    """
    speech_text = speech_text.strip()
    board_content = (board_markdown.strip() if board_markdown else board_text.strip())

    if not speech_text and not board_content:
        return ""

    if not board_content:
        return speech_text

    if not speech_text:
        return f"On the board: {board_content}"

    # Combine naturally
    # Check if speech already mentions the board content
    if board_text.lower() in speech_text.lower() or len(board_text) < 5:
        # Board content is already implicit in speech
        return speech_text
    else:
        # Add board content explicitly
        return f"{speech_text} On the board, the equation is {board_content}."


def create_fused_tts_text(speech_text: str, board_text: str, board_markdown: str = "") -> str:
    """
    Create a fused TTS text optimized for spoken audio (podcast).

    NEW REQUIREMENTS (per updated CLAUDE.md):
    - ONE smooth, natural fused sentence
    - NO phrases like "on the board" or "as written"
    - Seamlessly merge transcript + OCR without repetition
    - Convert math to spoken language naturally
    - Sound like something a teacher would naturally say in a podcast

    Example:
        Speech: "Here we have the function f of x equals three x squared plus one. This is a simple quadratic function."
        Board: "f(x) = 3x^2 + 1"
        Output: "Here we have the function f of x equals three times x to the power of two plus one, which represents a simple quadratic function."

    Args:
        speech_text: What the teacher said (ASR output)
        board_text: What's on the board (OCR output)
        board_markdown: Structured markdown version if available

    Returns:
        Smoothly fused text ready for TTS/podcast
    """
    speech_text = speech_text.strip()
    board_content = (board_markdown.strip() if board_markdown else board_text.strip())

    if not speech_text and not board_content:
        return ""

    # If no board content, just return speech
    if not board_content:
        return speech_text

    # If no speech, convert board to natural language
    if not speech_text:
        board_speech = math_to_speech(board_content)
        return board_speech

    # Both exist - need to merge intelligently
    return merge_speech_and_board_naturally(speech_text, board_content)


def merge_speech_and_board_naturally(speech_text: str, board_text: str) -> str:
    """
    Intelligently merge speech and board content into one smooth sentence.

    NEW Strategy (per CLAUDE.md):
    - Convert board to spoken form
    - Look for where the formula is informally mentioned in speech
    - Replace informal mention with precise spoken version
    - Merge explanatory phrases naturally (e.g., "This is" -> "which represents")
    - Create ONE smooth sentence

    Args:
        speech_text: Transcript text
        board_text: OCR text from board

    Returns:
        Seamlessly fused sentence
    """
    # Convert board math to spoken form
    board_speech = math_to_speech(board_text)

    # Check if it's just a label/title (no math operators)
    if len(board_text) < 10 and not any(op in board_text for op in ['=', '+', '-', '*', '/', '^']):
        return speech_text

    # Strategy 1: Find if formula is partially described in speech
    # Look for patterns like "f of x equals [informal description]"

    speech_lower = speech_text.lower()

    # Check if formula is mentioned in speech
    has_formula = any([
        "f(x)" in speech_lower or "f of x" in speech_lower,
        ("equals" in speech_lower and any(c.isdigit() for c in speech_text)),
        ("squared" in speech_lower or "cubed" in speech_lower or "power" in speech_lower),
    ])

    if has_formula:
        # Formula is mentioned - we want to enhance it with the board version

        # Split into sentences
        sentences = [s.strip() for s in speech_text.split('.') if s.strip()]

        if len(sentences) >= 2:
            # Multiple sentences - merge them

            first_sentence = sentences[0]
            remaining = sentences[1:]

            # Check if first sentence contains the formula description
            if "equals" in first_sentence.lower() or "function" in first_sentence.lower():
                # This sentence has the formula - enhance it

                # Extract just the mathematical part from board_speech
                # e.g., "f of (x) equals three times x squared plus one"
                # We want to use this to replace/enhance the formula part

                # Look for "equals" pattern in first sentence
                if " equals " in first_sentence.lower():
                    # Find what comes after "equals"
                    parts = first_sentence.lower().split(" equals ")
                    if len(parts) == 2:
                        # Get the formula part from board_speech
                        if " equals " in board_speech.lower():
                            board_parts = board_speech.lower().split(" equals ")
                            if len(board_parts) == 2:
                                formula_spoken = board_parts[1].strip()

                                # Replace in original (preserve case)
                                equals_idx = first_sentence.lower().index(" equals ")
                                before_equals = first_sentence[:equals_idx + 8]  # include " equals "
                                enhanced_sentence = f"{before_equals}{formula_spoken}"

                                # Now handle remaining sentences
                                if remaining:
                                    # Transform explanatory sentences
                                    # "This is a simple quadratic function" ->
                                    # "which represents a simple quadratic function"
                                    next_sentence = remaining[0]

                                    if next_sentence.lower().startswith("this is"):
                                        # Transform to "which [verb]"
                                        rest_of_sentence = next_sentence[7:].strip()  # Remove "This is"
                                        connecting_phrase = f"which represents {rest_of_sentence}"
                                        result = f"{enhanced_sentence}, {connecting_phrase}"

                                        # Add any additional sentences
                                        if len(remaining) > 1:
                                            result += ". " + ". ".join(remaining[1:])

                                        return result
                                    else:
                                        # Just concatenate naturally
                                        return f"{enhanced_sentence}. {' '.join(remaining)}."

                                return f"{enhanced_sentence}."

    # Strategy 2: Formula not in speech - add it naturally
    if '=' not in board_text:
        # Not a formula, probably already mentioned
        return speech_text

    # Add formula naturally with connector phrase
    sentences = [s.strip() for s in speech_text.split('.') if s.strip()]

    if sentences:
        first = sentences[0]
        if len(sentences) > 1:
            rest = ". ".join(sentences[1:])
            # Insert formula after first sentence
            return f"{first}, that is, {board_speech}. {rest}."
        else:
            # Single sentence
            if first.lower().endswith(("function", "equation", "formula", "expression")):
                return f"{first}, {board_speech}."
            else:
                return f"{first}, that is, {board_speech}."

    return speech_text
