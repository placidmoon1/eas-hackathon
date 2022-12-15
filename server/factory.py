from flask import Flask, render_template, Blueprint, request, session, redirect, url_for, g
import pyrebase
import requests
import functools

from config import config, user_types
from auth import check_token


firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()
storage = firebase.storage()

def f_login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
          return redirect(url_for('auth.login_page'))
        elif g.user["u_type"] != "factory":
          if (g.user["u_type"] == "customer"):
            return redirect(url_for('customer.get_customer_home'))
          if (g.user["u_type"] == "disposal"):
            return redirect(url_for('disposal.get_disposal_home'))
        return view(**kwargs)
    return wrapped_view

bp = Blueprint("factory", __name__, url_prefix="/factory")

@bp.route("/home", methods=["GET"])
@f_login_required
def get_factory_home():
  return render_template("factory/factory_home.html", product_name="")


@bp.route("/register_product", methods=["GET"])
@f_login_required
def register_product():
  return render_template("factory/register_product.html")

@bp.route("/record/product", methods=["POST"])
@f_login_required
def record_product():
  u_token = session['user_id'] 
  user_data = check_token(u_token)
  if user_data == "invalid token":
    g.user = None
    session.clear()
    return redirect(url_for('auth.login_user'))

  factory_id = user_data['localId']

  product_name = request.form["product_name"]
  product_id = "p" + db.generate_key()
  product_isbn = request.form["product_isbn"]
  product_trash = [word.strip() for word in request.form["product_trash"].split(',')] 

  db.child("products").child(product_id).set({
    "product_name": product_name,
    "product_id": product_id,
    "product_isbn": product_isbn,
    "product_trash": product_trash,
    "factory_id": factory_id
  })

  return render_template("factory/factory_home.html", product_name=product_name)

@bp.route("/record/item", methods=["POST"])
@f_login_required
def record_item():
  u_token = request.headers.get("Authorization")
  user_data = check_token(u_token)
  if user_data == "invalid token":
    g.user = None
    session.clear()
    return redirect(url_for('auth.login_user'))

  factory_id = user_data['localId']

  params = request.get_json()
  product_id = params["product_id"] 

  item_id = product_id + "-i" + db.generate_key()

  db.child("items").child(item_id).set({
    "product_id": product_id,     # FK
    "factory_id": factory_id,     # FK
    "item_id": item_id,           # PK (w other 2 FKs)
    "item_location": factory_id,
    "incentive_status": 0         #not yet used (0) | used (1)
  })

  return {"status": "set success"}, 200

@bp.route("/get/plist", methods=["GET"])
@f_login_required
def get_product_list():
  factory_id = request.args.get("factory_id")
  
  f_plist = db.child("products").order_by_child("factory_id").equal_to(factory_id).get().val()
  
  if f_plist == []:
    return {}, 200

  return f_plist, 200

@bp.route("/get/ilist", methods=["GET"])
@f_login_required
def get_item_list():
  product_id = request.args.get("product_id")

  p_itemlist = db.child("items").order_by_child("product_id").equal_to(product_id).get().val()
  
  if p_itemlist == []:
    return {}, 200

  return p_itemlist, 200