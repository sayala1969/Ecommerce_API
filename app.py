from sqlalchemy.exc import IntegrityError
from sqlalchemy import ForeignKey, String, Integer, Float, Date
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from marshmallow import ValidationError
from typing import List, Optional
from datetime import date
import os

# Initialize Flask app
app = Flask(__name__)

# #MYSQL database configuration
db_uri =os.getenv('DATABASE_URL')
if not db_uri:
    db_uri = 'mysql+mysqlconnector://root:Corvette92$@localhost/ecommerce_api'

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



#Creating our Base Model
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
db.init_app(app)

#Initialize SQLAlchemy and Marshmallow
ma = Marshmallow(app)


#models
class User(Base):
    __tablename__ = "user_account"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    #One-to-Many relationship from this User to a List of Order Objects
    orders: Mapped[List["Order"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class Order(Base):
    __tablename__ = "orders"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    order_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"), nullable=False)
    # product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    
    # One-to-Many relationship from this Order to a List of User Objects
    user: Mapped["User"] = relationship( back_populates="orders")
    order_products: Mapped[List["OrderProduct"]] = relationship( back_populates="order", cascade="all, delete-orphan")
    
class Product(Base):
    __tablename__ = "products"
    
    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    price: Mapped[float] = mapped_column(Float(10, 2), nullable=False)
    
    # One-to-Many relationship from this Product to a List of Order Objects
    order_products: Mapped[List["OrderProduct"]] = relationship( back_populates="product", cascade="all, delete-orphan")
    
class OrderProduct(Base):
    __tablename__ = "order_products"
    
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), primary_key=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    
    order: Mapped["Order"] = relationship(back_populates="order_products")
    product: Mapped["Product"] = relationship(back_populates="order_products")

    #========== Schemas ==========
    
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User 
        include_fk = True
        load_instance = True
        sqla_session = db.session


class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Order
        include_fk = True
        load_instance = True
        sqla_session = db.session
        
class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product 
        include_fk = True
        load_instance = True
        sqla_session = db.session
        
class OrderProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = OrderProduct
        include_fk = True
        load_instance = True
        sqla_session = db.session

        
user_schema = UserSchema()
users_schema = UserSchema(many=True)

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

order_product_schema = OrderProductSchema()


#========== Endpoints ==========

# ==========================================
# USER ENDPOINTS
# ==========================================
@app.route("/name/<string:username>", methods=["GET"])
def samiam(username):
    return "my name is "+ username

# 1. CREATE User
@app.route("/users", methods=["POST"])
def create_user():
    try:
        new_user = user_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    db.session.add(new_user)
    db.session.commit()
    return user_schema.jsonify(new_user), 201

# 2. READ All Users
@app.route("/users", methods=["GET"])
def get_users():
    users = db.session.scalars(db.select(User)).all()
    return users_schema.jsonify(users), 200

# 3. READ One User
@app.route("/users/<int:id>", methods=["GET"])
def get_user(id):
    user = db.session.get(User, id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    return user_schema.jsonify(user), 200

# 4. UPDATE User
@app.route("/users/<int:id>", methods=["PUT"])
def update_user(id):
    user = db.session.get(User, id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    try:
        # Load partial JSON updates into the existing instance
        updated_user = user_schema.load(request.json, instance=user, partial=True)
    except ValidationError as err:
        return jsonify(err.messages), 400

    db.session.commit()
    return user_schema.jsonify(updated_user), 200

# 5. DELETE User
@app.route("/users/<int:id>", methods=["DELETE"])
def delete_user(id):
    user = db.session.get(User, id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"User {id} deleted successfully"}), 200


# ==========================================
# PRODUCT ENDPOINTS
# ==========================================

# 1. CREATE Product
@app.route("/products", methods=["POST"])
def create_product():
    try:
        new_product = product_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    db.session.add(new_product)
    db.session.commit()
    return product_schema.jsonify(new_product), 201

# 2. READ All Products
@app.route("/products", methods=["GET"])
def get_products():
    products = db.session.scalars(db.select(Product)).all()
    return products_schema.jsonify(products), 200

# 3. READ One Product
@app.route("/products/<int:id>", methods=["GET"])
def get_product(id):
    product = db.session.get(Product, id)
    if not product:
        return jsonify({"message": "Product not found"}), 404
    return product_schema.jsonify(product), 200

# 4. UPDATE Product
@app.route("/products/<int:id>", methods=["PUT"])
def update_product(id):
    product = db.session.get(Product, id)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    try:
        updated_product = product_schema.load(request.json, instance=product, partial=True)
    except ValidationError as err:
        return jsonify(err.messages), 400

    db.session.commit()
    return product_schema.jsonify(updated_product), 200

# 5. DELETE Product
@app.route("/products/<int:id>", methods=["DELETE"])
def delete_product(id):
    product = db.session.get(Product, id)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": f"Product {id} deleted successfully"}), 200


# ==========================================
# ORDER ENDPOINTS
# ==========================================

# 1. CREATE Order
@app.route("/orders", methods=["POST"])
def create_order():
    data = request.get_json(silent=True)
    if not data or "user_id" not in data:
        return jsonify({"message": "Missing required fields: 'user_id'"}), 400
    
    try:
        new_order = order_schema.load(data)
    except ValidationError as err:
        return jsonify(err.messages), 400
    try:
        db.session.add(new_order)
        db.session.commit()
        
    # if user id doesn't exist in the users table
    except IntegrityError as error:
        db.session.rollback()
        return jsonify({"message": getattr(error.orig, 'errno', None)}), 400
    return order_schema.jsonify(new_order), 201

# 2. Add Product to Order (prevent duplicates)
@app.route("/orders/<int:order_id>/add_product/<int:product_id>", methods=["put"])
def add_product_to_order(order_id, product_id):
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"message": "Order not found"}), 404
    
    product =db.session.get(Product, product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404
    
    # Check for duplicates 
    existing_entry = db.session.get(OrderProduct, (order_id, product_id))
    if existing_entry:
        return jsonify({"message": "Product is already in this order"}), 400
    
    new_association = OrderProduct(order_id=order_id, product_id=product_id)
    db.session.add(new_association)
    db.session.commit()
    
    return jsonify({"message": f"Product {product_id} added to Order {order_id}"}), 200

# 3. Remove Product from Order
@app.route("/orders/<int:order_id>/remove_product/<int:product_id>", methods=["DELETE"])
def remove_product_from_order(order_id,product_id):
    order_product = db.session.get(OrderProduct, (order_id, product_id))
    if not order_product:
        return jsonify({"message": "Product not found in this order"}), 404

    db.session.delete(order_product)
    db.session.commit()
    return jsonify({"message": f"Product {product_id} deleted successfully from Order {order_id}"}), 200

# 4. Get all orders for a User
@app.route("/orders/user/<int:user_id>", methods=["GET"])
def get_user_orders(user_id):
    orders = db.session.scalars(
        db.select(Order).where(Order.user_id == user_id)
    ).all()
    return orders_schema.jsonify(orders),200

# 5. Get all Products for an Order
@app.route("/orders/<int:order_id>", methods=["GET"])
def get_order_products(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"message": "Order not found"}), 404
    
    return products_schema.jsonify(order.products), 200


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
    app.run(debug=True)