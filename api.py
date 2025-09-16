import customtkinter as ctk
import random
import threading
from nao_connection import NaoConnection
from nao_commands import NaoCommands

NAO_PORT = 9559

class SpellingGameApp(ctk.CTk):
    def __init__(self, words, nao_commands: NaoCommands):
        super().__init__()

        self.words = words
        self.nao = nao_commands
        self.current_word = ""
        self.user_spelling = ""

        self.title("Soletrando com NAO")
        self.geometry("600x400")

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.status_label = ctk.CTkLabel(
            self, 
            text="Clique em 'Nova Palavra' para começar", 
            font=ctk.CTkFont(size=20)
        )
        self.status_label.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10))

        self.spelled_word_frame = ctk.CTkFrame(self, fg_color="transparent", height=100)
        self.spelled_word_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=10, sticky="nsew")
        self.spelled_word_frame.grid_columnconfigure(0, weight=1)

        self.new_word_button = ctk.CTkButton(
            self, text="Nova Palavra", command=self.start_new_round,
            font=ctk.CTkFont(size=16), height=40
        )
        self.new_word_button.grid(row=2, column=0, padx=(20, 10), pady=20, sticky="ew")

        self.spell_button = ctk.CTkButton(
            self, text="Soletrar por Voz", command=self.start_voice_spelling,
            font=ctk.CTkFont(size=16), height=40
        )
        self.spell_button.grid(row=2, column=1, padx=(10, 20), pady=20, sticky="ew")
        self.spell_button.configure(state="disabled")

        if self.nao.connection.session:
            self.nao.say("Olá! Estou pronto para o jogo de soletrar.")
        else:
            self.status_label.configure(
                text="ERRO: Não foi possível conectar ao robô NAO.", 
                text_color="red"
            )
            self.new_word_button.configure(state="disabled")
            self.spell_button.configure(state="disabled")

    def on_closing(self):
        self.nao.close()
        self.destroy()

    def start_new_round(self):
        self.user_spelling = ""
        self.update_spelled_letters()
        self.current_word = random.choice(self.words)
        self.status_label.configure(
            text=f"A palavra é: {self.current_word.upper()}", 
            text_color="white"
        )
        self.nao.say(f"A nova palavra é: {self.current_word}")
        self.spell_button.configure(state="normal")
        self.new_word_button.configure(text="Outra Palavra")

    def start_voice_spelling(self):
        self.spell_button.configure(state="disabled")
        self.new_word_button.configure(state="disabled")
        self.status_label.configure(text="Ouvindo... Soletre a palavra.")
        
        threading.Thread(
            target=self.nao.start_listening_for_spelling,
            args=(self.update_spelling_from_thread, self.check_spelling_from_thread),
            daemon=True
        ).start()

    def update_spelling_from_thread(self, spelling):
        self.user_spelling = spelling
        self.after(0, self.update_spelled_letters)

    def check_spelling_from_thread(self, final_spelling):
        self.user_spelling = final_spelling
        self.after(0, self.finalize_check)

    def finalize_check(self):
        self.update_spelled_letters()
        normalized_spelling = self.user_spelling.lower()
        normalized_word = self.current_word.lower()

        if normalized_spelling == normalized_word:
            self.status_label.configure(
                text="Parabéns, você acertou!", text_color="#2ECC71"
            )
            self.nao.say("Parabéns, você acertou!")
        else:
            self.status_label.configure(
                text=f"Ops! A correta era '{self.current_word.upper()}'", 
                text_color="#E74C3C"
            )
            self.nao.say(f"Que pena, você errou. A palavra correta era {self.current_word}")
        
        self.new_word_button.configure(state="normal")
        self.spell_button.configure(state="disabled")

    def update_spelled_letters(self):
        for widget in self.spelled_word_frame.winfo_children():
            widget.destroy()

        inner_frame = ctk.CTkFrame(self.spelled_word_frame, fg_color="transparent")
        inner_frame.pack()

        if not self.user_spelling:
            placeholder = ctk.CTkLabel(
                inner_frame, text="-", font=ctk.CTkFont(size=30, weight="bold"), text_color="gray"
            )
            placeholder.pack()
        else:
            for letter in self.user_spelling:
                letter_box = ctk.CTkLabel(
                    inner_frame, text=letter.upper(), 
                    font=ctk.CTkFont(size=30, weight="bold"),
                    fg_color="#34495E", corner_radius=5, width=40, height=40
                )
                letter_box.pack(side="left", padx=5)


class IpConfigApp(ctk.CTk):
    """Tela inicial para digitar o IP do robô NAO."""
    def __init__(self, words):
        super().__init__()
        self.words = words
        self.title("Configurar IP do NAO")
        self.geometry("400x200")

        label = ctk.CTkLabel(self, text="Digite o IP do robô NAO:", font=ctk.CTkFont(size=16))
        label.pack(pady=20)

        self.ip_entry = ctk.CTkEntry(self, placeholder_text="Ex: 192.168.1.10", width=250)
        self.ip_entry.pack(pady=10)
        self.ip_entry.focus()

        connect_button = ctk.CTkButton(self, text="Conectar", command=self.start_main_app)
        connect_button.pack(pady=20)
        self.bind("<Return>", lambda event: self.start_main_app())

    def _show_popup(self, title, message):
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        
        popup_width = 350
        popup_height = 150
        popup.geometry(f"{popup_width}x{popup_height}")
        popup.resizable(False, False)

        popup.transient(self)
        popup.grab_set()

        self.update_idletasks()
        parent_x = self.winfo_x()
        parent_y = self.winfo_y()
        parent_width = self.winfo_width()
        parent_height = self.winfo_height()
        x = parent_x + (parent_width - popup_width) // 2
        y = parent_y + (parent_height - popup_height) // 2
        popup.geometry(f"+{x}+{y}")

        main_frame = ctk.CTkFrame(popup, fg_color="transparent")
        main_frame.pack(expand=True, fill="both")
        main_frame.bind("<Button-1>", lambda event: popup.destroy())

        label = ctk.CTkLabel(main_frame, text=message, font=ctk.CTkFont(size=16))
        label.place(relx=0.5, rely=0.4, anchor="center")
        label.bind("<Button-1>", lambda event: popup.destroy())

        ok_button = ctk.CTkButton(main_frame, text="OK", command=popup.destroy, width=100)
        ok_button.place(relx=0.5, rely=0.8, anchor="center")

        popup.wait_window()

    def start_main_app(self):
        ip = self.ip_entry.get().strip()
        if not ip:
            self._show_popup("Erro de Entrada", "O campo de IP não pode estar vazio.")
            return

        connection = NaoConnection(ip=ip, port=NAO_PORT)
        
        if connection.session:
            self._show_popup("Sucesso", "Conexão testada e deu sucesso!")
            commands = NaoCommands(connection)
            self.destroy()
            app = SpellingGameApp(words=self.words, nao_commands=commands)
            app.mainloop()
        else:
            self._show_popup("Erro de Conexão", "Conexão testada e deu erro.")
            connection.close()


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
    IpConfigApp(words=word_list).mainloop()