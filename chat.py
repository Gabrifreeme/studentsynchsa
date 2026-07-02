from openai import OpenAI

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="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"
)

print("Type your question (type 'exit' to stop):")
while True:
    question = input("You: ")
    if question.lower() == "exit":
        break
    completion = client.chat.completions.create(
        model="deepseek-ai/deepseek-v4-flash",
        messages=[{"role": "user", "content": question}],
        max_tokens=500
    )
    print("AI: " + completion.choices[0].message.content)
    print()