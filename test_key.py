import os
from openai import OpenAI
from create_ssh_keypair import load_env_file

load_env_file()
api_key = os.environ.get("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

print("Testing OpenAI API key...")
for model_name in ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo", "gpt-luna-6"]:
    try:
        res = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Say hello in 3 words"}],
            max_tokens=10
        )
        print(f"  [SUCCESS] Model '{model_name}' works! Response: {res.choices[0].message.content.strip()}")
        best_model = model_name
        break
    except Exception as e:
        print(f"  [ERROR] Model '{model_name}': {e}")
