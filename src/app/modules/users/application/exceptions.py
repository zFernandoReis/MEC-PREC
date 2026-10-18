class UserNotFoundError(ValueError):
    def __init__(self):
        super().__init__("Usuário não encontrado")

class VehicleNotFoundError(ValueError):
    def __init__(self):
        super().__init__("Veículo não encontrado")

