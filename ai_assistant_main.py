"""
Personal Assistant AI Agent
Main entry point for CLI interaction
Uses Ollama for local LLM
"""

import os
import argparse
from dotenv import load_dotenv
from agent import PersonalAssistant

def main():
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Personal Assistant AI Agent')
    parser.add_argument('--model', default='llama3.1', help='Ollama model to use (default: llama3.1)')
    parser.add_argument('--ollama-url', default='http://localhost:11434', help='Ollama API URL')
    args = parser.parse_args()
    
    # Check for required environment variables
    required_vars = ['CLIENT_ID', 'CLIENT_SECRET', 'TENANT_ID']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print("\nCreate a .env file with:")
        print("CLIENT_ID=your_microsoft_client_id")
        print("CLIENT_SECRET=your_microsoft_client_secret")
        print("TENANT_ID=your_microsoft_tenant_id")
        return
    
    print(f"🔧 Initializing with Ollama model: {args.model}")
    assistant = PersonalAssistant(ollama_model=args.model, ollama_url=args.ollama_url)
    
    print("\n🤖 Personal Assistant AI Agent")
    print("=" * 50)
    print("Using local LLM via Ollama")
    print("Commands:")
    print("  - Ask me anything about your emails or tasks")
    print("  - 'exit' or 'quit' to close")
    print("  - 'clear' to clear conversation history")
    print("=" * 50)
    print()
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['exit', 'quit']:
                print("👋 Goodbye!")
                break
            
            if user_input.lower() == 'clear':
                assistant.conversation_history = []
                print("🗑️  Conversation history cleared\n")
                continue
            
            if not user_input:
                continue
            
            print("\n🤔 Thinking...")
            response = assistant.process_request(user_input)
            print(f"\r🤖 Assistant: {response}\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")

if __name__ == "__main__":
    main()
