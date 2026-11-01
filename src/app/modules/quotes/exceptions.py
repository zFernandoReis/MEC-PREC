class BudgetNotFoundError(ValueError):
    def __init__(self):
        super().__init__("Orçamento não encontrado")

class StockNotFoundError(ValueError):
    def __init__(self):
        super().__init__("Peça não encontrada")


