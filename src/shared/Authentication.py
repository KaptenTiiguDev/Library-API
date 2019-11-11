# Faili nimi peaks olema authentication (PEP-8)
import jwt
import os
import datetime
from flask import json, Response, request, g
from functools import wraps
from ..models.UserModel import UserModel


'''
Siin failis on mitmel korral välja kutsutud Response tagastamine,kus mitmed parameetrid korduvad, et selle võiks eraldada
eraldi meetodisse
'''

class Auth:
    """Auth Class"""

    @staticmethod
    def generate_token(user_id):
        """Generate Token"""
        try:
            payload = {
                "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1),
                "iat": datetime.datetime.utcnow(),
                "sub": user_id,
            }
            return jwt.encode(payload, os.getenv("JWT_SECRET_KEY"), "HS256") \
                      .decode("utf-8")
        except Exception as e:
            return Response(
                mimetype="application/json",
                response=json.dumps({"error": "error in generating token"}),
                status=400,
            )

    @staticmethod
    def decode_token(token):
        """Decode token"""
        re = {"data": {}, "error": {}}
        try:
            payload = jwt.decode(token, os.getenv("JWT_SECRET_KEY"))
            re["data"] = {"user_id": payload["sub"]}
            return re
        except jwt.ExpiredSignatureError as e1:
            re["error"] = {"message": "token expired, please login again"}
            return re
        except jwt.InvalidTokenError:
            re["error"] = {
                "message": "Invalid token, please try again with a new token"
            }
            return re

    @staticmethod
    def auth_required(func):
        """Auth decorator"""

        @wraps(func)
        def decorated_auth(*args, **kwargs):
            auth_header = request.headers.get("Authorization")
            if auth_header:
                token = auth_header.split(" ")[1]
            else:
                token = None

            if not token:
                return Response(
                    mimetype="application/json",
                    response=json.dumps(
                        {
                            "error": "Authentication token is not available, \
                            please login to get one"
                        }
                    ),
                    status=400,
                )
            data = Auth.decode_token(token)
            if data["error"]:
                return Response(
                    mimetype="application/json",
                    response=json.dumps(data["error"]),
                    status=400,
                )

            user_id = data["data"]["user_id"]
            check_user = UserModel.get_one_user(user_id)
            if not check_user:
                return Response(
                    mimetype="application/json",
                    response=json.dumps(
                        {"error": "user does not exist, invalid token"}
                    ),
                    status=400,
                )
            g.user = {"id": user_id}
            return func(*args, **kwargs)

        return decorated_auth
