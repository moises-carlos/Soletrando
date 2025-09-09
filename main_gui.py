
import customtkinter as ctk
import random
import threading
from nao_controller import NaoController

# --- CONFIGURAÇÃO DO ROBÔ ---
# Altere para o endereço IP real do seu robô NAO
NAO_IP = "nao.local"
NAO_PORT = 9559
# --------------------------

class SpellingGameApp(ctk.CTk):
    def __init__(self, words, nao_controller):
        super().__init__()

        self.words = words
        self.nao = nao_controller
        self.current_word = ""
        self.user_spelling = ""

        self.title("Soletrando com NAO")
        self.geometry("600x400")

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.status_label = ctk.CTkLabel(self, text="Clique em 'Nova Palavra' para começar", font=ctk.CTkFont(size=20))
        self.status_label.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10))

        self.spelled_word_frame = ctk.CTkFrame(self, fg_color="transparent", height=100)
        self.spelled_word_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=10, sticky="nsew")
        self.spelled_word_frame.grid_columnconfigure(0, weight=1) # Centralizar as letras

        self.new_word_button = ctk.CTkButton(self, text="Nova Palavra", command=self.start_new_round, font=ctk.CTkFont(size=16), height=40)
        self.new_word_button.grid(row=2, column=0, padx=(20, 10), pady=20, sticky="ew")

        self.spell_button = ctk.CTkButton(self, text="Soletrar por Voz", command=self.start_voice_spelling, font=ctk.CTkFont(size=16), height=40)
        self.spell_button.grid(row=2, column=1, padx=(10, 20), pady=20, sticky="ew")
        self.spell_button.configure(state="disabled")

        if self.nao.session:
            self.nao.say("Olá! Estou pronto para o jogo de soletrar.")
        else:
            self.status_label.configure(text="ERRO: Não foi possível conectar ao robô NAO.", text_color="red")

    def on_closing(self):
        self.nao.close()
        self.destroy()

    def start_new_round(self):
        self.user_spelling = ""
        self.update_spelled_letters()
        self.current_word = random.choice(self.words)
        self.status_label.configure(text=f"A palavra é: {self.current_word.upper()}", text_color="white")
        self.nao.say(f"A nova palavra é: {self.current_word}")
        self.spell_button.configure(state="normal")
        self.new_word_button.configure(text="Outra Palavra")

    def start_voice_spelling(self):
        self.spell_button.configure(state="disabled")
        self.new_word_button.configure(state="disabled")
        self.status_label.configure(text="Ouvindo... Soletre a palavra.")
        
        # O reconhecimento de voz do NAO bloqueia, então rodamos em uma thread
        threading.Thread(target=self.nao.start_listening_for_spelling,
                         args=(self.update_spelling_from_thread, self.check_spelling_from_thread),
                         daemon=True).start()

    def update_spelling_from_thread(self, spelling):
        """Callback para atualizar a GUI a partir da thread do NAO."""
        self.user_spelling = spelling
        self.after(0, self.update_spelled_letters)

    def check_spelling_from_thread(self, final_spelling):
        """Callback para verificar a palavra final a partir da thread do NAO."""
        self.user_spelling = final_spelling
        self.after(0, self.finalize_check)

    def finalize_check(self):
        self.update_spelled_letters()
        if self.user_spelling == self.current_word:
            self.status_label.configure(text="Parabéns, você acertou!", text_color="#2ECC71")
            self.nao.say("Parabéns, você acertou!")
        else:
            self.status_label.configure(text=f"Ops! A correta era '{self.current_word.upper()}'", text_color="#E74C3C")
            self.nao.say(f"Que pena, você errou. A palavra correta era {self.current_word}")
        
        self.new_word_button.configure(state="normal")
        self.spell_button.configure(state="disabled")

    def update_spelled_letters(self):
        for widget in self.spelled_word_frame.winfo_children():
            widget.destroy()

        # Frame interno para centralizar as letras
        inner_frame = ctk.CTkFrame(self.spelled_word_frame, fg_color="transparent")
        inner_frame.pack()

        if not self.user_spelling:
            placeholder = ctk.CTkLabel(inner_frame, text="-", font=ctk.CTkFont(size=30, weight="bold"), text_color="gray")
            placeholder.pack()
        else:
            for letter in self.user_spelling:
                letter_box = ctk.CTkLabel(inner_frame, text=letter.upper(), font=ctk.CTkFont(size=30, weight="bold"), fg_color="#34495E", corner_radius=5, width=40, height=40)
                letter_box.pack(side="left", padx=5)

def get_words():
    try:
        with open('words.txt', 'r', encoding='utf-8') as f:
            words = [line.strip() for line in f if line.strip() and len(line.strip()) > 2]
        return words if words else ["soletrando", "python", "robotica"]
    except FileNotFoundError:
        return ["soletrando", "python", "robotica"]

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    word_list = get_words()
    nao = NaoController(ip=NAO_IP, port=NAO_PORT)
    
    app = SpellingGameApp(words=word_list, nao_controller=nao)
    app.mainloop()
