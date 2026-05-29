from dotenv import load_dotenv
import os
import anthropic

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")

print("=" * 50)
print("API Key Loaded:", api_key is not None)
print("=" * 50)

client = anthropic.Anthropic(
    api_key=api_key
)

try:
    response = client.messages.create(
        model="claude-sonnet-4-0",  # change if needed
        max_tokens=50,
        messages=[
            {
                "role": "user",
                "content": "Say hello in one sentence."
            }
        ]
    )

    print("\nSUCCESS")
    print(response.content[0].text)

except Exception as e:
    print("\nERROR")
    print(type(e).__name__)
    print(e)