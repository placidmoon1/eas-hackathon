from flask import Flask, render_template, Blueprint, request
import pyrebase
import requests

from config import config, user_types
from auth import check_token

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()
storage = firebase.storage()

INCENTIVE_AMOUNT = 10

bp = Blueprint("disposal", __name__, url_prefix="/disposal")

@bp.route("/user/incentivize", methods=["POST"])
def item_incentivize():
  u_token = request.headers.get("Authorization")
  disposal_id = check_token(u_token)['localId']

  params = request.get_json()
  item_id = params["item_id"] 
  
  #customer_id can be both registered & temp id
  customer_id = params["customer_id"] 

  #get information about the item
  item_info = db.child("items").child(item_id).get().val()

  if (int(item_info["incentive_status"]) == 1):
    return {"status": "item already claimed & incentivized"}, 403

  #update item status
  db.child("items").child(item_id).update({
    "item_location": disposal_id,
    "incentive_status": 1
  })

  #give incentives
  db.child("incentives").child(customer_id).push({
    "product_id": item_info["product_id"],
    "item_id": item_info["item_id"],
    "customer_id": customer_id,
    "disposal_id": disposal_id,
    "incentive_amount": INCENTIVE_AMOUNT,
    "incentive_used": 0
  })
  
  return {"status": "post success"}, 200

@bp.route("/temp/create", methods=["POST"])
def create_user_qr():
  #assign temp id
  temp_id = "userqr_" + db.generate_key()
  db.child("userqr").child(temp_id).set({
    "temp_id": temp_id
  })

  return {"status": "qr creation success", "userqr": temp_id}, 200