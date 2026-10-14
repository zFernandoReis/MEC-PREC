class BudgetNotFoundError(ValueError):
    def __init__(self):
        super().__init__("Orçamento não encontrado")

