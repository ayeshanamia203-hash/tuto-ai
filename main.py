import sys
from ai_brain import ask_ai_tutor

def start_tutor_app():
    print("=" * 60)
    print(" 🚀 Welcome to Your Global AI Educational Tutor! 🚀")
    print("=" * 60)
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            user_input = input("\n📝 Ask your question: ")

            if user_input.strip().lower() in ['exit', 'quit']:
                print("\n👋 Goodbye! Happy Learning!")
                break

            if not user_input.strip():
                print("⚠️ Please enter a valid question.")
                continue

            print("\n🤖 AI Tutor is thinking...")

            response = ask_ai_tutor(user_input)

            print("\n" + "=" * 40)
            print("💡 AI Tutor Response:")
            print("=" * 40)
            print(response)
            print("=" * 40)

        except KeyboardInterrupt:
            print("\n\n👋 App stopped.")
            sys.exit()

if __name__ == "__main__":
    start_tutor_app()

