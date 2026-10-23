class OrderNotFoundError(ValueError):
    def __init__(self):
        super().__init__("Ordem de serviço não encontrada")


