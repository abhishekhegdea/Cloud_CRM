from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
import random
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # For session management

# Initialize data
products = [
    {
        "id": 1,
        "name": "Wireless Headphones",
        "price": 89.99,
        "description": "High-quality wireless headphones with noise cancellation",
        "rating": 4.8,
        "sellerId": "S-1001",
        "sellerName": "AudioTech",
        "category": "electronics",
        "image": "https://picsum.photos/id/180/250/180",
        "stock": 45
    },
    {
        "id": 2,
        "name": "Smart Watch",
        "price": 159.99,
        "description": "Fitness tracking smartwatch with heart rate monitor",
        "rating": 4.6,
        "sellerId": "S-1002",
        "sellerName": "TechGear",
        "category": "electronics",
        "image": "https://picsum.photos/id/100/250/180",
        "stock": 30
    },
    {
        "id": 3,
        "name": "Laptop Backpack",
        "price": 49.99,
        "description": "Durable laptop backpack with USB charging port",
        "rating": 4.5,
        "sellerId": "S-1003",
        "sellerName": "Urban Carry",
        "category": "accessories",
        "image": "https://picsum.photos/id/1011/250/180",
        "stock": 78
    },
    {
        "id": 4,
        "name": "Ceramic Coffee Mug",
        "price": 12.99,
        "description": "Elegant ceramic coffee mug, microwave safe",
        "rating": 4.7,
        "sellerId": "S-1001",
        "sellerName": "HomeStyle",
        "category": "home",
        "image": "https://picsum.photos/id/367/250/180",
        "stock": 120
    },
    {
        "id": 5,
        "name": "Bluetooth Speaker",
        "price": 79.99,
        "description": "Waterproof bluetooth speaker with 20-hour battery life",
        "rating": 4.9,
        "sellerId": "S-1002",
        "sellerName": "AudioTech",
        "category": "electronics",
        "image": "https://picsum.photos/id/433/250/180",
        "stock": 25
    },
    {
        "id": 6,
        "name": "Cotton T-shirt",
        "price": 19.99,
        "description": "Premium cotton t-shirt, comfortable fit",
        "rating": 4.3,
        "sellerId": "S-1003",
        "sellerName": "FashionHub",
        "category": "clothing",
        "image": "https://picsum.photos/id/292/250/180",
        "stock": 200
    }
]

users = [
    {
        "id": "C-1001",
        "name": "John Doe",
        "email": "john@example.com",
        "password": "password123",  # In a real app, this would be hashed
        "type": "customer",
        "interests": ["electronics", "home"]
    },
    {
        "id": "S-1001",
        "name": "AudioTech",
        "email": "seller@audiotech.com",
        "password": "seller123",  # In a real app, this would be hashed
        "type": "seller"
    }
]

# Routes
@app.route('/')
def index():
    if 'user' in session:
        return render_template('index.html', authenticated=True)
    return render_template('index.html', authenticated=False)

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    for user in users:
        if user['email'].lower() == email.lower() and user['password'] == password:
            # In a real app, you'd use check_password_hash here
            session['user'] = user
            return jsonify({'success': True, 'user': user})
    
    return jsonify({'success': False, 'message': 'Invalid email or password'}), 401

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    user_type = data.get('type')
    
    # Check if email already exists
    if any(user['email'].lower() == email.lower() for user in users):
        return jsonify({'success': False, 'message': 'An account with this email already exists.'}), 400
    
    # Generate unique ID
    if user_type == 'customer':
        user_id = f"C-{1000 + len([u for u in users if u['type'] == 'customer']) + 1}"
    else:
        user_id = f"S-{1000 + len([u for u in users if u['type'] == 'seller']) + 1}"
    
    new_user = {
        "id": user_id,
        "name": name,
        "email": email,
        "password": password,  # In a real app, use generate_password_hash
        "type": user_type,
        "interests": ["electronics"] if user_type == 'customer' else []
    }
    
    users.append(new_user)
    session['user'] = new_user
    
    return jsonify({'success': True, 'user': new_user})

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('cart', None)
    return redirect(url_for('index'))

@app.route('/api/products')
def get_products():
    return jsonify(products)

@app.route('/api/recommended-products')
def get_recommended_products():
    if 'user' not in session or session['user']['type'] != 'customer':
        return jsonify([])
    
    user_interests = session['user'].get('interests', [])
    recommended = [p for p in products if p['category'] in user_interests]
    recommended.sort(key=lambda x: x['rating'], reverse=True)
    
    return jsonify(recommended[:3])

@app.route('/api/seller-products')
def get_seller_products():
    if 'user' not in session or session['user']['type'] != 'seller':
        return jsonify([])
    
    seller_id = session['user']['id']
    seller_products = [p for p in products if p['sellerId'] == seller_id]
    
    return jsonify(seller_products)

@app.route('/api/add-to-cart', methods=['POST'])
def add_to_cart():
    if 'cart' not in session:
        session['cart'] = []
    
    data = request.get_json()
    product_id = data.get('productId')
    
    product = next((p for p in products if p['id'] == product_id), None)
    if not product or product['stock'] <= 0:
        return jsonify({'success': False, 'message': 'Product out of stock'}), 400
    
    cart = session['cart']
    existing_item = next((item for item in cart if item['id'] == product_id), None)
    
    if existing_item:
        if existing_item['quantity'] >= product['stock']:
            return jsonify({'success': False, 'message': f"Maximum stock limit reached for {product['name']}"}), 400
        existing_item['quantity'] += 1
    else:
        cart.append({
            'id': product['id'],
            'name': product['name'],
            'price': product['price'],
            'quantity': 1
        })
    
    session['cart'] = cart
    return jsonify({'success': True, 'message': f"{product['name']} added to cart!"})

@app.route('/api/remove-from-cart', methods=['POST'])
def remove_from_cart():
    if 'cart' not in session:
        return jsonify({'success': False, 'message': 'Cart is empty'}), 400
    
    data = request.get_json()
    product_id = data.get('productId')
    
    cart = session['cart']
    session['cart'] = [item for item in cart if item['id'] != product_id]
    
    return jsonify({'success': True})

@app.route('/api/cart')
def get_cart():
    if 'cart' not in session:
        session['cart'] = []
    
    return jsonify(session['cart'])

@app.route('/api/checkout', methods=['POST'])
def checkout():
    if 'cart' not in session or not session['cart']:
        return jsonify({'success': False, 'message': 'Cart is empty'}), 400
    
    order_id = f"ORD-{random.randint(100000, 999999)}"
    session['cart'] = []
    
    return jsonify({'success': True, 'orderId': order_id})

@app.route('/api/add-product', methods=['POST'])
def add_product():
    if 'user' not in session or session['user']['type'] != 'seller':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    price = float(data.get('price', 0))
    stock = int(data.get('stock', 0))
    category = data.get('category')
    
    if not name or price <= 0 or stock < 0:
        return jsonify({'success': False, 'message': 'Invalid product data'}), 400
    
    new_product = {
        "id": max(p['id'] for p in products) + 1,
        "name": name,
        "price": price,
        "description": description,
        "rating": 0,
        "sellerId": session['user']['id'],
        "sellerName": session['user']['name'],
        "category": category,
        "image": f"https://picsum.photos/250/180/?random={random.randint(1, 1000)}",
        "stock": stock
    }
    
    products.append(new_product)
    return jsonify({'success': True, 'product': new_product})

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    data = request.get_json()
    rating = int(data.get('rating', 5))
    feedback = data.get('feedback', '')
    
    # In a real app, save this to a database
    return jsonify({'success': True, 'showReplacement': rating <= 2})

@app.route('/api/replacement', methods=['POST'])
def request_replacement():
    data = request.get_json()
    reason = data.get('reason')
    details = data.get('details', '')
    
    # In a real app, save this to a database
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)