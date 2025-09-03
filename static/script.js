document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('start-btn');
    const deleteBtn = document.getElementById('delete-btn');
    const status = document.getElementById('status');
    const spelledWordContainer = document.getElementById('spelled-word-container');
    const correctWordDisplay = document.getElementById('correct-word-display');
    const container = document.querySelector('.container');

    let currentWord = '';
    let currentSpelling = '';
    let isSpelling = false;
    let recognition;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const speechSynthesis = window.speechSynthesis;

    if (!SpeechRecognition || !speechSynthesis) {
        status.textContent = 'Seu navegador não suporta as APIs de voz. Tente o Google Chrome.';
        startBtn.disabled = true;
        return;
    }

    const letterMap = {
        'a': 'a', 'á': 'a', 'ah': 'a',
        'bê': 'b', 'be': 'b', 'b': 'b',
        'cê': 'c', 'ce': 'c', 'c': 'c',
        'dê': 'd', 'de': 'd', 'd': 'd',
        'e': 'e', 'é': 'e', 'eh': 'e',
        'efe': 'f', 'éfe': 'f', 'f': 'f',
        'gê': 'g', 'ge': 'g', 'g': 'g',
        'agá': 'h', 'h': 'h',
        'i': 'i', 'í': 'i',
        'jota': 'j', 'j': 'j',
        'cá': 'k', 'ka': 'k', 'k': 'k',
        'ele': 'l', 'éle': 'l', 'l': 'l',
        'eme': 'm', 'éme': 'm', 'm': 'm', 'em': 'm',
        'ene': 'n', 'éne': 'n', 'n': 'n', 'en': 'n',
        'o': 'o', 'ó': 'o', 'oh': 'o',
        'pê': 'p', 'pe': 'p', 'p': 'p',
        'quê': 'q', 'que': 'q', 'q': 'q',
        'erre': 'r', 'érre': 'r', 'r': 'r',
        'esse': 's', 'ésse': 's', 's': 's', 'es': 's', 'és': 's',
        'tê': 't', 'te': 't', 't': 't',
        'u': 'u',
        'vê': 'v', 've': 'v', 'v': 'v',
        'dáblio': 'w', 'dablio': 'w', 'w': 'w',
        'xis': 'x', 'x': 'x', 'chis': 'x',
        'ípsilon': 'y', 'ipsilon': 'y', 'y': 'y',
        'zê': 'z', 'ze': 'z', 'z': 'z',
    };

    function normalizeTranscript(transcript) {
        const word = transcript.toLowerCase().trim();
        if (letterMap[word]) {
            return letterMap[word];
        }
        if (word.length === 1 && /[a-z]/.test(word)) {
            return word;
        }
        return null;
    }

    recognition = new SpeechRecognition();
    recognition.lang = 'pt-BR';
    recognition.continuous = false;
    recognition.interimResults = false;

    startBtn.addEventListener('click', () => {
        if (isSpelling) return; // Previne múltiplos inícios
        startGame();
    });
    deleteBtn.addEventListener('click', deleteLastLetter);

    async function startGame() {
        resetUI();
        status.textContent = 'Pegando uma nova palavra...';
        try {
            const response = await fetch('/get-word');
            const data = await response.json();
            currentWord = data.word;
            speakWord(currentWord);
        } catch (error) {
            status.textContent = 'Erro ao buscar palavra. Tente novamente.';
            console.error('Error fetching word:', error);
        }
    }

    function speakWord(word) {
        status.textContent = 'Ouça a palavra e prepare-se para soletrar.';
        const utterance = new SpeechSynthesisUtterance(`A palavra é: ${word}`);
        utterance.lang = 'pt-BR';
        utterance.rate = 0.9;
        utterance.onend = () => {
            status.textContent = 'Sua vez! Soletre ou diga a palavra final.';
            deleteBtn.classList.remove('hidden');
            isSpelling = true;
            recognition.start();
        };
        speechSynthesis.speak(utterance);
    }

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript.trim().toLowerCase();

        if (transcript.endsWith(currentWord.toLowerCase())) {
            isSpelling = false;
            checkSpelling(currentSpelling);
            return;
        }

        const newlySpelledLetter = normalizeTranscript(transcript);
        if (newlySpelledLetter) {
            currentSpelling += newlySpelledLetter;
            updateSpelledLetters(currentSpelling);
        }
    };

    recognition.onend = () => {
        if (isSpelling) {
            recognition.start();
        }
    };

    recognition.onerror = (event) => {
        if (event.error !== 'no-speech') {
            status.textContent = `Erro no reconhecimento: ${event.error}. Tente novamente.`;
            console.error('Speech recognition error:', event.error);
        }
    };

    function updateSpelledLetters(spelling) {
        spelledWordContainer.innerHTML = '';
        spelling.split('').forEach(letter => {
            const letterBox = document.createElement('div');
            letterBox.className = 'letter-box';
            letterBox.textContent = letter;
            spelledWordContainer.appendChild(letterBox);
        });
    }

    function deleteLastLetter() {
        if (currentSpelling.length > 0) {
            currentSpelling = currentSpelling.slice(0, -1);
            updateSpelledLetters(currentSpelling);
        }
    }

    async function checkSpelling(spelling) {
        isSpelling = false;
        status.textContent = 'Verificando...';
        deleteBtn.classList.add('hidden');
        try {
            const response = await fetch('/check-word', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ spelling: spelling, word: currentWord }),
            });
            const result = await response.json();
            handleResult(result.correct);
        } catch (error) {
            status.textContent = 'Erro ao verificar a palavra.';
            console.error('Error checking word:', error);
        }
    }

    function handleResult(isCorrect) {
        const animationClass = isCorrect ? 'correct-flash' : 'incorrect-flash';
        if (isCorrect) {
            status.textContent = 'Parabéns, você acertou!';
        } else {
            status.textContent = 'Ops, não foi desta vez.';
            correctWordDisplay.textContent = `A palavra correta é: ${currentWord.toUpperCase()}`;
            correctWordDisplay.classList.remove('hidden');
        }
        container.classList.add(animationClass);
        container.addEventListener('animationend', () => {
            container.classList.remove(animationClass);
        }, { once: true });
        startBtn.textContent = 'Jogar Novamente';
        startBtn.disabled = false;
    }

    function resetUI() {
        currentSpelling = '';
        isSpelling = false;
        spelledWordContainer.innerHTML = '';
        correctWordDisplay.classList.add('hidden');
        deleteBtn.classList.add('hidden');
        correctWordDisplay.textContent = '';
        status.textContent = 'Clique no botão para começar';
        startBtn.textContent = 'Começar';
        startBtn.disabled = false;
        container.classList.remove('correct-flash', 'incorrect-flash');
    }
});
