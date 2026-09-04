"""Deriv bot API. Planning and backtesting are available; live orders stay gated."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..deriv.service import DerivBotService, DerivRequest, DerivStrategy, DerivMode
from ..deriv.backtest import run_deriv_backtest
from ..models.deriv_bot_run import DerivBotRun

router = APIRouter()
service = DerivBotService()


class PricePayload(BaseModel):
    prices: list[float] = Field(min_length=20)
    request: DerivRequest = Field(default_factory=DerivRequest)
    daily_loss: float = Field(default=0, ge=0)
    losses: int = Field(default=0, ge=0)


class BacktestPayload(BaseModel):
    prices: list[float] = Field(min_length=21)
    request: DerivRequest = Field(default_factory=DerivRequest)
    initial_balance: float | None = Field(default=None, gt=0)


@router.get("/strategies")
async def strategies() -> dict[str, list[str]]:
    return {"strategies": [strategy.value for strategy in DerivStrategy]}


@router.get("/availability")
async def availability() -> dict:
    return {
        "source": "Deriv availability must be queried from the authenticated proposal/contract API",
        "modes": [mode.value for mode in DerivMode],
        "products": ["digital_option", "turbo", "multiplier", "cfd", "synthetic", "accumulator", "vanilla"],
        "execution": "planning_only_until_authenticated_websocket_executor_is configured",
    }


@router.post("/plan")
async def create_plan(payload: PricePayload, db: Session = Depends(get_db)) -> dict:
    try:
        result = service.plan(payload.request, payload.prices, payload.daily_loss, payload.losses)
        db.add(DerivBotRun(
            symbol=payload.request.symbol,
            mode=payload.request.mode.value,
            strategy=result["strategy"].value,
            run_type="plan",
            confidence=result["analysis"]["confidence"],
            allowed=int(result["risk"]["allowed"]),
            request=payload.request.model_dump(mode="json"),
            result=result,
        ))
        db.commit()
        return result
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/backtest")
async def backtest(payload: BacktestPayload, db: Session = Depends(get_db)) -> dict:
    try:
        result = run_deriv_backtest(payload.request, payload.prices, payload.initial_balance)
        db.add(DerivBotRun(
            symbol=payload.request.symbol,
            mode=payload.request.mode.value,
            strategy=result["strategy"],
            run_type="backtest",
            confidence=None,
            allowed=1,
            request=payload.request.model_dump(mode="json"),
            result=result,
        ))
        db.commit()
        return result
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/runs")
async def runs(limit: int = 20, db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(DerivBotRun).order_by(DerivBotRun.created_at.desc()).limit(min(limit, 100)).all()
    return [{"id": row.id, "symbol": row.symbol, "mode": row.mode, "run_type": row.run_type,
             "strategy": row.strategy, "confidence": row.confidence, "allowed": bool(row.allowed),
             "created_at": row.created_at} for row in rows]