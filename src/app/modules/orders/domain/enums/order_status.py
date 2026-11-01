from enum import StrEnum


class OrderStatus(StrEnum):
    RECEBIDA = "recebida"
    EM_DIAGNOSTICO = "em_diagnostico"
    AGUARDANDO_APROVACAO = "aguardando_aprovacao"
    EM_EXECUCAO = "em_execucao"
    FINALIZADA = "finalizada"
    ENTREGUE = "entregue"
