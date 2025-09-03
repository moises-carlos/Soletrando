import random
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

def get_words():
    """Carrega as palavras do arquivo words.txt."""
    try:
        with open('words.txt', 'r', encoding='utf-8') as f:
            words = [line.strip() for line in f if line.strip()]
        if not words:
            return ["soletrando", "python"] # Palavras padrão se o arquivo estiver vazio
        return words
    except FileNotFoundError:
        return ["soletrando", "python"] # Palavras padrão se o arquivo não existir

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get-word')
def get_word():
    words = get_words()
    word = random.choice(words)
    response = jsonify({'word': word})
    # Adiciona headers para impedir o cache pelo navegador
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/check-word', methods=['POST'])
def check_word():
    data = request.get_json()
    user_spelling = data.get('spelling', '').lower().replace(' ', '')
    correct_word = data.get('word', '').lower()
    is_correct = user_spelling == correct_word
    return jsonify({'correct': is_correct})

if __name__ == '__main__':
    app.run(debug=True)
