from ollama import chat

def test_chat():
  
    stream = chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': 'Why is the sky blue?'}],
        stream=True,
    )

    for chunk in stream:
        print(chunk['message']['content'], end='', flush=True)


if __name__ == "__main__":
    test_chat()