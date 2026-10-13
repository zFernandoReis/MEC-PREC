class UserNotFoundError(ValueError):
    def __init__(self):
        super().__init__("Usuário não encontrado")
