from flask import Flask, render_template, Blueprint, request
import pyrebase
import requests

from config import config, user_types
from auth import check_token

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()
storage = firebase.storage()

bp = Blueprint("factory", __name__, url_prefix="/factory")

@bp.route("/record/product", methods=["POST"])
def record_product():
  u_token = request.headers.get("Authorization")
  factory_id = check_token(u_token)['localId']

  params = request.get_json()
  product_name = params["product_name"]
  product_id = "p" + db.generate_key()
  product_isbn = params["product_isbn"]
  product_trash = params["product_trash"]

  db.child("products").child(product_id).set({
    "product_name": product_name,
    "product_id": product_id,
    "product_isbn": product_isbn,
    "product_trash": product_trash,
    "factory_id": factory_id
  })

  return {"status": "set succes"}, 200

@bp.route("/record/item", methods=["POST"])
def record_item():
  u_token = request.headers.get("Authorization")
  factory_id = check_token(u_token)['localId']

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

  return {"status": "set succes"}, 200