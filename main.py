from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
import functions
app = FastAPI()

class UserRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    user_type: str


class MenuCreate(BaseModel):
    name: str 
    category: str
    price: int = Field(ge=5, le=500)

class MenuAvailability(BaseModel):
    available: int = Field(ge=0, le=1)

class OrderCreate(BaseModel):
    roll_no: str
    item_id: int = Field(gt=0)
    quantity: int = Field(ge=1, le=5)

USER_TYPES = ["student", "staff"]

def authorize(token, allowed_user_types):
    payload = functions.verify_token(token=token, token_type="access")
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or Expired token")
    if payload["user_type"] not in allowed_user_types:
        raise HTTPException(status_code=403, detail="You do not have permission to do this")
    return payload

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# E1 - Get Menu
@app.get("/menu")
def menu(category:str=None,available:int =None, token=Header(None)):
    authorize(token, ["student", "staff"])
    if category is not None and category not in ["breakfast","meals","snacks","beverages","desserts"]:
        raise HTTPException(status_code=422,detail="Invalid category")
    if available is not None and available not in [0, 1]:
        raise HTTPException(status_code=422,detail="Available must be 0 or 1")
    return functions.get_all_menu_items(category=category,available=available)

 #E2 - Add Menu Item
@app.post("/menu")
def add_menu(menu: MenuCreate, token=Header(None)):
    authorize(token, ["staff"])
    if menu.category not in ["breakfast", "meals", "snacks", "beverages", "desserts"]:
        raise HTTPException(status_code=422, detail="Invalid category")
    item = functions.add_menu_item(name=menu.name,category=menu.category,price=menu.price)
    if item is None:
        raise HTTPException(status_code=400, detail="Item already exists")
    return item

# E3 - Update Menu Availability
@app.patch("/menu/{id}/availability")
def update_availability(id: int, menu: MenuAvailability, token=Header(None)):
    authorize(token, ["staff"])
    result = functions.update_menu_availability(id, menu.available)
    if result is None:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return result

# E4 - Place Order
@app.post("/orders")
def place_order(order: OrderCreate, token=Header(None)):
    authorize(token, ["student"])
    item = functions.get_menu_item(order.item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Menu item not found")
    if item["available"] == 0:
        raise HTTPException(status_code=400, detail="This item is sold out today.")
    orders = functions.get_student_orders(order.roll_no, active=True)
    if len(orders) >= 2:
        raise HTTPException(status_code=400, detail="Student already has 2 active orders")
    return functions.place_order(roll_no=order.roll_no,item_id=order.item_id,quantity=order.quantity)

# E5 - Get One Order
@app.get("/orders/{id}")
def get_order(id: int, token=Header(None)):
    authorize(token, ["student", "staff"])
    result = functions.get_order_by_id(id)
    if result is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return result


# E6 - Get Student's Orders for Today
@app.get("/orders/student/{roll_no}")
def get_student_orders(roll_no: str, token=Header(None)):
    authorize(token, ["student", "staff"])
    return functions.get_student_orders(roll_no)

# E7 - Move Order to Next Status
@app.patch("/orders/{order_id}/next")
def next_order_status(order_id: int, token=Header(None)):
    authorize(token, ["staff"])
    result = functions.move_order_to_next_status(order_id)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Order not found")
    if result == "cannot_change":
        raise HTTPException(status_code=400, detail="Order cannot be changed")
    return result

# E8 - Cancel Order
@app.patch("/orders/{order_id}/cancel")
def cancel_order(order_id: int, token=Header(None)):
    authorize(token, ["student"])
    order = functions.get_order_by_id(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    result = functions.cancel_order(order_id)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Order not found")
    if result == "cannot_cancel":
        raise HTTPException(status_code=400, detail="Order cannot be cancelled")
    return result


# E9 - Get Kitchen Queue
@app.get("/kitchen/queue")
def get_kitchen_queue(token=Header(None)):
    authorize(token, ["staff"])
    return functions.get_kitchen_queue()


# E10 - Get Today's Sales Summary
@app.get("/kitchen/sales")
def get_today_sales(token=Header(None)):
    authorize(token, ["staff"])
    return functions.get_today_sales()

# SAMPLE DATA ENDPOINTS
@app.get("/sample menu")
def menu():
    return functions.menu_items()

@app.get("/sample orders")
def menu():
    return functions.orders()

@app.post("/login")
def login(user: UserRequest):
    token = functions.verify_login(username=user.username,password=user.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    return token

@app.post("/refresh")
def refresh(refresh_token=Header(None)):
    payload = functions.verify_token(token=refresh_token,token_type="refresh")
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or Expired refresh token")
    access_token = functions.create_token(username=payload["username"],user_type=payload["user_type"],token_type="access")
    return {"access_token": access_token}

@app.post("/register")
def register_user(user: RegisterRequest):
    if user.user_type not in USER_TYPES:
        raise HTTPException(status_code=400, detail="User type must be student or staff")
    if functions.register_user(user_name=user.username,password=user.password,user_type=user.user_type):
        return {"message": "User registered successfully"}
    raise HTTPException(status_code=400, detail="User already exists")
