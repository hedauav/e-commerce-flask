import os
import sqlite3
import functools
from flask import Flask, render_template, url_for, flash, redirect, request, session, g
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash


# Function to get the database connection
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    
    if db is not None:
        db.close()

# Create the Flask application
app = Flask(__name__, instance_relative_config=True)
app.config.from_mapping(
    SECRET_KEY='dev',
    DATABASE=os.path.join(app.instance_path, 'ecommerce.db'),
    UPLOAD_FOLDER='static/images/products'
)

# Ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

# Initialize the database
def init_db():
    db = sqlite3.connect(app.config['DATABASE'])
    
    with app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))
    
    db.close()

@app.cli.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    print('Initialized the database.')

# Close the database connection when the app context ends
app.teardown_appcontext(close_db)

# Authentication helpers
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM users WHERE id = ?', (user_id,)
        ).fetchone()

# Routes
@app.route('/')
def home():
    db_conn = get_db()
    # Get featured products (random selection)
    featured_products = db_conn.execute(
        'SELECT p.*, c.name as category_name FROM products p '
        'JOIN categories c ON p.category_id = c.id '
        'ORDER BY RANDOM() LIMIT 4'
    ).fetchall()
    
    categories = db_conn.execute('SELECT * FROM categories').fetchall()
    
    return render_template('home.html', featured_products=featured_products, categories=categories)

@app.route('/products')
def products():
    db_conn = get_db()
    category_id = request.args.get('category', type=int)
    
    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 8
    offset = (page - 1) * per_page
    
    # Query based on category filter
    if category_id:
        products = db_conn.execute(
            'SELECT p.*, c.name as category_name FROM products p '
            'JOIN categories c ON p.category_id = c.id '
            'WHERE p.category_id = ? '
            'LIMIT ? OFFSET ?',
            (category_id, per_page, offset)
        ).fetchall()
        
        # Count for pagination
        total = db_conn.execute(
            'SELECT COUNT(*) FROM products WHERE category_id = ?',
            (category_id,)
        ).fetchone()[0]
    else:
        products = db_conn.execute(
            'SELECT p.*, c.name as category_name FROM products p '
            'JOIN categories c ON p.category_id = c.id '
            'LIMIT ? OFFSET ?',
            (per_page, offset)
        ).fetchall()
        
        # Count for pagination
        total = db_conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    
    # Calculate pagination info
    total_pages = (total // per_page) + (1 if total % per_page > 0 else 0)
    
    categories = db_conn.execute('SELECT * FROM categories').fetchall()
    
    return render_template(
        'products.html', 
        products=products, 
        categories=categories,
        page=page,
        total_pages=total_pages,
        total_products=total,
        category_id=category_id
    )

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    db_conn = get_db()
    product = db_conn.execute(
        'SELECT p.*, c.name as category_name FROM products p '
        'JOIN categories c ON p.category_id = c.id '
        'WHERE p.id = ?',
        (product_id,)
    ).fetchone()
    
    if product is None:
        flash('Product not found', 'danger')
        return redirect(url_for('products'))
    
    return render_template('product_detail.html', product=product)

@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password_confirm = request.form['password_confirm']
        
        db_conn = get_db()
        error = None
        
        if not username:
            error = 'Username is required.'
        elif not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        elif password != password_confirm:
            error = 'Passwords do not match.'
        elif db_conn.execute(
            'SELECT id FROM users WHERE username = ?', (username,)
        ).fetchone() is not None:
            error = f'User {username} is already registered.'
        elif db_conn.execute(
            'SELECT id FROM users WHERE email = ?', (email,)
        ).fetchone() is not None:
            error = f'Email {email} is already registered.'
        
        if error is None:
            db_conn.execute(
                'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                (username, email, generate_password_hash(password))
            )
            db_conn.commit()
            
            flash('Registration successful. You can now log in.', 'success')
            return redirect(url_for('login'))
        
        flash(error, 'danger')
    
    return render_template('register.html')

@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        db_conn = get_db()
        error = None
        
        user = db_conn.execute(
            'SELECT * FROM users WHERE email = ?', (email,)
        ).fetchone()
        
        if user is None:
            error = 'Incorrect email.'
        elif not check_password_hash(user['password_hash'], password):
            error = 'Incorrect password.'
        
        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('home'))
        
        flash(error, 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    db_conn = get_db()
    quantity = int(request.form.get('quantity', 1))
    
    # Verify product exists and has enough stock
    product = db_conn.execute(
        'SELECT * FROM products WHERE id = ?', (product_id,)
    ).fetchone()
    
    if product is None:
        flash('Product not found', 'danger')
        return redirect(url_for('products'))
    
    if quantity > product['stock']:
        flash('Not enough items in stock!', 'danger')
        return redirect(url_for('product_detail', product_id=product_id))
    
    # Check if product already in cart
    cart_item = db_conn.execute(
        'SELECT * FROM cart WHERE user_id = ? AND product_id = ?',
        (g.user['id'], product_id)
    ).fetchone()
    
    if cart_item:
        # Update quantity
        db_conn.execute(
            'UPDATE cart SET quantity = quantity + ? WHERE id = ?',
            (quantity, cart_item['id'])
        )
    else:
        # Add new cart item
        db_conn.execute(
            'INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)',
            (g.user['id'], product_id, quantity)
        )
    
    db_conn.commit()
    flash('Product added to cart!', 'success')
    return redirect(url_for('cart'))

@app.route('/cart')
@login_required
def cart():
    db_conn = get_db()
    cart_items = db_conn.execute(
        'SELECT c.id, c.quantity, p.id as product_id, p.name, p.price, p.image '
        'FROM cart c JOIN products p ON c.product_id = p.id '
        'WHERE c.user_id = ?',
        (g.user['id'],)
    ).fetchall()
    
    # Calculate total
    total = 0
    for item in cart_items:
        total += item['price'] * item['quantity']
    
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/update_cart/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    db_conn = get_db()
    quantity = int(request.form.get('quantity', 0))
    
    # Verify cart item belongs to user
    cart_item = db_conn.execute(
        'SELECT c.*, p.stock FROM cart c JOIN products p ON c.product_id = p.id '
        'WHERE c.id = ? AND c.user_id = ?',
        (item_id, g.user['id'])
    ).fetchone()
    
    if cart_item is None:
        flash('Item not found in your cart', 'danger')
        return redirect(url_for('cart'))
    
    if quantity <= 0:
        # Remove item if quantity is 0 or negative
        db_conn.execute('DELETE FROM cart WHERE id = ?', (item_id,))
        flash('Item removed from cart', 'success')
    else:
        # Check if requested quantity is available
        if quantity > cart_item['stock']:
            flash(f'Only {cart_item["stock"]} items available in stock', 'warning')
            quantity = cart_item['stock']
        
        # Update quantity
        db_conn.execute(
            'UPDATE cart SET quantity = ? WHERE id = ?',
            (quantity, item_id)
        )
        flash('Cart updated', 'success')
    
    db_conn.commit()
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    db_conn = get_db()
    
    # Verify cart item belongs to user
    result = db_conn.execute(
        'DELETE FROM cart WHERE id = ? AND user_id = ?',
        (item_id, g.user['id'])
    )
    
    db_conn.commit()
    
    if result.rowcount > 0:
        flash('Item removed from cart', 'success')
    else:
        flash('Item not found in your cart', 'danger')
    
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    db_conn = get_db()
    
    # Get cart items
    cart_items = db_conn.execute(
        'SELECT c.id, c.quantity, p.id as product_id, p.name, p.price, p.stock '
        'FROM cart c JOIN products p ON c.product_id = p.id '
        'WHERE c.user_id = ?',
        (g.user['id'],)
    ).fetchall()
    
    if not cart_items:
        flash('Your cart is empty!', 'info')
        return redirect(url_for('cart'))
    
    # Calculate total
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    
    if request.method == 'POST':
        # Get form data
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        address = request.form.get('address')
        city = request.form.get('city')
        state = request.form.get('state')
        zip_code = request.form.get('zip_code')
        payment_method = request.form.get('payment_method')
        
        # Validate form data
        error = None
        if not full_name:
            error = 'Full name is required'
        elif not email:
            error = 'Email is required'
        elif not address:
            error = 'Address is required'
        elif not city:
            error = 'City is required'
        elif not state:
            error = 'State is required'
        elif not zip_code:
            error = 'Zip code is required'
        
        # Verify stock before creating order
        for item in cart_items:
            if item['quantity'] > item['stock']:
                error = f'Not enough stock for {item["name"]}'
                break
        
        if error is None:
            try:
                # Build shipping address
                shipping_address = f"{full_name}, {address}, {city}, {state}, {zip_code}"
                
                # Create order
                cursor = db_conn.cursor()
                cursor.execute(
                    'INSERT INTO orders (user_id, total, shipping_address) VALUES (?, ?, ?)',
                    (g.user['id'], total, shipping_address)
                )
                order_id = cursor.lastrowid
                
                # Create order items and update stock
                for item in cart_items:
                    cursor.execute(
                        'INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)',
                        (order_id, item['product_id'], item['quantity'], item['price'])
                    )
                    
                    # Update product stock
                    cursor.execute(
                        'UPDATE products SET stock = stock - ? WHERE id = ?',
                        (item['quantity'], item['product_id'])
                    )
                
                # Clear cart
                cursor.execute('DELETE FROM cart WHERE user_id = ?', (g.user['id'],))
                
                # Commit transaction
                db_conn.commit()
                
                flash('Order placed successfully!', 'success')
                return redirect(url_for('orders'))
                
            except db_conn.Error:
                db_conn.rollback()
                error = 'An error occurred while processing your order'
        
        if error:
            flash(error, 'danger')
    
    return render_template('checkout.html', cart_items=cart_items, total=total)

@app.route('/orders')
@login_required
def orders():
    db_conn = get_db()
    
    # Get user's orders
    orders_data = db_conn.execute(
        'SELECT * FROM orders WHERE user_id = ? ORDER BY order_date DESC',
        (g.user['id'],)
    ).fetchall()
    
    # Create a dictionary to map order IDs to their items
    order_items_map = {}
    
    # Get items for each order
    for order in orders_data:
        order_id = order['id']
        items = db_conn.execute(
            'SELECT oi.*, p.name, p.image FROM order_items oi '
            'JOIN products p ON oi.product_id = p.id '
            'WHERE oi.order_id = ?',
            (order_id,)
        ).fetchall()
        
        # Store in map by order id
        order_items_map[order_id] = items
    
    return render_template('orders.html', orders=orders_data, order_items_map=order_items_map)

# Run the application
if __name__ == '__main__':
    app.run(debug=True)