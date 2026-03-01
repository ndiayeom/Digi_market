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

def check_fields(body, fields):
    required_parameters_set = set(fields)
    fields_set = set(body.keys())
    return required_parameters_set <= fields_set
