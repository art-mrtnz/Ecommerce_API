from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from marshmallow import fields, validate
from datetime import datetime, timedelta
import bcrypt
import math

# Create Flask app instance
app = Flask(__name__)

# Configure SQLAlchemy Database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:Mrtnz81!@localhost/ecommerce_api'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking to save resources

# JWT Configuration
app.config['JWT_SECRET_KEY'] = 'your-secret-key-change-this-in-production'  # ⚠️ CHANGE THIS IN PRODUCTION!
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize SQLAlchemy, Marshmallow, and JWT
db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)

# ================================
# DATABASE MODELS
# ================================

# User Model
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with Orders (One-to-Many)
    orders = db.relationship('Order', backref='user', lazy=True, cascade="all, delete-orphan")
    
    def set_password(self, password):
        """Hash and set the password"""
        password_bytes = password.encode('utf-8')
        self.password_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """Check if the provided password matches the hash"""
        password_bytes = password.encode('utf-8')
        hash_bytes = self.password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    
    def __repr__(self):
        return f'<User {self.name}>'

# Product Model
class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    def __repr__(self):
        return f'<Product {self.product_name}>'

# Order_Product Association Table (Many-to-Many with no duplicates)
order_product = db.Table('order_product',
    db.Column('order_id', db.Integer, db.ForeignKey('orders.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key=True),
    # The combination of order_id and product_id is the primary key, preventing duplicates
)

# Order Model
class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, shipped, delivered, cancelled
    total_amount = db.Column(db.Float, default=0.0)
    shipping_address = db.Column(db.String(500))
    notes = db.Column(db.Text)
    
    # Many-to-Many relationship with Products
    products = db.relationship('Product', secondary=order_product, lazy='subquery',
                             backref=db.backref('orders', lazy=True))
    
    def calculate_total(self):
        """Calculate total amount for the order"""
        self.total_amount = sum(product.price for product in self.products)
        return self.total_amount
    
    def __repr__(self):
        return f'<Order {self.id} - User {self.user_id} - Status: {self.status}>'

# ================================
# MARSHMALLOW SCHEMAS
# ================================

# User Schema
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        include_fk = True
        exclude = ['password_hash']  # Never expose password hash
    
    # Field validation
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    address = fields.String(required=True, validate=validate.Length(min=1, max=255))
    email = fields.Email(required=True, validate=validate.Length(min=1, max=120))
    password = fields.String(required=True, validate=validate.Length(min=6), load_only=True)

# User Login Schema
class UserLoginSchema(ma.Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True)

# Product Schema
class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product
        load_instance = True
        include_fk = True
    
    # Field validation
    product_name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    price = fields.Float(required=True, validate=validate.Range(min=0.01))

# Order Schema
class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Order
        load_instance = True
        include_relationships = True
        include_fk = True  # This ensures user_id is included in the schema
    
    # Field validation
    user_id = fields.Integer(required=True, validate=validate.Range(min=1))
    order_date = fields.DateTime(dump_only=True)  # Auto-generated, not for input
    status = fields.String(validate=validate.OneOf(['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']))
    total_amount = fields.Float(dump_only=True)
    shipping_address = fields.String(validate=validate.Length(max=500))
    notes = fields.String()
    
    # Nested relationships
    products = ma.Nested(ProductSchema, many=True, dump_only=True)

# Initialize schemas
user_schema = UserSchema()
users_schema = UserSchema(many=True)
user_login_schema = UserLoginSchema()
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

# ================================
# HELPER FUNCTIONS
# ================================

def get_current_user_id():
    """Get current user ID from JWT token and convert to integer"""
    return int(get_jwt_identity())

def paginate_query(query, page, per_page, error_out=False):
    """Paginate a SQLAlchemy query"""
    items = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=error_out
    )
    
    return {
        'items': items.items,
        'total': items.total,
        'pages': items.pages,
        'page': page,
        'per_page': per_page,
        'has_next': items.has_next,
        'has_prev': items.has_prev,
        'next_page': items.next_num if items.has_next else None,
        'prev_page': items.prev_num if items.has_prev else None
    }

# ================================
# API ROUTES
# ================================

# Basic route for testing
@app.route('/')
def home():
    return jsonify({
        "message": "Welcome to the E-commerce API!",
        "version": "2.0 - Enhanced with JWT Authentication, Pagination & Advanced Order Management",
        "endpoints": {
            "authentication": {
                "register": "POST /auth/register",
                "login": "POST /auth/login",
                "profile": "GET /auth/profile (JWT Required)"
            },
            "users": {
                "get_all": "GET /users (JWT Required, Paginated)",
                "get_by_id": "GET /users/<id> (JWT Required)",
                "create": "POST /users",
                "update": "PUT /users/<id> (JWT Required)",
                "delete": "DELETE /users/<id> (JWT Required)"
            },
            "products": {
                "get_all": "GET /products (Paginated)",
                "get_by_id": "GET /products/<id>",
                "create": "POST /products (JWT Required)",
                "update": "PUT /products/<id> (JWT Required)",
                "delete": "DELETE /products/<id> (JWT Required)"
            },
            "orders": {
                "create": "POST /orders (JWT Required)",
                "get_all": "GET /orders (JWT Required, Paginated)",
                "get_by_id": "GET /orders/<id> (JWT Required)",
                "update_status": "PUT /orders/<id>/status (JWT Required)",
                "add_product": "PUT /orders/<order_id>/add_product/<product_id> (JWT Required)",
                "remove_product": "DELETE /orders/<order_id>/remove_product/<product_id> (JWT Required)",
                "get_user_orders": "GET /orders/user/<user_id> (JWT Required, Paginated)",
                "get_order_products": "GET /orders/<order_id>/products (JWT Required)",
                "cancel_order": "PUT /orders/<id>/cancel (JWT Required)",
                "get_orders_by_status": "GET /orders/status/<status> (JWT Required, Paginated)"
            }
        }
    })

# ================================
# AUTHENTICATION ENDPOINTS
# ================================

# Register a new user
@app.route('/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({'error': 'Email already exists'}), 400
        
        new_user = User(
            name=data['name'],
            address=data['address'],
            email=data['email']
        )
        
        # Set password
        new_user.set_password(data['password'])
        
        db.session.add(new_user)
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(identity=str(new_user.id))
        
        return jsonify({
            'message': 'User registered successfully',
            'access_token': access_token,
            'user': user_schema.dump(new_user)
        }), 201
        
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Login user
@app.route('/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        user = User.query.filter_by(email=data['email']).first()
        
        if user and user.check_password(data['password']):
            access_token = create_access_token(identity=str(user.id))
            return jsonify({
                'message': 'Login successful',
                'access_token': access_token,
                'user': user_schema.dump(user)
            }), 200
        else:
            return jsonify({'error': 'Invalid email or password'}), 401
            
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get current user profile
@app.route('/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    current_user_id = get_current_user_id()
    user = User.query.get_or_404(current_user_id)
    return user_schema.jsonify(user)

# ================================
# USER ENDPOINTS
# ================================

# Create a new user (public registration - use /auth/register instead)
@app.route('/users', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({'error': 'Email already exists'}), 400
        
        new_user = User(
            name=data['name'],
            address=data['address'],
            email=data['email']
        )
        
        # Set password
        new_user.set_password(data['password'])
        
        db.session.add(new_user)
        db.session.commit()
        
        return user_schema.jsonify(new_user), 201
        
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Get all users with pagination (JWT required)
@app.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    per_page = min(per_page, 100)  # Limit to 100 per page
    
    users_query = User.query
    paginated_users = paginate_query(users_query, page, per_page)
    
    return jsonify({
        'users': users_schema.dump(paginated_users['items']),
        'pagination': {
            'total': paginated_users['total'],
            'pages': paginated_users['pages'],
            'page': paginated_users['page'],
            'per_page': paginated_users['per_page'],
            'has_next': paginated_users['has_next'],
            'has_prev': paginated_users['has_prev'],
            'next_page': paginated_users['next_page'],
            'prev_page': paginated_users['prev_page']
        }
    })

# Get a specific user (JWT required)
@app.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return user_schema.jsonify(user)

# Update a user (JWT required)
@app.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    try:
        current_user_id = get_current_user_id()
        user = User.query.get_or_404(user_id)
        
        # Users can only update their own profile
        if current_user_id != user_id:
            return jsonify({'error': 'Unauthorized: You can only update your own profile'}), 403
        
        data = request.get_json()
        
        # Check if email is being changed and if it already exists
        if 'email' in data and data['email'] != user.email:
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user:
                return jsonify({'error': 'Email already exists'}), 400
        
        user.name = data.get('name', user.name)
        user.address = data.get('address', user.address)
        user.email = data.get('email', user.email)
        
        # Update password if provided
        if 'password' in data:
            user.set_password(data['password'])
        
        db.session.commit()
        return user_schema.jsonify(user)
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Delete a user (JWT required)
@app.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    try:
        current_user_id = get_current_user_id()
        user = User.query.get_or_404(user_id)
        
        # Users can only delete their own profile
        if current_user_id != user_id:
            return jsonify({'error': 'Unauthorized: You can only delete your own profile'}), 403
        
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ================================
# PRODUCT ENDPOINTS
# ================================

# Create a new product (JWT required)
@app.route('/products', methods=['POST'])
@jwt_required()
def create_product():
    try:
        data = request.get_json()
        
        new_product = Product(
            product_name=data['product_name'],
            price=float(data['price'])
        )
        
        db.session.add(new_product)
        db.session.commit()
        
        return product_schema.jsonify(new_product), 201
        
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {str(e)}'}), 400
    except ValueError:
        return jsonify({'error': 'Price must be a valid number'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Get all products with pagination
@app.route('/products', methods=['GET'])
def get_products():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    per_page = min(per_page, 100)  # Limit to 100 per page
    
    # Optional search by name
    search = request.args.get('search', '', type=str)
    
    products_query = Product.query
    if search:
        products_query = products_query.filter(Product.product_name.ilike(f'%{search}%'))
    
    paginated_products = paginate_query(products_query, page, per_page)
    
    return jsonify({
        'products': products_schema.dump(paginated_products['items']),
        'pagination': {
            'total': paginated_products['total'],
            'pages': paginated_products['pages'],
            'page': paginated_products['page'],
            'per_page': paginated_products['per_page'],
            'has_next': paginated_products['has_next'],
            'has_prev': paginated_products['has_prev'],
            'next_page': paginated_products['next_page'],
            'prev_page': paginated_products['prev_page']
        }
    })

# Get a specific product
@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return product_schema.jsonify(product)

# Update a product (JWT required)
@app.route('/products/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        data = request.get_json()
        
        product.product_name = data.get('product_name', product.product_name)
        if 'price' in data:
            product.price = float(data['price'])
        
        db.session.commit()
        return product_schema.jsonify(product)
        
    except ValueError:
        return jsonify({'error': 'Price must be a valid number'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Delete a product (JWT required)
@app.route('/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        db.session.delete(product)
        db.session.commit()
        return jsonify({'message': 'Product deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ================================
# ORDER ENDPOINTS
# ================================

# Create a new order (JWT required)
@app.route('/orders', methods=['POST'])
@jwt_required()
def create_order():
    try:
        current_user_id = get_current_user_id()
        data = request.get_json()
        
        # Create new order
        new_order = Order(
            user_id=current_user_id,  # Use authenticated user
            order_date=datetime.utcnow(),
            shipping_address=data.get('shipping_address', ''),
            notes=data.get('notes', '')
        )
        
        # Add products to order if provided
        if 'product_ids' in data:
            for product_id in data['product_ids']:
                product = Product.query.get(product_id)
                if product:
                    # Check if product is already in the order (prevents duplicates)
                    if product not in new_order.products:
                        new_order.products.append(product)
                else:
                    return jsonify({'error': f'Product with id {product_id} not found'}), 404
        
        # Calculate total
        new_order.calculate_total()
        
        db.session.add(new_order)
        db.session.commit()
        
        return order_schema.jsonify(new_order), 201
        
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Get all orders with pagination (JWT required)
@app.route('/orders', methods=['GET'])
@jwt_required()
def get_orders():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    per_page = min(per_page, 100)  # Limit to 100 per page
    
    orders_query = Order.query
    paginated_orders = paginate_query(orders_query, page, per_page)
    
    return jsonify({
        'orders': orders_schema.dump(paginated_orders['items']),
        'pagination': {
            'total': paginated_orders['total'],
            'pages': paginated_orders['pages'],
            'page': paginated_orders['page'],
            'per_page': paginated_orders['per_page'],
            'has_next': paginated_orders['has_next'],
            'has_prev': paginated_orders['has_prev'],
            'next_page': paginated_orders['next_page'],
            'prev_page': paginated_orders['prev_page']
        }
    })

# Get a specific order (JWT required)
@app.route('/orders/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    current_user_id = get_current_user_id()
    order = Order.query.get_or_404(order_id)
    
    # Users can only view their own orders
    if order.user_id != current_user_id:
        return jsonify({'error': 'Unauthorized: You can only view your own orders'}), 403
    
    return order_schema.jsonify(order)

# Update order status (JWT required)
@app.route('/orders/<int:order_id>/status', methods=['PUT'])
@jwt_required()
def update_order_status(order_id):
    try:
        current_user_id = get_current_user_id()
        order = Order.query.get_or_404(order_id)
        
        # Users can only update their own orders
        if order.user_id != current_user_id:
            return jsonify({'error': 'Unauthorized: You can only update your own orders'}), 403
        
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']:
            return jsonify({'error': 'Invalid status'}), 400
        
        order.status = new_status
        
        # Update other fields if provided
        if 'shipping_address' in data:
            order.shipping_address = data['shipping_address']
        if 'notes' in data:
            order.notes = data['notes']
        
        db.session.commit()
        return order_schema.jsonify(order)
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Cancel an order (JWT required)
@app.route('/orders/<int:order_id>/cancel', methods=['PUT'])
@jwt_required()
def cancel_order(order_id):
    try:
        current_user_id = get_current_user_id()
        order = Order.query.get_or_404(order_id)
        
        # Users can only cancel their own orders
        if order.user_id != current_user_id:
            return jsonify({'error': 'Unauthorized: You can only cancel your own orders'}), 403
        
        # Can only cancel pending or confirmed orders
        if order.status not in ['pending', 'confirmed']:
            return jsonify({'error': f'Cannot cancel order with status: {order.status}'}), 400
        
        order.status = 'cancelled'
        db.session.commit()
        
        return jsonify({'message': 'Order cancelled successfully', 'order': order_schema.dump(order)})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Get orders by status with pagination (JWT required)
@app.route('/orders/status/<status>', methods=['GET'])
@jwt_required()
def get_orders_by_status(status):
    if status not in ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']:
        return jsonify({'error': 'Invalid status'}), 400
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    per_page = min(per_page, 100)
    
    orders_query = Order.query.filter_by(status=status)
    paginated_orders = paginate_query(orders_query, page, per_page)
    
    return jsonify({
        'orders': orders_schema.dump(paginated_orders['items']),
        'status': status,
        'pagination': {
            'total': paginated_orders['total'],
            'pages': paginated_orders['pages'],
            'page': paginated_orders['page'],
            'per_page': paginated_orders['per_page'],
            'has_next': paginated_orders['has_next'],
            'has_prev': paginated_orders['has_prev'],
            'next_page': paginated_orders['next_page'],
            'prev_page': paginated_orders['prev_page']
        }
    })

# Get orders by user with pagination (JWT required)
@app.route('/orders/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_orders(user_id):
    current_user_id = get_current_user_id()
    
    # Users can only view their own orders
    if current_user_id != user_id:
        return jsonify({'error': 'Unauthorized: You can only view your own orders'}), 403
    
    user = User.query.get_or_404(user_id)
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    per_page = min(per_page, 100)
    
    orders_query = Order.query.filter_by(user_id=user_id)
    paginated_orders = paginate_query(orders_query, page, per_page)
    
    return jsonify({
        'orders': orders_schema.dump(paginated_orders['items']),
        'user': user_schema.dump(user),
        'pagination': {
            'total': paginated_orders['total'],
            'pages': paginated_orders['pages'],
            'page': paginated_orders['page'],
            'per_page': paginated_orders['per_page'],
            'has_next': paginated_orders['has_next'],
            'has_prev': paginated_orders['has_prev'],
            'next_page': paginated_orders['next_page'],
            'prev_page': paginated_orders['prev_page']
        }
    })

# Get all products for an order (JWT required)
@app.route('/orders/<int:order_id>/products', methods=['GET'])
@jwt_required()
def get_order_products(order_id):
    current_user_id = get_current_user_id()
    order = Order.query.get_or_404(order_id)
    
    # Users can only view products of their own orders
    if order.user_id != current_user_id:
        return jsonify({'error': 'Unauthorized: You can only view your own orders'}), 403
    
    return products_schema.jsonify(order.products)

# Add product to existing order (JWT required)
@app.route('/orders/<int:order_id>/add_product/<int:product_id>', methods=['PUT'])
@jwt_required()
def add_product_to_order(order_id, product_id):
    try:
        current_user_id = get_current_user_id()
        order = Order.query.get_or_404(order_id)
        product = Product.query.get_or_404(product_id)
        
        # Users can only modify their own orders
        if order.user_id != current_user_id:
            return jsonify({'error': 'Unauthorized: You can only modify your own orders'}), 403
        
        # Can only modify pending orders
        if order.status != 'pending':
            return jsonify({'error': f'Cannot modify order with status: {order.status}'}), 400
        
        # Check if product is already in the order (prevents duplicates)
        if product in order.products:
            return jsonify({'error': 'Product already in order'}), 400
        
        order.products.append(product)
        order.calculate_total()  # Recalculate total
        db.session.commit()
        
        return order_schema.jsonify(order)
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Remove product from order (JWT required)
@app.route('/orders/<int:order_id>/remove_product/<int:product_id>', methods=['DELETE'])
@jwt_required()
def remove_product_from_order(order_id, product_id):
    try:
        current_user_id = get_current_user_id()
        order = Order.query.get_or_404(order_id)
        product = Product.query.get_or_404(product_id)
        
        # Users can only modify their own orders
        if order.user_id != current_user_id:
            return jsonify({'error': 'Unauthorized: You can only modify your own orders'}), 403
        
        # Can only modify pending orders
        if order.status != 'pending':
            return jsonify({'error': f'Cannot modify order with status: {order.status}'}), 400
        
        if product in order.products:
            order.products.remove(product)
            order.calculate_total()  # Recalculate total
            db.session.commit()
            return jsonify({'message': 'Product removed from order'})
        else:
            return jsonify({'error': 'Product not in order'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Delete an order (JWT required)
@app.route('/orders/<int:order_id>', methods=['DELETE'])
@jwt_required()
def delete_order(order_id):
    try:
        current_user_id = get_current_user_id()
        order = Order.query.get_or_404(order_id)
        
        # Users can only delete their own orders
        if order.user_id != current_user_id:
            return jsonify({'error': 'Unauthorized: You can only delete your own orders'}), 403
        
        # Can only delete pending or cancelled orders
        if order.status not in ['pending', 'cancelled']:
            return jsonify({'error': f'Cannot delete order with status: {order.status}'}), 400
        
        db.session.delete(order)
        db.session.commit()
        return jsonify({'message': 'Order deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ================================
# DATABASE INITIALIZATION
# ================================

# Create all tables
@app.route('/init-db', methods=['POST'])
def init_database():
    try:
        db.create_all()
        return jsonify({'message': 'Database tables created successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create tables when app starts
    try:
        with app.app_context():
            db.create_all()
            print("✅ Database tables created successfully")
    except Exception as e:
        print(f"⚠️  Database warning: {e}")
        print("   Make sure MySQL is running and credentials are correct")
    
    print(f"🚀 Starting E-commerce API on http://localhost:5001")
    app.run(debug=True, port=5001)
