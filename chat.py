from time import sleep
from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import markdown
import os

app = Flask(__name__)

STATUS = ["queued", "in_progress", "completed", "requires_action", "expired", "cancelling", "cancelled", "failed"]
UPLOAD_FOLDER = './uploads'

@app.route('/')
def index():
    return render_template('chat.html')  # LINE風のデザインをしたHTMLファイル

@app.route('/renew_message', methods=['POST'])
def renew_message():
    
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
    # 添付ファイルがある場合は、ファイル名を取得
    file_id = None
    if request.files:
        file = request.files['file']
        filename = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filename)
        # ファイルを送信
        file_id = send_file(filename)
    
    user_input = request.form['message']
    # AIからの応答を取得
    response = get_ai_response(user_input, file_id)
    return jsonify({'message': response})

def send_file(filename):
    client = OpenAI()
    file = open(filename, "rb")
    file_response = client.files.create(
        file=file,
        purpose="assistants"
    )
    print(file_response)
    # ファイルの消去
    os.remove(filename)
    return file_response.id

def get_ai_response(user_input, file_id):
    client = OpenAI()

    assistant_id = request.form['assistant_id']
    client.beta.assistants.retrieve(assistant_id)
    print(assistant_id)

    # threadの作成
    thread = client.beta.threads.create()

    # パラメーターを指定してthreadにメッセージを送信
    message = None
    if file_id == None:
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input
        )
    else:
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input,
            file_ids=[file_id]
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
    last_value = markdown.markdown(last_message.content[0].text.value)


    return last_value

if __name__ == '__main__':
    app.run(debug=True)
