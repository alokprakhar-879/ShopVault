from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# ---------- Categories ----------
class CategoryBase(BaseModel):
    category_name: str
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryOut(CategoryBase):
    category_id: int

    class Config:
        from_attributes = True


# ---------- Products ----------
class ProductBase(BaseModel):
    category_id: int
    name: str
    price: Decimal = Field(ge=0)
    description: Optional[str] = None


class ProductCreate(ProductBase):
    stock_quantity: int = Field(ge=0, default=0)
    reorder_level: int = Field(ge=0, default=5)


class ProductOut(BaseModel):
    product_id: int
    category_id: int
    name: str
    price: Decimal
    description: Optional[str] = None
    created_at: datetime
    stock_quantity: int = 0
    reorder_level: int = 5
    stock_status: str = "out_of_stock"
    stock_badge: str = "Out of Stock"
    average_rating: Optional[float] = None
    review_count: int = 0
    category_name: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- Inventory ----------
class InventoryOut(BaseModel):
    inventory_id: int
    product_id: int
    product_name: Optional[str] = None
    stock_quantity: int
    reorder_level: int
    last_updated: Optional[datetime] = None
    is_low_stock: bool = False

    class Config:
        from_attributes = True


class InventoryUpdate(BaseModel):
    stock_quantity: Optional[int] = Field(default=None, ge=0)
    reorder_level: Optional[int] = Field(default=None, ge=0)


# ---------- Customers ----------
class CustomerCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None


class CustomerOut(BaseModel):
    customer_id: int
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    registered_at: datetime

    class Config:
        from_attributes = True


# ---------- Cart / Checkout ----------
class CartItem(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class CartValidateRequest(BaseModel):
    items: List[CartItem]


class CartValidateIssue(BaseModel):
    product_id: int
    product_name: str
    requested: int
    available: int


class CartValidateResponse(BaseModel):
    valid: bool
    message: Optional[str] = None
    issues: List[CartValidateIssue] = []
    refreshed_items: List[CartItem] = []


class CheckoutRequest(BaseModel):
    customer_id: int
    items: List[CartItem]
    payment_method: str = Field(pattern="^(Credit Card|UPI|PayPal)$")
    simulate_payment_failure: bool = False


# ---------- Orders ----------
class OrderItemOut(BaseModel):
    order_item_id: int
    product_id: int
    product_name: Optional[str] = None
    quantity: int
    unit_price: Decimal

    class Config:
        from_attributes = True


class PaymentOut(BaseModel):
    payment_id: int
    order_id: int
    amount: Decimal
    payment_status: str
    payment_method: str
    transaction_date: datetime

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    order_id: int
    customer_id: int
    order_status: str
    total_amount: Decimal
    order_date: datetime
    status_emoji: str = ""
    can_cancel: bool = False
    items: List[OrderItemOut] = []
    payment: Optional[PaymentOut] = None

    class Config:
        from_attributes = True


class CheckoutResponse(BaseModel):
    success: bool
    message: str
    order: Optional[OrderOut] = None
    cart_issues: List[CartValidateIssue] = []


# ---------- Wishlist ----------
class WishlistCreate(BaseModel):
    customer_id: int
    product_id: int


class WishlistOut(BaseModel):
    wishlist_id: int
    customer_id: int
    product_id: int
    product_name: Optional[str] = None
    price: Optional[Decimal] = None
    stock_quantity: Optional[int] = None
    stock_badge: Optional[str] = None
    added_at: datetime

    class Config:
        from_attributes = True


# ---------- Reviews ----------
class ReviewCreate(BaseModel):
    customer_id: int
    product_id: int
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None


class ReviewOut(BaseModel):
    review_id: int
    customer_id: int
    customer_name: Optional[str] = None
    product_id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ProductReviewsSummary(BaseModel):
    product_id: int
    average_rating: Optional[float] = None
    review_count: int = 0
    reviews: List[ReviewOut] = []


# ---------- Admin ----------
class AdminLoginRequest(BaseModel):
    email: str
    password: str
    access_key: str


class SalesPoint(BaseModel):
    date: str
    revenue: float
    order_count: int


class AdminPaymentOut(BaseModel):
    payment_id: int
    order_id: int
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    amount: Decimal
    payment_status: str
    payment_method: str
    transaction_date: datetime

    class Config:
        from_attributes = True


class AdminDashboard(BaseModel):
    total_revenue: float
    total_orders: int
    pending_orders: int
    low_stock_count: int
    sales_trend: List[SalesPoint]
    low_stock_items: List[InventoryOut]
    all_inventory: List[InventoryOut]
    low_stock_threshold: int
    failed_payments_count: int = 0
    failed_payments: List[AdminPaymentOut] = []
