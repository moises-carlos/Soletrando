
import qi
import sys
import time

LETTER_MAP = {
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
}

class NaoController:
    def __init__(self, ip="nao.local", port=9559):
        self.ip = ip
        self.port = port
        self.session = None
        self.tts = None
        self.asr = None
        self.memory = None
        self.connect()

    def connect(self):
        """Conecta-se ao robô NAO."""
        try:
            connection_url = f"tcp://{self.ip}:{self.port}"
            self.session = qi.Application(["SpellingGame", f"--qi-url={connection_url}"])
            self.session.start()
            print(f"Conectado ao NAO em {self.ip}:{self.port}")

            self.tts = self.session.service("ALTextToSpeech")
            self.asr = self.session.service("ALSpeechRecognition")
            self.memory = self.session.service("ALMemory")
            self.asr.setLanguage("Brazilian")
        except RuntimeError as e:
            print(f"Erro ao conectar ao NAO: {e}")
            print("Verifique o endereço IP e se o robô está acessível.")
            print("Certifique-se de que a biblioteca 'naoqi' está instalada.")
            self.session = None

    def say(self, text):
        """Faz o robô NAO falar um texto."""
        if self.tts:
            try:
                self.tts.setLanguage("Brazilian")
                self.tts.say(str(text))
            except Exception as e:
                print(f"Erro ao tentar fazer o NAO falar: {e}")
        else:
            print(f"[SIMULAÇÃO] NAO diria: {text}")

    def listen_for_spelling(self, on_letter_spelled, on_final_word):
        """Inicia o reconhecimento de voz para soletrar uma palavra."""
        if not self.asr:
            self.say("Não consigo ouvir você agora.")
            return

        vocabulary = list(LETTER_MAP.keys()) + ["confirmar", "apagar"]
        self.asr.setVocabulary(vocabulary, False)
        
        self.say("Pode começar a soletrar. Diga 'confirmar' quando terminar ou 'apagar' para remover a última letra.")

        spelled_word = ""
        self.word_recognized_subscriber = self.memory.subscriber("WordRecognized")
        self.word_recognized_signal = self.word_recognized_subscriber.signal.connect(lambda words: self._on_word_recognized(words, on_letter_spelled, on_final_word))

    def _on_word_recognized(self, words, on_letter_spelled, on_final_word):
        """Callback interno para o evento de reconhecimento de palavra."""
        recognized_word = words[0].lower()
        confidence = words[1]

        if confidence < 0.3:
            return

        if recognized_word == "confirmar":
            self.stop_listening()
            on_final_word(self.current_spelling)
        elif recognized_word == "apagar":
            if len(self.current_spelling) > 0:
                self.current_spelling = self.current_spelling[:-1]
                on_letter_spelled(self.current_spelling)
        elif recognized_word in LETTER_MAP:
            letter = LETTER_MAP[recognized_word]
            self.current_spelling += letter
            on_letter_spelled(self.current_spelling)

    def start_listening_for_spelling(self, on_letter_spelled, on_final_word):
        if not self.asr:
            self.say("Não consigo te ouvir.")
            return

        self.current_spelling = ""
        vocabulary = list(LETTER_MAP.keys()) + ["confirmar", "apagar"]
        self.asr.setVocabulary(vocabulary, False)
        self.asr.subscribe("SpellingGame")
        self.say("Pode começar a soletrar. Diga 'confirmar' quando terminar.")
        
        while True:
            time.sleep(1)
            value = self.memory.getData("WordRecognized")
            if value and value[0]:
                word = value[0]
                confidence = value[1]
                self.memory.removeData("WordRecognized")

                if confidence < 0.3:
                    continue

                if word == "confirmar":
                    on_final_word(self.current_spelling)
                    break
                elif word == "apagar":
                    if self.current_spelling:
                        self.current_spelling = self.current_spelling[:-1]
                        on_letter_spelled(self.current_spelling)
                elif word in LETTER_MAP:
                    self.current_spelling += LETTER_MAP[word]
                    on_letter_spelled(self.current_spelling)

        self.asr.unsubscribe("SpellingGame")

    def stop_listening(self):
        """Para o reconhecimento de voz."""
        if self.asr and self.word_recognized_subscriber:
            self.word_recognized_signal.disconnect()
            self.word_recognized_subscriber = None
            print("NAO parou de ouvir.")

    def close(self):
        """Encerra a sessão com o NAO."""
        if self.session:
            self.stop_listening()
            self.session.stop()
            print("Conexão com o NAO encerrada.")


if __name__ == "__main__":
    NAO_IP = "nao.local"
    
    controller = NaoController(ip=NAO_IP)

    if controller.asr:
        def print_letter(spelling):
            print(f"Soletrando até agora: {spelling}")

        def final_word(spelling):
            print(f"Palavra final soletrada: {spelling}")


        import threading
        thread = threading.Thread(target=controller.start_listening_for_spelling, args=(print_letter, final_word))
        thread.start()

        try:
            while thread.is_alive():
                time.sleep(1)
        except KeyboardInterrupt:
            controller.stop_listening()

        controller.close()
    else:
        print("Não foi possível conectar ao robô para o teste.")
