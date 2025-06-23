from flask import Flask, request, jsonify
import openai
import os
import time

# Pegando a chave da OpenAI da variável de ambiente
openai.api_key = os.environ.get("OPEN_AI_APIKEY")

# ID do seu assistente (criado via https://platform.openai.com/assistants)
ASSISTANT_ID = os.environ.get("OPEN_AI_ASSISTANTID")

app = Flask(__name__)

@app.route("/responder", methods=["POST"])
def responder():
    data = request.json
    numero = data.get("numero")
    mensagem = data.get("mensagem")
    thread_id = data.get("thread_id")  # ← recebido do Make, se houver

    if not numero or not mensagem:
        return jsonify({"erro": "Faltando número ou mensagem"}), 400

    # Se não enviaram uma thread, cria nova
    if not thread_id:
        thread = openai.beta.threads.create()
        thread_id = thread.id

    # Adiciona mensagem à thread
    openai.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=mensagem
    )

    # Executa o assistente
    run = openai.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=ASSISTANT_ID
    )

    # Espera terminar
    while True:
        run_status = openai.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        if run_status.status == "completed":
            break
        time.sleep(1)

    # Responde
    messages = openai.beta.threads.messages.list(thread_id=thread_id)
    resposta = messages.data[0].content[0].text.value

    return jsonify({
        "resposta": resposta,
        "thread_id": thread_id  # ← retorna para você guardar no Make
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
