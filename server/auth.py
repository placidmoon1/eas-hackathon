from flask import Flask, render_template, Blueprint, request
import pyrebase

from config import config, user_types

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()
storage = firebase.storage()

bp = Blueprint("auth", __name__, url_prefix="/auth")

@bp.route("/register")
def register_user():
  params = request.get_json()
  name = params["name"]
  description = params["description"]
  email = params["email"]
  password = params["password"]
  u_type = params["type"] #type of user: in config.user_types
  

  # register in auth db, and provide user details 
  user = auth.create_user_with_email_and_password(email, password)
  try:
    localId = user["localId"]
  except:
    return {"status": "duplicate email"}, 403


  db.child("users").child(localId).set({
    "name": name,
    "description": description,
    "email": email,
    "u_type": u_type
  })

  #print(user)
  return {"idToken": user["idToken"]}, 200

