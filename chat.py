from time import sleep
from flask import Flask, render_template, request, jsonify
import openai

app = Flask(__name__)

STATUS = ["queued", "in_progress", "completed", "requires_action", "expired", "cancelling", "cancelled", "failed"]

@app.route('/')
def index():
    return render_template('chat.html')  # LINE風のデザインをしたHTMLファイル

@app.route('/renew_message', methods=['POST'])
def renew_message():
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

    return jsonify({'message': 'renewed', 'assistant_id': assistant.id})
    

@app.route('/send_message', methods=['POST'])
def send_message():
    user_input = request.form['message']
    # AIからの応答を取得
    response = get_ai_response(user_input)
    return jsonify({'message': response})

def get_ai_response(user_input):
    from openai import OpenAI
    client = OpenAI()

    assistant_id = request.form['assistant_id']
    client.beta.assistants.retrieve(assistant_id)
    print(assistant_id)

    # threadの作成
    thread = client.beta.threads.create()

    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_input
    )
    print(message)

    # assistantとthreadのidを指定して実行
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id,
        instructions="Please address the user as Mr.Tree. The user has a premium account."
    )
    print(run)

    # assistantのidを指定して結果の確認
    status = "running"
    while status != "completed":
        result = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        print(result)
        status = result.status
        sleep(1)

    print(result)
    
    messages = client.beta.threads.messages.list(
        thread_id=thread.id
    )
    print(messages)

    # responseオブジェクトからdata属性にアクセス
    data = messages.data

    # dataリストの最後の要素を取得
    last_message = data[0]

    # last_messageから必要な情報を取得
    last_value = last_message.content[0].text.value


    return last_value

if __name__ == '__main__':
    app.run(debug=True)
