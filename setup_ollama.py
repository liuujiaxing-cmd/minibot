import os
import subprocess
import time
import requests
import sys

def check_ollama_status():
    """Check if Ollama is running."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=1)
        if response.status_code == 200:
            print("✅ Ollama is running.")
            return True
        else:
            print(f"⚠️ Ollama is responding with status {response.status_code}.")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Ollama is not running (connection refused).")
        return False
    except Exception as e:
        print(f"❌ Error checking Ollama: {e}")
        return False

def pull_model(model_name):
    """Pull the specified model."""
    print(f"📥 Pulling model '{model_name}'... (this might take a while)")
    try:
        # Use subprocess to run 'ollama pull' and show progress
        subprocess.run(["ollama", "pull", model_name], check=True)
        print(f"✅ Model '{model_name}' pulled successfully.")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Failed to pull model '{model_name}'. Is 'ollama' installed in your PATH?")
        return False
    except FileNotFoundError:
        print("❌ 'ollama' command not found. Please install Ollama from https://ollama.com")
        return False

def start_ollama():
    """Attempt to start Ollama."""
    print("🚀 Attempting to start Ollama in the background...")
    try:
        # Start 'ollama serve' in background
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait for it to be ready
        for i in range(10):
            print(f"Waiting for Ollama to start... ({i+1}/10)")
            time.sleep(2)
            if check_ollama_status():
                return True
        
        print("❌ Timed out waiting for Ollama to start.")
        return False
    except FileNotFoundError:
        print("❌ 'ollama' command not found. Please install Ollama from https://ollama.com")
        return False

def main():
    print("Minibot Ollama Setup Tool")
    print("=========================")
    
    # Check if Ollama is running
    is_running = check_ollama_status()
    
    if not is_running:
        print("\nOllama is not running.")
        choice = input("Would you like me to try starting it? (y/n): ").lower().strip()
        if choice == 'y':
            if start_ollama():
                is_running = True
            else:
                print("Failed to start Ollama automatically. Please run 'ollama serve' in a separate terminal.")
                sys.exit(1)
        else:
            print("Please start Ollama manually before running Minibot.")
            sys.exit(0)

    # Check for model
    # Read model from .env if possible, otherwise default
    model_name = "llama3.1" # Default
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("DEFAULT_MODEL="):
                    model_name = line.strip().split("=")[1]
                    break
    
    print(f"\nChecking model '{model_name}'...")
    
    # We can check if model exists by listing tags, but simpler to just try pulling (it's fast if exists)
    # Or check via API
    try:
        response = requests.get("http://localhost:11434/api/tags")
        models = [m['name'] for m in response.json().get('models', [])]
        # Clean model names (e.g. 'llama3.1:latest' -> 'llama3.1')
        found = False
        for m in models:
            if model_name in m:
                found = True
                print(f"✅ Model '{model_name}' found.")
                break
        
        if not found:
            print(f"⚠️ Model '{model_name}' not found locally.")
            choice = input(f"Pull '{model_name}' now? (y/n): ").lower().strip()
            if choice == 'y':
                pull_model(model_name)
            else:
                print("Warning: Minibot might fail if the model is missing.")
    except Exception as e:
        print(f"Error checking models: {e}")

    print("\n✅ Setup complete! You can now run 'python main.py'.")

if __name__ == "__main__":
    main()
