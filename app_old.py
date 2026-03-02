from flask import Flask, request, jsonify

app = Flask(__name__)

cart = []

@app.route('/')
def hello_world():
    return "Coucou !"

@app.route('/cart', methods=['GET'])
def list_cart():
    return jsonify(cart), 200

@app.route('/cart', methods=['POST'])
def add_to_cart():
    try:
        body = request.get_json()
        if not check_fields(body, {'id', 'quantity'}):
            return jsonify({'error': "Missing fields"}), 400

        for i, item in enumerate(cart):
            if item['id'] == body['id']:
                cart[i]['quantity'] += int(body['quantity'])
                return jsonify({}), 200
        
        cart.append(body)
        return jsonify({}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def check_fields(body, fields):
    # on recupere les champs requis au format 'ensemble'
    required_parameters_set = set(fields)

    # on recupere les champs du corps de la requête au format 'ensemble'abs
    fields_set = set(body.keys())

    # si 'l'ensemble des champs requis n'est pas inclu dans l'ensemble des champs du corps
    # alors q'il manque des paramètres et de la valeur False sera renvoyée
    return required_parameters_set <= fields_set


@app.route('/cart', methods=['PATCH'])
def edit_cart():
    try:
        body = request.get_json()
        if not check_fields(body, {'id', 'quantity'}):
            return jsonify({'error': "Missing fields"}), 400

        for i, item in enumerate(cart):
            if item['id'] == body['id']:
                cart[i]['quantity'] = int(body['quantity'])
                return jsonify({}), 200
        
        return jsonify({'error': "Product not found."}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/cart', methods=['DELETE'])
def remove_from_cart():
    try:
        body = request.get_json()
        if not check_fields(body, {'id'}):
            return jsonify({'error': "Missing fields"}), 400

        for i, item in enumerate(cart):
            if item['id'] == body['id']:
               del cart[i]
               return jsonify({}), 200
        
        return jsonify({'error': "Product not found."}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500