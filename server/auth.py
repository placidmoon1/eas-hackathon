from flask import Flask, render_template, Blueprint, request, session, redirect, url_for, g
import pyrebase
import requests

from config import config, user_types

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()
storage = firebase.storage()

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.before_app_request
def load_logged_in_user():
  user_id = session.get('user_id')
  if user_id is None:  
    g.user = None

  decoded = check_token(user_id) #localId
  if decoded == "invalid token":
    g.user = None
  else: 
    #print(decoded)
    localId = decoded["localId"]
    g.user = db.child("users").child(localId).get().val()

def check_token(token):
  try:
    decoded_token = auth.get_account_info(token)
    return (decoded_token["users"][0])
  except:
    return "invalid token"

@bp.route("/register", methods=["GET"])
def register_page():
  return render_template("auth/register.html")

@bp.route('/logout')
def logout():
  session.clear()
  return redirect(url_for('auth.login_user'))

@bp.route("/register", methods=["POST"])
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

  session.clear()
  session['user_id'] = user['idToken']

  if(u_type== "customer"):
    return redirect(url_for("customer.get_customer_home"))
  if(u_type == "disposal"):
    return redirect(url_for("disposal.get_disposal_home"))
  if(u_type == "factory"):
    return redirect(url_for("factory.get_factory_home"))
  
  #else, wrong type
  session.clear()
  return render_template("auth/register.html")

@bp.route("/login", methods=["GET"])
def login_page():
  if g.user is not None:
    u_type = g.user["u_type"]
    if(u_type== "customer"):
      return redirect(url_for("customer.get_customer_home"))
    if(u_type == "disposal"):
      return redirect(url_for("disposal.get_disposal_home"))
    if(u_type == "factory"):
      return redirect(url_for("factory.get_factory_home"))
  return render_template("auth/login.html")

@bp.route("/login", methods=["POST"])
def login_user():
  #params = request.get_json()
  email = request.form["email"]
  password = request.form["password"]
  try:
    user = auth.sign_in_with_email_and_password(email, password)
  except:
    return "invalid email or pw", 200
  session.clear()
  session['user_id'] = user['idToken']
  user_info = db.child("users").child(user['localId']).get().val()

  if(user_info["u_type"] == "customer"):
    return redirect(url_for("customer.get_customer_home"))
  if(user_info["u_type"] == "disposal"):
    return redirect(url_for("disposal.get_disposal_home"))
  if(user_info["u_type"] == "factory"):
    return redirect(url_for("factory.get_factory_home"))
  
  #else, wrong type
  session.clear()
  return render_template("auth/login.html")

@bp.route("/user/myself", methods=["GET"])
def get_my_info():
  u_token = request.headers.get("Authorization")
  decoded = check_token(u_token) #localId
  if decoded == "invalid token":
    return {"status": "Invalid token"}, 200
  u_id = decoded["localId"]
  data = db.child("users").child(u_id).get().val()
  if data is None:
      return {
          "error": "User not found. Account data possibly corrupted."
      }, 500
  return data, 200
