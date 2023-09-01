from pydantic import BaseModel

class CartItemBase(BaseModel):
    inventory_id: int
    quantity: int
    
class CartItemCreate(CartItemBase):
    pass
    
class CartItemUpdate(BaseModel):
    id: int
    user_id: int