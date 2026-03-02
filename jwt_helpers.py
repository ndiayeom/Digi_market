from flask import request
import jwt

from datetime import datetime, timedelta

JWT_SECRET = "d3fb12750c2eff92120742e1b334479e"

def generate_token(user):
    return jwt.encode(
        {
            "exp": datetime.utcnow() + timedelta(hours=1),
            "user": user
        },
        JWT_SECRET,
        algorithm="HS256"
    )

def decode_token(token):
    try:
        return jwt.decode(
            token,
            JWT_SECRET,
            algorithms="HS256"
        )
    except Exception:
        print("Jeton JWT invalide.")
        return
    
def require_authentication(f):
    def wrapper(**kwargs):
        token = request.headers.get("Authorization", "0")
        if not decode_token(token):
            return {"error": "Jeton d'accès invalide."}, 401
        return f(**kwargs)
    return wrapper
