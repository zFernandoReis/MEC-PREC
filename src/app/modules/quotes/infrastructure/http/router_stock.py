from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status

from app.bootstrap.stock import StockUseCases
from app.modules.quotes.application.dtos.stock_dto import CreateStockDTO, UpdateStockDTO
from app.modules.quotes.infrastructure.http.dependencies import get_stock_use_cases
from app.modules.quotes.infrastructure.http.schemas import (
    StockCreateResponse,
    StockReadResponse,
    StockResponse,
)
from app.shared.infrastructure.logging import logger

router = APIRouter(prefix="/stock", tags=["Stock"])
UseCases = Annotated[StockUseCases, Depends(get_stock_use_cases)]
ToolId = Annotated[str, Path(title="Tool ID", description="The ID of the tool in the stock")]


@router.post("", response_model=StockCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_stock(dto: CreateStockDTO, use_cases: UseCases):
    logger.debug("Recebida solicitação HTTP para criar item de estoque.")
    return await use_cases.create_stock.execute(dto)


@router.get("", response_model=list[StockReadResponse])
async def list_stocks(
    use_cases: UseCases,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
):
    logger.debug("Recebida listagem HTTP de item de estoque: offset=%s, limit=%s", offset, limit)
    return await use_cases.list_stocks.execute(offset=offset, limit=limit)


@router.get("/{tool_id}", response_model=StockResponse)
async def get_stock(tool_id: ToolId, use_cases: UseCases):
    logger.debug("Recebida consulta HTTP de item de estoque: tool_id=%s", tool_id)
    return await use_cases.get_stock.execute(tool_id)


@router.patch("/{tool_id}", response_model=StockReadResponse)
async def update_stock(tool_id: ToolId, dto: UpdateStockDTO, use_cases: UseCases):
    logger.debug("Recebida solicitação HTTP para atualizar item de estoque: tool_id=%s", tool_id)
    return await use_cases.update_stock.execute(tool_id, dto)


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stock(tool_id: ToolId, use_cases: UseCases):
    logger.debug("Recebida solicitação HTTP para excluir item de estoque: tool_id=%s", tool_id)
    await use_cases.delete_stock.execute(tool_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
