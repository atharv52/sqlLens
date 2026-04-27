from dotenv import load_dotenv
load_dotenv()

from agent.sql_agent import create_agent


def main():
    print("Initializing SQLens agent...")
    agent = create_agent()
    print("Agent ready. Type 'exit' to quit.\n")

    while True:
        try:
            question = input("Ask a question: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if not question:
            continue

        if question.lower() == "exit":
            print("Goodbye.")
            break

        try:
            response = agent.invoke({"input": question})
            print(f"\nAnswer: {response['output']}\n")
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()