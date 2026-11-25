import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/inventory", tags=["Inventory"])

LOW_STOCK_THRESHOLD = int(os.getenv("LOW_STOCK_THRESHOLD", "4"))


@router.get("", response_model=List[schemas.InventoryOut])
def list_inventory(db: Session = Depends(get_db)):
    rows = (
        db.query(models.Inventory)
        .options(joinedload(models.Inventory.product))
        .order_by(models.Inventory.stock_quantity.asc())
        .all()
    )
    return [
        schemas.InventoryOut(
            inventory_id=r.inventory_id,
            product_id=r.product_id,
            product_name=r.product.name if r.product else None,
            stock_quantity=r.stock_quantity,
            reorder_level=r.reorder_level,
            last_updated=r.last_updated,
            is_low_stock=r.stock_quantity <= LOW_STOCK_THRESHOLD,
        )
        for r in rows
    ]


@router.get("/low-stock", response_model=List[schemas.InventoryOut])
def low_stock(db: Session = Depends(get_db)):
    rows = (
        db.query(models.Inventory)
        .options(joinedload(models.Inventory.product))
        .filter(models.Inventory.stock_quantity <= LOW_STOCK_THRESHOLD)
        .order_by(models.Inventory.stock_quantity.asc())
        .all()
    )
    return [
        schemas.InventoryOut(
            inventory_id=r.inventory_id,
            product_id=r.product_id,
            product_name=r.product.name if r.product else None,
            stock_quantity=r.stock_quantity,
            reorder_level=r.reorder_level,
            last_updated=r.last_updated,
            is_low_stock=True,
        )
        for r in rows
    ]


@router.patch("/{product_id}", response_model=schemas.InventoryOut)
def update_inventory(
    product_id: int, payload: schemas.InventoryUpdate, db: Session = Depends(get_db)
):
    inv = (
        db.query(models.Inventory)
        .options(joinedload(models.Inventory.product))
        .filter(models.Inventory.product_id == product_id)
        .first()
    )
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory row not found")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(inv, key, value)
    db.commit()
    db.refresh(inv)
    return schemas.InventoryOut(
        inventory_id=inv.inventory_id,
        product_id=inv.product_id,
        product_name=inv.product.name if inv.product else None,
        stock_quantity=inv.stock_quantity,
        reorder_level=inv.reorder_level,
        last_updated=inv.last_updated,
        is_low_stock=inv.stock_quantity <= LOW_STOCK_THRESHOLD,
    )
