#!/usr/bin/env python3
import sys
import json
import argparse
import os
from pathlib import Path

try:
    from mistral_sdk import Mistral
except ImportError:
    print("Error: mistral-sdk package not found. Install it with: pip install mistral-sdk")
    sys.exit(1)

SYSTEM_PROMPT = """You are an empathetic reflection assistant. Given a first-person journal entry or diary note, respond ONLY with valid JSON in this exact format:
{
  "keyPeopleEvents": ["item 1", "item 2", "item 3"],
  "reflectionBullets": ["reflection 1", "reflection 2", "reflection 3"]
}

Rules:
1. Extract key people and events as bullet points (identify specific people, main activities/events)
2. Write 3 concise reflection bullets capturing emotional insights (max 15 words each)
3. Keep tone supportive, realistic, and forward-looking
4. Return ONLY valid JSON, no other text"""


def reflect_on_entry(entry: str) -> None:
    """Analyze a diary entry using Mistral-7B and display formatted results."""
    try:
        print("\n✨ Analyzing your diary entry...\n")
        
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            print("❌ Error: MISTRAL_API_KEY environment variable not set")
            sys.exit(1)
        
        client = Mistral(api_key=api_key)
        
        message = client.chat.complete(
            model="mistral-7b-instruct",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": f"Analyze this diary entry:\n\n{entry}"
                }
            ],
            max_tokens=1024,
            temperature=0.7
        )
        
        text = message.choices[0].message.content
        parsed = json.loads(text)
        
        print("\n" + "━" * 42)
        print("📌 KEY PEOPLE & EVENTS")
        print("━" * 42 + "\n")
        for idx, item in enumerate(parsed.get("keyPeopleEvents", []), 1):
            print(f"  {idx}. {item}")
        
        print("\n" + "━" * 42)
        print("💭 REFLECTION INSIGHTS")
        print("━" * 42 + "\n")
        for bullet in parsed.get("reflectionBullets", []):
            print(f"  • {bullet}")
        
        print("\n" + "━" * 42 + "\n")
    
    except json.JSONDecodeError as e:
        print(f"❌ Error: Failed to parse AI response as JSON: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze your diary entries with AI-powered reflections using Mistral-7B",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                  # Interactive mode - type your entry
  %(prog)s entry.txt        # Analyze a diary entry from a file

Environment:
  MISTRAL_API_KEY           # Required for API authentication
        """
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Path to a diary entry file (optional; if not provided, enter interactive mode)"
    )
    
    args = parser.parse_args()
    
    print("\n" + "═" * 43)
    print("    📔 DIARY REFLECTION CLI")
    print("═" * 43 + "\n")
    
    if args.file:
        try:
            file_path = Path(args.file)
            entry = file_path.read_text(encoding="utf-8")
            reflect_on_entry(entry)
        except FileNotFoundError:
            print(f"❌ Error: File not found: {args.file}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error reading file: {str(e)}")
            sys.exit(1)
    else:
        print("📝 Write your diary entry (press Enter twice to submit):\n")
        
        entry = []
        empty_line_count = 0
        
        try:
            while True:
                line = input()
                if line == "":
                    empty_line_count += 1
                    if empty_line_count == 2:
                        break
                else:
                    empty_line_count = 0
                    entry.append(line)
            
            entry_text = "\n".join(entry).strip()
            
            if entry_text:
                reflect_on_entry(entry_text)
            else:
                print("❌ Please write a diary entry first")
                sys.exit(1)
        
        except KeyboardInterrupt:
            print("\n\n❌ Interrupted by user")
            sys.exit(1)
        except EOFError:
            entry_text = "\n".join(entry).strip()
            if entry_text:
                reflect_on_entry(entry_text)
            else:
                print("❌ Please write a diary entry first")
                sys.exit(1)


if __name__ == "__main__":
    main()
