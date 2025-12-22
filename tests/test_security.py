import asyncio
import json
import websockets
import pytest

async def run_test(payload, test_name):
    """Connects to the WebSocket, sends a payload, and prints the response."""
    uri = "ws://localhost:8000/ws/verify"
    print(f"--- Running Test: {test_name} ---")
    try:
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps(payload))
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                print("✅ Server Response:")
                print(json.loads(response))
            except asyncio.TimeoutError:
                print("✅ Server did not respond, which may be correct (e.g., silent close).")

    except websockets.exceptions.ConnectionClosed as e:
        print(f"✅ Connection closed as expected: Code={e.code}, Reason='{e.reason}'")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
    print("-" * (len(test_name) + 20) + "\n")

async def main():
    # Test 1: Invalid `max_iterations` (out of range)
    invalid_iterations_payload = {
        "input": "test",
        "max_iterations": 99
    }
    await run_test(invalid_iterations_payload, "Invalid Iterations")

    # Test 2: Invalid `type`
    invalid_type_payload = {
        "input": "test",
        "type": "INVALID_TYPE"
    }
    await run_test(invalid_type_payload, "Invalid Type")

    # Test 3: Invalid URL format with type="URL"
    invalid_url_payload = {
        "input": "not-a-valid-url",
        "type": "URL"
    }
    await run_test(invalid_url_payload, "Invalid URL Format")

    # Test 4: URL with invalid protocol
    ftp_url_payload = {
        "input": "ftp://example.com/file.txt",
        "type": "URL"
    }
    await run_test(ftp_url_payload, "Invalid URL Protocol")

    # Test 5: Empty input (should fail min_length constraint)
    empty_input_payload = {
        "input": "",
        "type": "Text"
    }
    await run_test(empty_input_payload, "Empty Input")

    # Test 6: Input too long (> 10000 chars)
    long_input_payload = {
        "input": "x" * 10001,
        "type": "Text"
    }
    await run_test(long_input_payload, "Input Too Long")

    # Test 7: Invalid personality type
    invalid_personality_payload = {
        "input": "test",
        "proPersonality": "INVALID_PERSONALITY"
    }
    await run_test(invalid_personality_payload, "Invalid Personality")

    # Test 8: Invalid language
    invalid_language_payload = {
        "input": "test",
        "language": "Spanish"
    }
    await run_test(invalid_language_payload, "Invalid Language")

    # Test 9: Invalid max_searches (negative, not -1)
    invalid_searches_payload = {
        "input": "test",
        "max_searches": -5
    }
    await run_test(invalid_searches_payload, "Invalid Max Searches")

if __name__ == "__main__":
    asyncio.run(main())