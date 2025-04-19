from flask import Flask, render_template, url_for, request, jsonify, redirect, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_user, logout_user, login_required, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from secrets import token_urlsafe
from functools import wraps
from sqlalchemy import func
import os
import time
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure key
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/ecommerce'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'error'

db = SQLAlchemy(app)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Add this context processor after your app configuration
@app.context_processor
def utility_processor():
    return {
        'now': datetime.utcnow()
    }

class Category(db.Model):
    __tablename__ = 'categories'
    CategoryID = db.Column(db.Integer, primary_key=True)
    CategoryName = db.Column(db.String(50), nullable=False)  # Changed from Name
    Description = db.Column(db.Text)

class Product(db.Model):
    __tablename__ = 'products'
    ProductID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100), nullable=False)
    Description = db.Column(db.Text)
    Price = db.Column(db.Float, nullable=False)
    Stock = db.Column(db.Integer, nullable=False)
    ImageURL = db.Column(db.String(200))
    CategoryID = db.Column(db.Integer, db.ForeignKey('categories.CategoryID'), nullable=False)
    category = db.relationship('Category', backref=db.backref('products', lazy=True))

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    UserID = db.Column(db.Integer, primary_key=True)
    Fullname = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(120), unique=True, nullable=False)
    Password = db.Column(db.String(255), nullable=False)
    Phone = db.Column(db.String(20))
    Address = db.Column(db.Text)
    IsAdmin = db.Column(db.Boolean, default=False)
    
    def get_id(self):
        return str(self.UserID)

# Add after the User model definition
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Cart(db.Model):
    __tablename__ = 'cart'
    CartID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey('users.UserID'), nullable=False)
    ProductID = db.Column(db.Integer, db.ForeignKey('products.ProductID'), nullable=False)
    Quantity = db.Column(db.Integer, nullable=False)

    # Add relationships
    product = db.relationship('Product', backref='cart_items')

class Order(db.Model):
    __tablename__ = 'orders'
    OrderID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey('users.UserID'), nullable=False)
    OrderDate = db.Column(db.DateTime, default=datetime.utcnow)
    TotalAmount = db.Column(db.Float, nullable=False)
    Status = db.Column(db.String(50), default='Pending')
    
    # Add shipping and payment relationships
    shipment = db.relationship('Shipment', backref='order', uselist=False)
    payment = db.relationship('Payment', backref='order', uselist=False)

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    OrderItemID = db.Column(db.Integer, primary_key=True)
    OrderID = db.Column(db.Integer, db.ForeignKey('orders.OrderID'), nullable=False)
    ProductID = db.Column(db.Integer, db.ForeignKey('products.ProductID'), nullable=False)
    Quantity = db.Column(db.Integer, nullable=False)
    Price = db.Column(db.Float, nullable=False)
    
    product = db.relationship('Product')

class Payment(db.Model):
    __tablename__ = 'payments'
    PaymentID = db.Column(db.Integer, primary_key=True)
    OrderID = db.Column(db.Integer, db.ForeignKey('orders.OrderID'), nullable=False)
    Amount = db.Column(db.Float, nullable=False)
    PaymentMethod = db.Column(db.String(50), nullable=False)
    PaymentStatus = db.Column(db.String(50), default='Pending')
    TransactionID = db.Column(db.String(100), unique=True)
    PaymentDate = db.Column(db.DateTime, default=datetime.utcnow)

class Shipment(db.Model):
    __tablename__ = 'shipments'
    ShipmentID = db.Column(db.Integer, primary_key=True)
    OrderID = db.Column(db.Integer, db.ForeignKey('orders.OrderID'), nullable=False)
    ShippingAddress = db.Column(db.Text, nullable=False)
    TrackingNumber = db.Column(db.String(50))
    ShippingMethod = db.Column(db.String(50), nullable=False)
    ShippingStatus = db.Column(db.String(50), default='Pending')
    EstimatedDelivery = db.Column(db.DateTime)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.IsAdmin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@admin_required
def admin_dashboard():
    stats = {
        'total_orders': Order.query.count(),
        'total_users': User.query.count(),
        'total_products': Product.query.count(),
        'total_revenue': db.session.query(
            func.sum(Order.TotalAmount)).scalar() or 0.0
    }
    return render_template('admin/dashboard.html', stats=stats)

@app.route('/admin/products')
@admin_required
def admin_products():
    products = Product.query.all()
    categories = Category.query.all()
    return render_template('admin/products.html', products=products, categories=categories)

@app.route('/admin/products/add', methods=['POST'])
@admin_required
def add_product():
    try:
        product = Product(
            Name=request.form['name'],
            Description=request.form['description'],
            Price=float(request.form['price']),
            Stock=int(request.form['stock']),
            CategoryID=int(request.form['category_id']),
            ImageURL=request.form['image_url']
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding product: {str(e)}', 'error')
    return redirect(url_for('admin_products'))

@app.route('/admin/products/<int:product_id>', methods=['GET'])
@admin_required
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify({
        'ProductID': product.ProductID,
        'Name': product.Name,
        'Description': product.Description,
        'Price': product.Price,
        'Stock': product.Stock,
        'CategoryID': product.CategoryID,
        'ImageURL': product.ImageURL
    })

@app.route('/admin/products/<int:product_id>/update', methods=['POST'])
@admin_required
def update_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        product.Name = request.form['name']
        product.Description = request.form['description']
        product.Price = float(request.form['price'])
        product.Stock = int(request.form['stock'])
        product.CategoryID = int(request.form['category_id'])
        if request.form.get('image_url'):
            product.ImageURL = request.form['image_url']
        
        db.session.commit()
        flash('Product updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating product: {str(e)}', 'error')
    return redirect(url_for('admin_products'))

@app.route('/admin/products/<int:product_id>/delete', methods=['POST'])
@admin_required
def delete_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        db.session.delete(product)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/products/<int:product_id>', methods=['PUT', 'DELETE'])
@admin_required
def manage_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'DELETE':
        try:
            db.session.delete(product)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
            
    elif request.method == 'PUT':
        try:
            product.Name = request.form['name']
            product.Description = request.form['description']
            product.Price = float(request.form['price'])
            product.Stock = int(request.form['stock'])
            product.CategoryID = int(request.form['category_id'])
            
            image = request.files.get('image')
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                product.ImageURL = url_for('static', filename=f'uploads/{filename}')
            
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/orders')
@admin_required
def admin_orders():
    orders = Order.query.order_by(Order.OrderDate.desc()).all()
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/')
def index():
    # Get some trending products (maybe the newest or most popular)
    trending_products = Product.query.limit(4).all()
    return render_template('index.html', trending_products=trending_products)

@app.route('/products')
def products():
    search_query = request.args.get('q', '')
    if search_query:
        products_list = Product.query.filter(Product.Name.like(f'%{search_query}%')).all()
    else:
        products_list = Product.query.all()
    return render_template('products.html', products=products_list, search_query=search_query)

@app.route('/product/<int:product_id>')
def product_details(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_details.html', product=product)

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        flash('Please login to add items to cart')
        return redirect(url_for('login'))
    
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))
    user_id = session['user_id']
    
    product = Product.query.get_or_404(product_id)
    
    if product.Stock < quantity:
        flash('Not enough stock available!')
        return redirect(url_for('product_details', product_id=product_id))
    
    # Check if item already exists in cart
    cart_item = Cart.query.filter_by(UserID=user_id, ProductID=product_id).first()
    
    try:
        if cart_item:
            cart_item.Quantity += quantity
        else:
            cart_item = Cart(UserID=user_id, ProductID=product_id, Quantity=quantity)
            db.session.add(cart_item)
        
        db.session.commit()
        flash('Product added to cart!')
    except Exception as e:
        db.session.rollback()
        flash('Failed to add product to cart.')
    
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        flash('Please login to view your cart')
        return redirect(url_for('login'))
    
    cart_items = Cart.query.filter_by(UserID=session['user_id']).all()
    total = sum(item.product.Price * item.Quantity for item in cart_items)
    
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/update-cart', methods=['POST'])
def update_cart_item():
    if 'user_id' not in session:
        flash('Please login to update cart')
        return redirect(url_for('login'))
    
    cart_id = request.form.get('cart_id')
    quantity = int(request.form.get('quantity', 1))
    
    cart_item = Cart.query.get_or_404(cart_id)
    
    # Verify the cart item belongs to the logged-in user
    if cart_item.UserID != session['user_id']:
        flash('Unauthorized action')
        return redirect(url_for('cart'))
    
    try:
        if quantity > 0:
            # Check if we have enough stock
            if quantity > cart_item.product.Stock:
                flash('Not enough stock available!')
            else:
                cart_item.Quantity = quantity
                db.session.commit()
                flash('Cart updated successfully!')
        else:
            # If quantity is 0 or negative, remove the item
            db.session.delete(cart_item)
            db.session.commit()
            flash('Item removed from cart')
            
    except Exception as e:
        db.session.rollback()
        flash('Failed to update cart')
    
    return redirect(url_for('cart'))

@app.route('/remove-from-cart', methods=['POST'])
def remove_from_cart():
    if 'user_id' not in session:
        flash('Please login to remove items')
        return redirect(url_for('login'))
    
    cart_id = request.form.get('cart_id')
    cart_item = Cart.query.get_or_404(cart_id)
    
    # Verify the cart item belongs to the logged-in user
    if cart_item.UserID != session['user_id']:
        flash('Unauthorized action')
        return redirect(url_for('cart'))
    
    try:
        db.session.delete(cart_item)
        db.session.commit()
        flash('Item removed from cart')
    except Exception as e:
        db.session.rollback()
        flash('Failed to remove item')
    
    return redirect(url_for('cart'))

@app.route('/checkout/options', methods=['GET', 'POST'])
@login_required
def checkout_options():
    cart_items = Cart.query.filter_by(UserID=current_user.UserID).all()
    if not cart_items:
        flash('Your cart is empty', 'error')
        return redirect(url_for('cart'))

    total = sum(item.product.Price * item.Quantity for item in cart_items)
    return render_template('checkout_options.html', cart_items=cart_items, total=total)

@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    try:
        cart_items = Cart.query.filter_by(UserID=current_user.UserID).all()
        if not cart_items:
            flash('Your cart is empty', 'error')
            return redirect(url_for('cart'))

        # Calculate total
        total_amount = sum(item.product.Price * item.Quantity for item in cart_items)
        shipping_cost = float(request.form.get('shipping_method').split(':')[1])
        final_total = total_amount + shipping_cost

        # Create order
        order = Order(
            UserID=current_user.UserID,
            OrderDate=datetime.utcnow(),
            TotalAmount=final_total,
            Status='Pending'
        )
        db.session.add(order)
        db.session.flush()

        # Create shipment record
        shipping_method = request.form.get('shipping_method').split(':')[0]
        estimated_delivery = datetime.utcnow()
        if shipping_method == 'standard':
            estimated_delivery += timedelta(days=7)
        elif shipping_method == 'express':
            estimated_delivery += timedelta(days=3)
        else:  # overnight
            estimated_delivery += timedelta(days=1)

        shipment = Shipment(
            OrderID=order.OrderID,
            ShippingAddress=f"{request.form.get('address')}, {request.form.get('city')}, "
                          f"{request.form.get('state')} {request.form.get('zipcode')}",
            ShippingMethod=shipping_method,
            ShippingStatus='Pending',
            EstimatedDelivery=estimated_delivery,
            TrackingNumber=f"TRK-{token_urlsafe(8)}"
        )
        db.session.add(shipment)

        # Simplified payment handling
        payment_method = request.form.get('payment_method')
        payment = Payment(
            OrderID=order.OrderID,
            Amount=final_total,
            PaymentMethod=payment_method,
            PaymentStatus='Pending' if payment_method == 'cash' else 'Completed',
            TransactionID=f"TXN-{token_urlsafe(8)}",
            PaymentDate=datetime.utcnow()
        )
        db.session.add(payment)

        # Update order status based on payment method
        order.Status = 'Pending' if payment_method == 'cash' else 'Processing'

        # Create order items and update stock
        for cart_item in cart_items:
            if cart_item.Quantity > cart_item.product.Stock:
                raise Exception(f'Not enough stock for {cart_item.product.Name}')

            order_item = OrderItem(
                OrderID=order.OrderID,
                ProductID=cart_item.ProductID,
                Quantity=cart_item.Quantity,
                Price=cart_item.product.Price
            )
            db.session.add(order_item)

            # Update product stock
            cart_item.product.Stock -= cart_item.Quantity

        # Clear cart
        Cart.query.filter_by(UserID=current_user.UserID).delete()

        db.session.commit()
        flash('Order placed successfully!', 'success')
        return redirect(url_for('order_confirmation', order_id=order.OrderID))

    except Exception as e:
        db.session.rollback()
        flash(f'Error processing order: {str(e)}', 'error')
        return redirect(url_for('cart'))

@app.route('/process_checkout', methods=['POST'])
def process_checkout():
    if 'user_id' not in session:
        flash('Please login to checkout', 'error')
        return redirect(url_for('login'))
        
    try:
        shipping_address = request.form.get('shipping_address')
        shipping_method = request.form.get('shipping_method')
        payment_method = request.form.get('payment_method')
        
        if not all([shipping_address, shipping_method, payment_method]):
            flash('Please fill in all required fields', 'error')
            return redirect(url_for('checkout'))
            
        # Process the order here
        # ...your order processing logic...
        
        flash('Order placed successfully!', 'success')
        return redirect(url_for('order_confirmation'))
        
    except Exception as e:
        flash('An error occurred while processing your order', 'error')
        return redirect(url_for('checkout'))

@app.route('/order-confirmation/<int:order_id>')
def order_confirmation(order_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    order = Order.query.get_or_404(order_id)
    if order.UserID != session['user_id']:
        flash('Unauthorized access')
        return redirect(url_for('index'))
    
    order_items = OrderItem.query.filter_by(OrderID=order_id).all()
    return render_template('order_confirmation.html', order=order, items=order_items)

@app.route('/my-orders')
def my_orders():
    if 'user_id' not in session:
        flash('Please login to view your orders')
        return redirect(url_for('login'))
    
    orders = Order.query.filter_by(UserID=session['user_id']).order_by(Order.OrderDate.desc()).all()
    return render_template('my_orders.html', orders=orders)

# @app.route('/test-db')
# def test_db():
#     try:
#         # Try to query the database
#         test_query = Product.query.first()
#         return jsonify({
#             "status": "success",
#             "message": "Database connection successful!",
#             "data": {
#                 "product_count": Product.query.count()
#             }
#         })
#     except Exception as e:
#         return jsonify({
#             "status": "error",
#             "message": f"Database connection failed: {str(e)}"
#         }), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            user = User.query.filter_by(Email=email).first()
            
            if user and check_password_hash(user.Password, password):
                login_user(user)
                flash('Login successful!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page if next_page else url_for('index'))
            else:
                flash('Invalid email or password', 'error')
                return redirect(url_for('login'))
                
        except Exception as e:
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        address = request.form.get('address')
        
        if User.query.filter_by(Email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        new_user = User(
            Fullname=fullname,
            Email=email,
            Password=hashed_password,
            Phone=phone,
            Address=address
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/submit-contact', methods=['POST'])
def submit_contact():
    name = request.form.get('name')
    email = request.form.get('email')
    subject = request.form.get('subject')
    message = request.form.get('message')
    
    # Here you would typically save to database or send email
    flash('Thank you for your message. We will get back to you soon!', 'success')
    return redirect(url_for('contact'))

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Please login to view your profile')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)

@app.route('/update-profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        flash('Please login to update your profile')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    try:
        user.Fullname = request.form.get('fullname')
        user.Phone = request.form.get('phone')
        user.Address = request.form.get('address')
        
        if request.form.get('current_password'):
            if check_password_hash(user.Password, request.form.get('current_password')):
                if request.form.get('new_password') == request.form.get('confirm_password'):
                    user.Password = generate_password_hash(request.form.get('new_password'))
                else:
                    flash('New passwords do not match')
                    return redirect(url_for('profile'))
            else:
                flash('Current password is incorrect')
                return redirect(url_for('profile'))
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    except:
        db.session.rollback()
        flash('Failed to update profile')
    
    return redirect(url_for('profile'))

@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot_password.html')

@app.route('/change-password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        flash('Please login first')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not check_password_hash(user.Password, current_password):
        flash('Current password is incorrect')
        return redirect(url_for('profile'))
        
    if new_password != confirm_password:
        flash('New passwords do not match')
        return redirect(url_for('profile'))
        
    try:
        user.Password = generate_password_hash(new_password)
        db.session.commit()
        flash('Password updated successfully!')
    except:
        db.session.rollback()
        flash('Failed to update password')
    
    return redirect(url_for('profile'))

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    
    if user is None or user.reset_token_expiry < datetime.utcnow():
        flash('Invalid or expired reset token')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password == confirm_password:
            user.Password = generate_password_hash(password)
            user.reset_token = None
            user.reset_token_expiry = None
            db.session.commit()
            flash('Password has been reset successfully!', 'success')
            return redirect(url_for('login'))
        else:
            flash('Passwords do not match')
            
    return render_template('reset_password.html')

@app.route('/init-admin')
def init_admin():
    try:
        # Check if admin already exists
        admin = User.query.filter_by(Email='admin@eshop.com').first()
        if not admin:
            admin = User(
                Fullname='Admin',
                Email='admin@eshop.com',
                Password=generate_password_hash('adminpass'),
                IsAdmin=True
            )
            db.session.add(admin)
            db.session.commit()
            return 'Admin account created successfully'
    except Exception as e:
        return str(e)
    return 'Admin account already exists'

if __name__ == '__main__':
    app.run(debug=True)