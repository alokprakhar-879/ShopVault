from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get("/product/{product_id}", response_model=schemas.ProductReviewsSummary)
def product_reviews(product_id: int, db: Session = Depends(get_db)):
    if not db.get(models.Product, product_id):
        raise HTTPException(status_code=404, detail="Product not found")

    agg = (
        db.query(
            func.avg(models.Review.rating).label("avg_rating"),
            func.count(models.Review.review_id).label("cnt"),
        )
        .filter(models.Review.product_id == product_id)
        .one()
    )

    reviews = (
        db.query(models.Review)
        .options(joinedload(models.Review.customer))
        .filter(models.Review.product_id == product_id)
        .order_by(models.Review.created_at.desc())
        .all()
    )

    return schemas.ProductReviewsSummary(
        product_id=product_id,
        average_rating=round(float(agg.avg_rating), 2) if agg.avg_rating else None,
        review_count=int(agg.cnt or 0),
        reviews=[
            schemas.ReviewOut(
                review_id=r.review_id,
                customer_id=r.customer_id,
                customer_name=r.customer.full_name if r.customer else None,
                product_id=r.product_id,
                rating=r.rating,
                comment=r.comment,
                created_at=r.created_at,
            )
            for r in reviews
        ],
    )


@router.post("", response_model=schemas.ReviewOut, status_code=201)
def create_review(payload: schemas.ReviewCreate, db: Session = Depends(get_db)):
    customer = db.get(models.Customer, payload.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    if not db.get(models.Product, payload.product_id):
        raise HTTPException(status_code=404, detail="Product not found")

    review = models.Review(**payload.model_dump())
    db.add(review)
    db.commit()
    db.refresh(review)
    return schemas.ReviewOut(
        review_id=review.review_id,
        customer_id=review.customer_id,
        customer_name=customer.full_name,
        product_id=review.product_id,
        rating=review.rating,
        comment=review.comment,
        created_at=review.created_at,
    )
