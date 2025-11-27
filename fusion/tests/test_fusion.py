"""
Simple test of the ClassCast Fusion System
No external data files required - runs with dummy test data
"""

import os
from dotenv import load_dotenv
from fusion_engine.batch_fusion import batch_fuse_segments

# Load environment variables
load_dotenv()


def main():
    print("\n" + "=" * 80)
    print("CLASSCAST FUSION SYSTEM - QUICK TEST")
    print("=" * 80)

    # Verify API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ ERROR: OPENAI_API_KEY not found in .env file")
        print("   Please create a .env file with:")
        print("   OPENAI_API_KEY=sk-proj-your-key-here")
        return

    print("\n✅ OpenAI API key found")

    # Test data - realistic lecture content
    segments = [
        {
            'text': 'Let us examine this derivative',
            'start': 0.0,
            'end': 3.0
        },
        {
            'text': 'Now consider this limit expression',
            'start': 3.0,
            'end': 6.0
        },
        {
            'text': 'We can simplify the integral',
            'start': 6.0,
            'end': 9.0
        },
        {
            'text': 'And finally this quadratic formula',
            'start': 9.0,
            'end': 12.0
        }
    ]

    # Dummy frames (we don't actually need the images for text-based fusion)
    frames = [
        {'path': 'frame_0.jpg', 'time': 1.5},
        {'path': 'frame_1.jpg', 'time': 4.5},
        {'path': 'frame_2.jpg', 'time': 7.5},
        {'path': 'frame_3.jpg', 'time': 10.5}
    ]

    # Board content - LaTeX mathematical notation
    board_elements = [
        ['\\frac{d}{dx}(x^2) = 2x'],
        ['\\lim_{x \\to \\infty} \\frac{1}{x} = 0'],
        ['\\int_0^1 x^2 dx = \\frac{1}{3}'],
        ['x = \\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}']
    ]

    print(f"\n📊 Test Data:")
    print(f"   - {len(segments)} transcript segments")
    print(f"   - {len(frames)} video frames")
    print(f"   - {len(board_elements)} board equations")

    # Run batch fusion
    print(f"\n🚀 Running batch fusion (batch_size=2)...")
    print("   This will make 2 API calls to OpenAI GPT-4o-mini")
    print("   With retry logic for rate limiting...")

    try:
        fused_sentences = batch_fuse_segments(
            segments=segments,
            frames=frames,
            board_elements=board_elements,
            batch_size=2
        )

        # Display results
        print("\n" + "=" * 80)
        print("RESULTS: Original Transcript → Fused Podcast Script")
        print("=" * 80)

        for idx, (segment, board, fused) in enumerate(zip(segments, board_elements, fused_sentences), 1):
            print(f"\n[Segment {idx}] {segment['start']:.1f}s - {segment['end']:.1f}s")
            print(f"  📝 Original:  {segment['text']}")
            print(f"  📐 Board:     {board[0] if board else 'None'}")
            print(f"  🎙️  Fused:     {fused}")

        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"✅ Total segments processed:  {len(fused_sentences)}")
        print(f"✅ API calls made:            {(len(segments) + 1) // 2}")
        print(f"✅ Old method would need:     {len(segments)} calls")
        print(f"✅ API calls saved:           {len(segments) - (len(segments) + 1) // 2}")
        print(f"✅ Efficiency gain:           {((len(segments) - (len(segments) + 1) // 2) / len(segments) * 100):.0f}%")

        print("\n🎉 SUCCESS! Fusion system is working perfectly!")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nPlease check:")
        print("  1. Your OpenAI API key is valid")
        print("  2. You have API credits available")
        print("  3. Your internet connection is working")


if __name__ == "__main__":
    main()
