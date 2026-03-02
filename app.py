# debug imports
from flask import Flask, request, jsonify
from service import *
import os
import jwt

app = Flask(__name__)
# optional: allow overriding secret via env
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret')


@app.route('/api/auth/users', methods=['GET'])
def list_list():
    # protected endpoint: requires Authorization: Bearer <token>
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith('Bearer '):
        return jsonify({'error': 'Missing or invalid Authorization header'}), 401
    token = auth.split(' ', 1)[1]
    payload = verify_access_token(token, secret=app.config.get('SECRET_KEY'))
    if not payload:
        return jsonify({'error': 'Invalid or expired token'}), 401
    return jsonify(load_users_from_db()), 200


@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        body = request.get_json()
        if not check_fields(body, {'email', 'mot_de_passe', 'nom', 'role'}):
            return jsonify({'error': "Missing fields"}), 400

        add_user_to_db(body)
        return jsonify({}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        body = request.get_json()
        if not check_fields(body, {'email', 'mot_de_passe'}):
            return jsonify({'error': "Missing fields"}), 400

        user = authenticate_user(body.get('email'), body.get('mot_de_passe'))
        if user:
            # create JWT access token and return it with the user payload
            token = create_access_token(user['id'], user.get('role'), secret=app.config.get('SECRET_KEY'))
            return jsonify({'access_token': token, 'refresh_token': create_refresh_token(user['id'], user.get('role'), secret=app.config.get('SECRET_KEY')), 'user': user}), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/refresh', methods=['POST'])
def refresh():
    try:
        body = request.get_json()
        token = None
        if body and 'refresh_token' in body:
            token = body.get('refresh_token')
        else:
            auth = request.headers.get('Authorization')
            if auth and auth.startswith('Bearer '):
                token = auth.split(' ', 1)[1]

        if not token:
            return jsonify({'error': 'Missing refresh token'}), 400

        payload = verify_refresh_token(token, secret=app.config.get('SECRET_KEY'))
        if not payload:
            return jsonify({'error': 'Invalid or expired refresh token'}), 401

        user_id = payload.get('sub')
        role = payload.get('role')
        new_access = create_access_token(user_id, role, secret=app.config.get('SECRET_KEY'))
        new_refresh = create_refresh_token(user_id, role, secret=app.config.get('SECRET_KEY'))
        return jsonify({'access_token': new_access, 'refresh_token': new_refresh}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# catalogue endpoints -------------------------------------------------------


@app.route('/api/produits', methods=['GET'])
def list_products():
    """Return full catalogue. query args:
        - categorie : filter by category (exact match)
        - q         : search term for name/description

    No authentication required; visitors and clients may browse.
    """
    try:
        categorie = request.args.get('categorie')
        search = request.args.get('q')
        products = load_products_from_db(category=categorie, search=search)
        return jsonify(products), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/produits', methods=['POST'])
def create_product():
    """Add a new product to the catalogue (admin only)."""
    # check authorization header
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith('Bearer '):
        return jsonify({'error': 'Missing or invalid Authorization header'}), 401
    token = auth.split(' ', 1)[1]
    payload = verify_access_token(token, secret=app.config.get('SECRET_KEY'))
    if not payload:
        return jsonify({'error': 'Invalid or expired token'}), 401
    # role guard
    if payload.get('role') != 'admin':
        return jsonify({'error': 'Admin privileges required'}), 403

    try:
        body = request.get_json()
        new_prod = add_product_to_db(body)
        return jsonify(new_prod), 201
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/produits/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Return a single product by id."""
    try:
        product = get_product_by_id(product_id)
        if not product:
            return jsonify({'error': 'Product not found.'}), 404
        return jsonify(product), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/produits/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Modify an existing product (admin only)."""
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith('Bearer '):
        return jsonify({'error': 'Missing or invalid Authorization header'}), 401
    token = auth.split(' ', 1)[1]
    payload = verify_access_token(token, secret=app.config.get('SECRET_KEY'))
    if not payload:
        return jsonify({'error': 'Invalid or expired token'}), 401
    if payload.get('role') != 'admin':
        return jsonify({'error': 'Admin privileges required'}), 403

    try:
        body = request.get_json()
        updated = update_product_in_db(product_id, body)
        if updated is None:
            return jsonify({'error': 'Product not found.'}), 404
        return jsonify(updated), 200
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/produits/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product (admin only)."""
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith('Bearer '):
        return jsonify({'error': 'Missing or invalid Authorization header'}), 401
    token = auth.split(' ', 1)[1]
    payload = verify_access_token(token, secret=app.config.get('SECRET_KEY'))
    if not payload:
        return jsonify({'error': 'Invalid or expired token'}), 401
    if payload.get('role') != 'admin':
        return jsonify({'error': 'Admin privileges required'}), 403

    try:
        success = delete_product_in_db(product_id)
        if not success:
            return jsonify({'error': 'Product not found.'}), 404
        return jsonify({}), 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def check_fields(body, fields):
    required_parameters_set = set(fields)
    fields_set = set(body.keys())
    return required_parameters_set <= fields_set
