from flask import Blueprint, request, jsonify, session
from ..models.product import Product
from ..models.order import Order

cart_bp = Blueprint('cart', __name__)

@cart_bp.route('/cart', methods=['GET'])
def view_cart():
    cart_items = session.get('cart', {})
    return jsonify(cart_items)

@cart_bp.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    cart_items = session.get('cart', {})
    cart_items[product_id] = cart_items.get(product_id, 0) + 1
    session['cart'] = cart_items
    return jsonify(cart_items)

@cart_bp.route('/cart/remove/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    cart_items = session.get('cart', {})
    if product_id in cart_items:
        del cart_items[product_id]
    session['cart'] = cart_items
    return jsonify(cart_items)