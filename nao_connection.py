import qi
import sys

class NaoConnection:
    def __init__(self, ip, port=9559):
        self.ip = ip
        self.port = port
        self.app = None
        self.session = None
        self.connect()

    def connect(self):
        """Conecta-se ao robô NAO."""
        try:
            connection_url = f"tcp://{self.ip}:{self.port}"
            self.app = qi.Application(["SpellingGame", f"--qi-url={connection_url}"])
            self.app.start()
            self.session = self.app.session
            print(f"Conectado ao NAO em {self.ip}:{self.port}")
        except RuntimeError as e:
            print(f"Erro ao conectar ao NAO: {e}")
            self.app = None
            self.session = None

    def close(self):
        """Encerra a aplicação e a sessão com o NAO."""
        if self.app:
            print("Encerrando conexão com o NAO.")
            self.app.stop()

    def get_service(self, service_name):
        """Retorna um serviço da sessão do NAO se a conexão estiver ativa."""
        if self.session:
            try:
                return self.session.service(service_name)
            except Exception as e:
                print(f"Erro ao obter o serviço '{service_name}': {e}")
        return None