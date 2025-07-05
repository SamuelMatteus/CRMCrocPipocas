from enum import Enum

class ClassificacaoProduto(Enum):

    PIPOCA = 'Pipoca'
    BEBIDAS = 'Bebidas'
    OUTROS = 'Outros'

class TipoPedido(Enum):
    VENDA_BALCAO = "Retirada"
    PEDIDO_ENTREGA = "Entrega/Delivery"

class ClassificacaoDespesa(Enum):
    CUSTOS_PRODUCAO = "Custos de Produção"
    IMPREVISTOS = "Imprevistos"
    MATERIA_PRIMA = "Matéria Prima"
    DESPESAS_REGULARES = "Despesas Regulares"