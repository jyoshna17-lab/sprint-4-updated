from sqlalchemy import Integer, String, Column, create_engine, DateTime, ForeignKey 
from sqlalchemy.orm import Session, declarative_base 
from datetime import datetime, timedelta, timezone
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()
 
DB_PATH = "canteen-preorder.db" 
engine = create_engine(f"sqlite:///{DB_PATH}") 
Base = declarative_base() 

ACCESS_TOKEN_EXPIRY = 15  # minutes
REFRESH_TOKEN_EXPIRY = 7*24*60
SECRET_kEY = "SECRET123"
ALGORITHM = "HS256"
 
class MenuItem(Base): 
    __tablename__ = "menu_items" 
    id = Column(Integer, primary_key=True) 
    name = Column(String) 
    category = Column(String) 
    price = Column(Integer) 
    available = Column(Integer, default=1) 
 
 
class Order(Base): 
    __tablename__ = "orders" 
    id = Column(Integer, primary_key=True) 
    roll_no = Column(String) 
    item_id = Column(Integer, ForeignKey("menu_items.id")) 
    quantity = Column(Integer) 
    status = Column(String, default="placed") 
    ordered_at = Column(DateTime, default=datetime.now) 
    collected_at = Column(DateTime, nullable=True) 

class User(Base):
    __tablename__ = "Users"

    user_id = Column(Integer, primary_key=True)
    user_name = Column(String)
    password = Column(String)
    user_type = Column(String, default="student")
    

Base.metadata.create_all(engine) 
 
def menu_items(): 
    session = Session(engine) 
    menu = [ 
        MenuItem(name="Idli", category="breakfast", price=30, available=1), 
        MenuItem(name="Dosa", category="breakfast", price=40, available=1), 
        MenuItem(name="Puri", category="breakfast", price=35, available=1), 
        MenuItem(name="Veg Meals", category="meals", price=80, available=1), 
        MenuItem(name="Fried Rice", category="meals", price=90, available=1), 
        MenuItem(name="Samosa", category="snacks", price=15, available=1), 
        MenuItem(name="Sandwich", category="snacks", price=50, available=0), 
        MenuItem(name="Burger", category="snacks", price=70, available=1), 
        MenuItem(name="Tea", category="beverages", price=10, available=1), 
        MenuItem(name="Coffee", category="beverages", price=20, available=0), 
        MenuItem(name="Ice Cream", category="desserts", price=40, available=1), 
        MenuItem(name="Gulab Jamun", category="desserts", price=30, available=1) 
    ] 
    items = session.query(MenuItem).all()
    if len(items) == 0:
        session.add_all(menu)
        session.commit()
    session.close()
    return menu
    
def orders(): 
    session = Session(engine) 
    order = [ 
        Order(roll_no="1", item_id=1, quantity=2, status="placed", ordered_at=datetime.now()), 
        Order(roll_no="2", item_id=2, quantity=1, status="placed", ordered_at=datetime.now()), 
        Order(roll_no="3", item_id=4, quantity=1, status="preparing", ordered_at=datetime.now()), 
        Order(roll_no="4", item_id=5, quantity=2, status="preparing", ordered_at=datetime.now()), 
        Order(roll_no="5", item_id=6, quantity=3, status="ready", ordered_at=datetime.now()), 
        Order(roll_no="6", item_id=8, quantity=1, status="collected", ordered_at=datetime.now(), collected_at=datetime.now()), 
        Order(roll_no="7", item_id=9, quantity=2, status="collected", ordered_at=datetime.now(), collected_at=datetime.now()), 
        Order(roll_no="8", item_id=11, quantity=1, status="cancelled", ordered_at=datetime.now()) 
    ] 
    items = session.query(Order).all()
    if len(items) == 0:
        session.add_all(order)
        session.commit() 
    session.close() 
    return order 


def get_all_menu_items(category=None, available=None):
    menu_items()
    session = Session(engine)
    items = session.query(MenuItem)
    if category:
        items = items.filter(MenuItem.category == category)
    if available is not None:
        items = items.filter(MenuItem.available == available)
    items = items.all()
    response = []
    for item in items:
        temp_item = {
            "id": item.id,
            "name": item.name,
            "category": item.category,
            "price": item.price,
            "available": item.available
        }
        response.append(temp_item)
    session.close()
    return response

def get_menu_item(item_id):
    session = Session(engine)
    item = session.get(MenuItem, item_id)
    if item is None:
        session.close()
        return None
    response = {
        "id": item.id,
        "name": item.name,
        "available": item.available
    }
    session.close()
    return response

def add_menu_item(name, category, price):
    session = Session(engine)
    item = session.query(MenuItem).filter(MenuItem.name == name).first()
    if item is not None:
        session.close()
        return None
    item = MenuItem(name=name, category=category, price=price, available=1)
    session.add(item)
    session.commit()
    response = {
        "id": item.id,
        "name": item.name,
        "category": item.category,
        "price": item.price,
        "available": item.available
    }
    session.close()
    return response

def update_menu_availability(id, available):
    session = Session(engine)
    item = session.get(MenuItem, id)
    if item is None:
        session.close()
        return None
    item.available = available
    response = {
        "id": item.id,
        "name": item.name,
        "category": item.category,
        "price": item.price,
        "available": item.available
    }
    session.commit()
    session.close()
    return response

def place_order(roll_no, item_id, quantity):
    session = Session(engine)
    order = Order(roll_no=roll_no,item_id=item_id,quantity=quantity,status="placed")
    session.add(order)
    session.commit()

    response = {
        "id": order.id,
        "roll_no": order.roll_no,
        "item_id": order.item_id,
        "quantity": order.quantity,
        "status": order.status,
        "ordered_at": order.ordered_at
    }
    session.close()
    return response

def get_order_by_id(id):
    session = Session(engine)
    order = session.get(Order, id)
    if order is None:
        session.close()
        return None
    item = session.get(MenuItem, order.item_id)
    response = {
        "id": order.id,
        "roll_no": order.roll_no,
        "item_id": order.item_id,
        "item_name": item.name,
        "quantity": order.quantity,
        "price": item.price,
        "total_price": item.price * order.quantity,
        "status": order.status,
        "ordered_at": order.ordered_at,
        "collected_at": order.collected_at
    }
    session.close()
    return response


def get_student_orders(roll_no, active=False):
    session = Session(engine)
    orders = session.query(Order).filter(Order.roll_no == roll_no).order_by(Order.ordered_at.desc()).all()
    response = []
    for order in orders:
        if order.ordered_at.strftime("%d-%m-%Y") == datetime.now().strftime("%d-%m-%Y"):
            if active == False or (order.status != "collected" and order.status != "cancelled"):
                item = session.get(MenuItem, order.item_id)
                if item is not None:
                    item_name = item.name
                    total_price = item.price * order.quantity
                else:
                    item_name = None
                    total_price = None
                response.append({
                    "id": order.id,
                    "roll_no": order.roll_no,
                    "item_id": order.item_id,
                    "item_name": item_name,
                    "quantity": order.quantity,
                    "total_price": total_price,
                    "status": order.status,
                    "ordered_at": order.ordered_at.strftime("%d-%m-%Y %H:%M:%S"),
                    "collected_at": order.collected_at
                })
    session.close()
    return response


def move_order_to_next_status(order_id):
    next_status = {
        "placed": "preparing",
        "preparing": "ready",
        "ready": "collected"
    }
    session = Session(engine)
    order = session.get(Order, order_id)
    if order is None:
        session.close()
        return "not_found"
    if order.status not in next_status:
        session.close()
        return "cannot_change"
    order.status = next_status[order.status]
    if order.status == "collected":
        order.collected_at = datetime.now()
    session.commit()
    response = {
        "message": "Order status updated successfully",
        "order_id": order.id,
        "status": order.status,
        "collected_at": order.collected_at
    }
    session.close()
    return response


def cancel_order(order_id):
    session = Session(engine)
    order = session.get(Order, order_id)
    if order is None:
        session.close()
        return "not_found"
    if order.status != "placed":
        session.close()
        return "cannot_cancel"
    order.status = "cancelled"
    session.commit()
    response = {
        "message": "Order cancelled successfully",
        "order_id": order.id,
        "status": order.status
    }
    session.close()
    return response


def get_kitchen_queue():
    session = Session(engine)
    orders = session.query(Order).order_by(Order.ordered_at).all()
    response = []
    for order in orders:
        if order.ordered_at.strftime("%d-%m-%Y") == datetime.now().strftime("%d-%m-%Y"):
            if order.status == "placed" or order.status == "preparing" or order.status == "ready":
                item = session.get(MenuItem, order.item_id)
                if item is not None:
                    item_name = item.name
                else:
                    item_name = None
                response.append({
                    "id": order.id,
                    "roll_no": order.roll_no,
                    "item_id": order.item_id,
                    "item_name": item_name,
                    "quantity": order.quantity,
                    "status": order.status,
                    "ordered_at": order.ordered_at.strftime("%d-%m-%Y %H:%M:%S")
                })
    session.close()
    return response

def get_today_sales():
    session = Session(engine)
    orders = session.query(Order).all()

    total_orders = 0
    total_quantity = 0
    total_sales = 0

    for order in orders:
        if order.status == "collected":
            if order.collected_at is not None:
                if order.collected_at.strftime("%d-%m-%Y") == datetime.now().strftime("%d-%m-%Y"):

                    item = session.get(MenuItem, order.item_id)
                    if item is not None:
                        total_orders = total_orders + 1
                        total_quantity = total_quantity + order.quantity
                        total_sales = total_sales + (item.price * order.quantity)

    response = {
        "total_orders": total_orders,
        "total_quantity": total_quantity,
        "total_sales": total_sales
    }
    session.close()
    return response


def create_token(username, user_type, token_type):
    time = ACCESS_TOKEN_EXPIRY
    if token_type == "refresh":
        time = REFRESH_TOKEN_EXPIRY
    payload = {
        "username": username,
        "user_type": user_type,
        "token_type": token_type,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=time)
    }
    token = jwt.encode(payload=payload, key=SECRET_kEY, algorithm=ALGORITHM)
    return token

def verify_token(token, token_type):
    try: 
        payload = jwt.decode(jwt=token,key=SECRET_kEY,algorithms=[ALGORITHM])
    except:
        return False
    if payload["token_type"] == token_type:
        return payload
    return False

def register_user(user_name:str, password:str, user_type:str):
    session = Session(engine)
    user_exists = session.query(User).filter_by(user_name=user_name).first()
    if user_exists is  not None :
        session.close()
        return False
    session.add(User(user_name=user_name,password=ph.hash(password),user_type=user_type))
    session.commit()
    session.close()
    return True

def verify_login(username,password):
    session = Session(engine)
    user = session.query(User).filter_by(user_name = username).first()
    if user is None:
        session.close()
        return False
    try:
        ph.verify(user.password, password)
    except VerifyMismatchError:
        session.close()
        return False
    user_type = user.user_type
    session.close()

    access_token = create_token(username=username,user_type=user_type,token_type="access")
    refresh_token = create_token(username=username,user_type=user_type,token_type="refresh")
    return {"access_token":access_token, "refresh_token": refresh_token}