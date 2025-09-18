# Este arquivo define os comandos para interação com o robô NAO.

import time
from nao_connection import NaoConnection

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

class NaoCommands:
    def __init__(self, connection: NaoConnection):
        self.connection = connection
        self.tts = connection.get_service("ALTextToSpeech")
        self.asr = connection.get_service("ALSpeechRecognition")
        self.memory = connection.get_service("ALMemory")
        if self.asr:
            try:
                self.asr.setLanguage("Brazilian")
                self.asr.setParameter("Sensitivity", 0.7)
                self.asr.setParameter("NoiseSuppression", True)
            
            except Exception as e:
                print(f"Erro ao configurar o idioma: {e}")

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

    def start_listening_for_spelling(self, on_letter_spelled, on_final_word):
        """Inicia o reconhecimento de voz para soletrar uma palavra."""
        if not self.asr or not self.memory:
            self.say("Não consigo ouvir você agora.")
            return

        current_spelling = ""
        vocabulary = list(LETTER_MAP.keys()) + ["confirmar", "apagar"]
        
        try:
            self.asr.setVocabulary(vocabulary, False)
            self.asr.subscribe("SpellingGame")
            self.say("Pode começar a soletrar. Diga 'confirmar' quando terminar ou 'apagar' para a última letra.")
            
            self.memory.insertData("WordRecognized", ["", 0])

            while True:
                time.sleep(1)
                value = self.memory.getData("WordRecognized")
                if value and value[0]:
                    word = value[0].lower()
                    confidence = value[1]
                    self.memory.insertData("WordRecognized", ["", 0])

                    if confidence < 0.5:
                        continue

                    if word == "confirmar":
                        on_final_word(current_spelling)
                        break
                    elif word == "apagar":
                        if current_spelling:
                            current_spelling = current_spelling[:-1]
                            on_letter_spelled(current_spelling)
                    elif word in LETTER_MAP:
                        current_spelling += LETTER_MAP[word]
                        on_letter_spelled(current_spelling)
        except Exception as e:
            print(f"Ocorreu um erro durante o reconhecimento de voz: {e}")
            self.say("Desculpe, ocorreu um erro.")
        finally:
            self.asr.unsubscribe("SpellingGame")

    def close(self):
        """Encerra a conexão com o robô."""
        self.connection.close()