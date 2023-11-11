
from openai import OpenAI
client = OpenAI()

# assistantの作成
assistant = client.beta.assistants.create(
    instructions="You are a personal math tutor. When asked a question, write and run Python code to answer the question.",
    name="Math Tutor",
    tools=[{"type": "code_interpreter"}],
    model="gpt-4",
)
print(assistant)

# threadの作成
thread = client.beta.threads.create()


message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="I need to solve the equation `3x + 11 = 14`. Can you help me?"
)
print(message)

# assistantとthreadのidを指定して実行
run = client.beta.threads.runs.create(
  thread_id=thread.id,
  assistant_id=assistant.id,
  instructions="Please address the user as Jane Doe. The user has a premium account."
)
print(run)

# assistantのidを指定して結果の確認
result = client.beta.threads.runs.retrieve(
  thread_id=thread.id,
  run_id=run.id
)
print(result)

print ("status:" + result.status)

# 
# threadのidを指定してメッセージの確認
messages = client.beta.threads.messages.list(
  thread_id=thread.id
)
print(messages)

# assistantのidを指定して削除
response = client.beta.assistants.delete(assistant.id)
print(response)