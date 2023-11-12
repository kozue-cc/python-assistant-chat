document.getElementById('send-btn').addEventListener('click', function() {
    const inputElement = document.getElementById('chat-input');
    const message = inputElement.value;
    inputElement.value = '';

    const fileInputElement = document.getElementById('file-input');
    const file = fileInputElement.files[0];

    if (message) {
        // メッセージをチャットボックスに追加
        addMessageToChatBox('You', message);

        // サーバーにメッセージを送信し、応答を待つ
        currentAssistantID = localStorage.getItem('current_assistant_id');
        console.log(currentAssistantID);

        //添付ファイルの取得と送信
        const formData = new FormData();
        formData.append('message', message);
        formData.append('assistant_id', currentAssistantID);
        if (file) {
            formData.append('file', file);
        }

        fetch('/send_message', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            addMessageToChatBox('AI', data.message);
        });
    }
});

document.getElementById('renew-btn').addEventListener('click', function() {
    clearChatBox();
    fetch('/renew_message', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        localStorage.setItem('current_assistant_id', data.assistant_id);
        console.log(data.assistant_id);
    })
});

function addMessageToChatBox(sender, message) {
    const chatBox = document.getElementById('chat-box');
    const messageElement = document.createElement('div');
    messageElement.classList.add('message');
    messageElement.textContent = `${sender}: ${message}`;
    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function clearChatBox() {
    const chatBox = document.getElementById('chat-box');
    chatBox.textContent = '';
}
