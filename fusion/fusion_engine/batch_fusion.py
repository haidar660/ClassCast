"""
Batch Fusion Engine for ClassCast Pipeline

This module implements batched OpenAI API calls to avoid rate limiting.
Instead of sending one request per segment, it groups segments into batches
and processes them together in a single API call.

Features:
- Batch processing (configurable batch size)
- Exponential backoff retry logic (up to 5 retries)
- Graceful error handling
- TTS-ready output (no LaTeX symbols)
"""

import os
import json
import time
import base64
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import requests

from utils.logging_utils import setup_logger
from utils.latex_converter import latex_to_text

logger = setup_logger(__name__)

# Load environment variables
load_dotenv()


def batch_fuse_segments(
    segments: List[Dict[str, Any]],
    frames: List[Dict[str, Any]],
    board_elements: Optional[List[List[str]]] = None,
    batch_size: int = 4
) -> List[str]:
    """
    Batch-fuse multiple transcript segments with their corresponding frames and board content.

    This function processes segments in batches to reduce API calls and avoid rate limiting.
    Each batch is sent as a single OpenAI request, returning multiple fused sentences at once.

    Args:
        segments: List of transcript segments, each with:
            - 'text': transcript text
            - 'start': start time in seconds
            - 'end': end time in seconds
        frames: List of frame info, each with:
            - 'path': path to frame image
            - 'time': timestamp in seconds
        board_elements: Optional list of LaTeX strings for each segment (parallel to segments)
        batch_size: Number of segments to process per API call (default: 4)

    Returns:
        List of fused podcast-ready sentences (one per segment, in order)

    Example:
        >>> segments = [
        ...     {'text': 'Let us examine derivatives', 'start': 0, 'end': 5},
        ...     {'text': 'The function f of x', 'start': 5, 'end': 10}
        ... ]
        >>> frames = [
        ...     {'path': 'frame_0.jpg', 'time': 2.5},
        ...     {'path': 'frame_1.jpg', 'time': 7.5}
        ... ]
        >>> fused = batch_fuse_segments(segments, frames)
    """
    logger.info(f"Starting batch fusion for {len(segments)} segments with batch_size={batch_size}")

    # Initialize board_elements if not provided
    if board_elements is None:
        board_elements = [[] for _ in segments]

    # Prepare batch items
    items = []
    for idx, (segment, frame, board) in enumerate(zip(segments, frames, board_elements)):
        items.append({
            'id': idx,
            'transcript': segment['text'],
            'board_latex': board if board else [],
            'frame_path': frame['path']
        })

    # Process in batches
    all_fused = [None] * len(items)  # Placeholder list to maintain order
    num_batches = (len(items) + batch_size - 1) // batch_size

    for batch_idx in range(num_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, len(items))
        batch = items[start_idx:end_idx]

        logger.info(f"Processing batch {batch_idx + 1}/{num_batches} ({len(batch)} items)")

        # Try fusion with exponential backoff
        result = _fuse_batch_with_retry(batch, max_retries=5)

        # Map results back to original indices
        if result['success']:
            for fused_item in result['data']:
                original_idx = fused_item['id']
                all_fused[original_idx] = fused_item['fused']
        else:
            # On failure, use error message for this batch
            logger.error(f"Batch {batch_idx + 1} failed permanently: {result['error']}")
            for item in batch:
                all_fused[item['id']] = f"[Fusion error: {result['error']}]"

        # Small delay between batches to be gentle on rate limits
        if batch_idx < num_batches - 1:
            time.sleep(0.5)

    logger.info("Batch fusion complete")
    return all_fused


def _fuse_batch_with_retry(batch: List[Dict[str, Any]], max_retries: int = 5) -> Dict[str, Any]:
    """
    Attempt to fuse a batch with exponential backoff retry logic.

    Retry delays: 1s, 2s, 4s, 8s, 16s

    Args:
        batch: List of items to fuse in this batch
        max_retries: Maximum number of retry attempts

    Returns:
        Dictionary with:
            - 'success': bool
            - 'data': list of fused results (if success)
            - 'error': error message (if failure)
    """
    for attempt in range(max_retries):
        try:
            logger.debug(f"Fusion attempt {attempt + 1}/{max_retries}")

            # Call OpenAI API with the batch
            result = _call_openai_batch_fusion(batch)

            # Success!
            logger.info(f"Batch fusion succeeded on attempt {attempt + 1}")
            return {
                'success': True,
                'data': result,
                'error': None
            }

        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Batch fusion attempt {attempt + 1} failed: {error_msg}")

            # Check if it's a rate limit error
            is_rate_limit = '429' in error_msg or 'rate_limit' in error_msg.lower()

            if attempt < max_retries - 1:
                # Calculate exponential backoff delay
                delay = 2 ** attempt  # 1, 2, 4, 8, 16 seconds
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                # Max retries reached
                logger.error(f"Batch fusion failed after {max_retries} attempts")
                return {
                    'success': False,
                    'data': None,
                    'error': error_msg
                }

    # Should never reach here, but just in case
    return {
        'success': False,
        'data': None,
        'error': 'Unknown error in retry logic'
    }


def _call_openai_batch_fusion(batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Call OpenAI API to fuse a batch of segments.

    Args:
        batch: List of items, each with:
            - id: segment index
            - transcript: transcript text
            - board_latex: list of LaTeX strings
            - frame_path: path to frame image

    Returns:
        List of results: [{"id": 0, "fused": "..."}, ...]

    Raises:
        Exception: If API call fails
    """
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")

    # Build the messages
    system_message = {
        "role": "system",
        "content": """You are an expert fusion engine for educational content.

Your task: Preserve the professor's EXACT words. Only add board content when the professor EXPLICITLY AND CLEARLY references it.

CRITICAL RULES:
1. PRESERVE the professor's exact wording - DO NOT paraphrase, rewrite, or add anything
2. ONLY add board content if the professor uses EXPLICIT reference words:
   - "this [equation/formula]" where they're pointing at the board
   - "let's examine this" where "this" refers to board content
   - "as you can see here" referring to visual content

   DO NOT add board content for:
   - General words like "this", "these", "that" used in normal speech
   - Incomplete sentences at segment boundaries (these are transcription artifacts)
   - Any sentence that makes sense on its own

3. When you DO add board content, insert it naturally in spoken form - NO LaTeX:
   - "x squared" not "x^2"
   - "f prime of x" not "f'(x)"

4. Never mention "the board", "the image", or "OCR"

5. DEFAULT BEHAVIOR: If unsure, return the transcript EXACTLY as-is without changes

6. Process each item independently

7. Return JSON list with same IDs

Output format MUST be valid JSON:
[
  {"id": 0, "fused": "exact transcript verbatim unless CLEAR board reference"},
  {"id": 1, "fused": "another sentence"},
  ...
]"""
    }

    # Prepare the batch data for the user message
    batch_data = []
    for item in batch:
        batch_data.append({
            "id": item['id'],
            "transcript": item['transcript'],
            "board_latex": item['board_latex']
        })

    user_message = {
        "role": "user",
        "content": f"""For each segment below, preserve the professor's EXACT words. Only add board content where the professor explicitly references it.

{json.dumps(batch_data, indent=2)}

Return a JSON list with the same IDs. Do NOT paraphrase - keep the professor's original wording."""
    }

    # Make the API request
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [system_message, user_message],
        "temperature": 0.7,
        "max_tokens": 500 * len(batch),  # Scale with batch size
        "response_format": {"type": "json_object"}  # Ensure JSON response
    }

    logger.debug(f"Sending batch fusion request for {len(batch)} items")
    response = requests.post(url, headers=headers, json=payload, timeout=60)

    # Check for errors
    if response.status_code != 200:
        error_detail = response.text
        raise Exception(f"OpenAI API error {response.status_code}: {error_detail}")

    # Parse response
    result = response.json()
    content = result['choices'][0]['message']['content']

    # Parse the JSON content
    try:
        # Try to parse as JSON
        fused_results = json.loads(content)

        # Handle both list and dict with various keys
        if isinstance(fused_results, dict):
            # Try common keys for list of results
            for key in ['results', 'fused_segments', 'segments', 'items']:
                if key in fused_results and isinstance(fused_results[key], list):
                    fused_results = fused_results[key]
                    break
            else:
                # Check if this dict itself is a single result
                if 'id' in fused_results and 'fused' in fused_results:
                    fused_results = [fused_results]
                else:
                    # Try to extract list from any key that contains a list
                    for value in fused_results.values():
                        if isinstance(value, list) and len(value) > 0:
                            fused_results = value
                            break
                    else:
                        # Single dict, wrap in list
                        fused_results = [fused_results]

        # Ensure it's a list
        if not isinstance(fused_results, list):
            raise ValueError(f"Expected list of results, got: {type(fused_results)}")

        # Validate and fix structure
        validated_results = []
        for idx, item in enumerate(fused_results):
            if not isinstance(item, dict):
                logger.warning(f"Item {idx} is not a dict: {item}")
                continue

            # Ensure 'id' key exists
            if 'id' not in item:
                logger.warning(f"Item missing 'id', using index: {item}")
                item['id'] = idx

            # Ensure 'fused' key exists
            if 'fused' not in item:
                # Try alternative keys
                for alt_key in ['text', 'sentence', 'content', 'result']:
                    if alt_key in item:
                        item['fused'] = item[alt_key]
                        break
                else:
                    logger.error(f"Item {item['id']} missing fused text: {item}")
                    item['fused'] = f"[Error: No fused text returned for segment {item['id']}]"

            validated_results.append(item)

        # Post-process: Convert any remaining LaTeX to plain text
        for item in validated_results:
            item['fused'] = latex_to_text(item['fused'])

        logger.debug(f"Successfully parsed {len(validated_results)} fused results")
        return validated_results

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OpenAI response as JSON: {content}")
        raise Exception(f"Invalid JSON response from OpenAI: {e}")


def batch_fuse_simple(
    transcript_texts: List[str],
    frame_paths: List[str],
    batch_size: int = 4
) -> List[str]:
    """
    Simplified batch fusion interface for quick integration.

    Args:
        transcript_texts: List of transcript strings
        frame_paths: List of frame image paths (parallel to transcripts)
        batch_size: Number of items per batch

    Returns:
        List of fused sentences (one per input)

    Example:
        >>> texts = ["Let's examine derivatives", "The chain rule states"]
        >>> paths = ["frame_1.jpg", "frame_2.jpg"]
        >>> fused = batch_fuse_simple(texts, paths)
    """
    # Convert to expected format
    segments = [
        {'text': text, 'start': i * 10, 'end': (i + 1) * 10}
        for i, text in enumerate(transcript_texts)
    ]

    frames = [
        {'path': path, 'time': i * 10}
        for i, path in enumerate(frame_paths)
    ]

    return batch_fuse_segments(segments, frames, batch_size=batch_size)


if __name__ == "__main__":
    # Test the batch fusion system
    logger.info("Testing batch fusion system...")

    # Create sample data
    test_segments = [
        {'text': 'Functions are foundational', 'start': 0, 'end': 5},
        {'text': 'The derivative measures rate of change', 'start': 5, 'end': 10},
        {'text': 'For f of x equals x cubed', 'start': 10, 'end': 15},
    ]

    test_frames = [
        {'path': 'data/test_video/frames/frame_0000_t0.0s.jpg', 'time': 2},
        {'path': 'data/test_video/frames/frame_0001_t2.0s.jpg', 'time': 7},
        {'path': 'data/test_video/frames/frame_0002_t4.0s.jpg', 'time': 12},
    ]

    test_board = [
        ['FUNCTIONS'],
        ['Derivatives', "f'(x)"],
        ['f(x) = x^3'],
    ]

    # Run batch fusion
    results = batch_fuse_segments(
        segments=test_segments,
        frames=test_frames,
        board_elements=test_board,
        batch_size=2
    )

    # Display results
    print("\n" + "=" * 60)
    print("BATCH FUSION RESULTS")
    print("=" * 60)
    for idx, fused in enumerate(results):
        print(f"\n[Segment {idx + 1}]")
        print(f"Original: {test_segments[idx]['text']}")
        print(f"Fused: {fused}")
    print("\n" + "=" * 60)
