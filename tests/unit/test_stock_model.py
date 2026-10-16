from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.modules.quotes.application.dtos.stock_dto import CreateStockDTO
from app.modules.quotes.domain.entities.stock import Stock
from app.modules.quotes.infrastructure.models.stock_model import StockModel


def test_create_stock_payload_persists_and_restores_required_fields():
    dto = CreateStockDTO(
        tool_name="parafuso",
        quantity=43443,
        price=50,
        batch="prd-43443",
        replacement_time_hours=72,
        replacement_time_days=3,
        tool_description="parafuso para m6",
    )
    stock = Stock(
        **dto.model_dump(exclude={"tool_description"}),
        description=dto.tool_description,
    )
    engine = create_engine("sqlite://")
    try:
        StockModel.__table__.create(engine)
        with Session(engine) as session:
            session.add(StockModel.from_entity(stock))
            session.commit()

        with Session(engine) as session:
            model = session.scalars(select(StockModel)).one()
            assert model.price == dto.price
            assert model.batch == dto.batch
            restored = model.to_entity()
            assert restored == stock
    finally:
        engine.dispose()
