"""
This script contains a Flask web application that uses OpenAI's GPT-4 model to provide customer support.
The application allows users to send messages and files to the AI assistant, which responds with relevant information.
The application also includes a function called getFAQContest that returns FAQ content in response to customer inquiries about products.
"""
from time import sleep
from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import markdown
import os

UPLOAD_FOLDER = './uploads'

app = Flask(__name__)


@app.route('/')
def index():
    """
    Renders the chat.html file with LINE-style design.

    Returns:
        The rendered HTML template.
    """
    return render_template('chat.html')


@app.route('/renew_message', methods=['POST'])
def renew_message():
    
    client = OpenAI()

    # assistantの作成
    assistant = client.beta.assistants.create(
        instructions="""
        あなたはhoge株式会社のカスタマーサポートの優秀なオペレーターです。オペレーターとして、顧客と会話しながら、以下の「問い合わせ情報」を聞き出してまとめてください。
        また、まとめた後に顧客に自身の理解を説明し、「フォーマット」の書き方に沿ってまとめてください。
        また、その内容で正しいかを顧客に確認してもらってください。
        顧客と認識が合うまで会話をしてください。
        顧客への質問は、一度のレスポンスで一つだけにしてください。
        
        ### 問い合わせ情報
        問い合わせの内容：
        　具体的なお問い合わせの内容です。特に、何にお困りなのかを明確にしてください。

        発生した事象：
        　以下のような内容を聞き出してください。
        　・どのような操作をしていたか
        　・どのような事象が発生したのか。
        　・エラーメッセージが表示された場合は、その内容
        　・発生した日時
        　・発生の頻度

        発生した環境：
        　以下のような内容を聞き出してください。
        　・OSの種類、バージョン
        　・ブラウザの種類、バージョン

        ご利用サービス：
        　・管理画面
        　・モバイルアプリ
        　・利用者画面

        いつまでに回答が欲しいか：
        　・解決までの緊急度を判断できるように、この問い合わせをいつまでに解決したいのか確認してください。

        ### フォーマット
        顧客の回答を以下のフォーマットに沿ってまとめてください。
        事象：{あなたがまとめた事象の内容}
        利用環境：{あなたがまとめた利用環境の内容}
        ご利用サービス：{あなたがまとめたご利用サービスの内容}
        いつまでに回答が欲しいか：{あなたがまとめたいつまでに回答が欲しいかの内容}
        発生日時：{あなたがまとめた発生日時の内容}
        緊急度：{あなたがまとめた緊急度の内容}
        """,
        name="オペレーター",
        model="gpt-4-1106-preview",
        tools=[{
            "type": "function",
            "function": {
                "name": "getFAQContest",
                "description": "Return FAQ content in response to customer inquiries about products.",
                "parameters": {
                    "type": "object",
                    "properties": {
                    "product": {"type": "string", "description": "製品名。指定可能なのは一つだけ。選択肢は「アプリ」「管理画面」「顧客画面」の３つ。"},
                    },
                    "required": ["product"]
                }
            }
        }]
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

def getFAQContest(user_input, file_id):
    return "その操作方法は、こちらのページをご覧ください。 https://www.google.com/"


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
        instructions="日本語で回答してください。"
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
        if status == "requires_action":
            break
        sleep(5)
    
    # requires_actionの場合は、actionを実行
    if status == "requires_action":
        function_name = result.required_action.submit_tool_outputs.tool_calls[0].function.name
        call_id = result.required_action.submit_tool_outputs.tool_calls[0].id

        faqContext = None
        if function_name == "getFAQContest":
            faqContext = getFAQContest(user_input, file_id)
        else:
            faqContext = "すみません。よくわかりませんでした。"

        print(faqContext)

        submit_tool_run = client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread.id,
            run_id=run.id,
            tool_outputs=[
                {
                    "tool_call_id": call_id,
                    "output": faqContext
                },
                ]
        )
        print(submit_tool_run)

        # runの状態を確認
        status = "running"
        while status != "completed":
            result = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            print(result)
            status = result.status
            sleep(5)
    
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
