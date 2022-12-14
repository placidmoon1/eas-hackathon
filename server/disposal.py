from flask import Flask, render_template, Blueprint, request
import pyrebase
import time
import requests

from config import config, user_types
from auth import check_token
from incentives import i_portions


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
  multiplier = float(params["multiplier"])

  #customer_id can be both registered & temp id
  customer_id = params["customer_id"] 

  #get information about the item
  item_info = db.child("items").child(item_id).get().val()
  factory_id = item_info["factory_id"]

  if (int(item_info["incentive_status"]) == 1):
    return {"status": "item already claimed & incentivized"}, 403

  #update item status
  db.child("items").child(item_id).update({
    "item_location": disposal_id,
    "incentive_status": 1
  })

  c_incen = INCENTIVE_AMOUNT * multiplier * i_portions["customer"]
  f_incen = INCENTIVE_AMOUNT * i_portions["factory"]
  d_incen = INCENTIVE_AMOUNT * i_portions["disposal"]
  lo_incen = INCENTIVE_AMOUNT * i_portions["lottery"]
  le_incen = INCENTIVE_AMOUNT * i_portions["leaderboard"]

  #multiplier is 0.7 ~ 1.05 (70% to 105%)
  #depending on the multiplie, our total gain is 0.75 ~ 2.5 out of 10
  fc_delta = INCENTIVE_AMOUNT * (1 - multiplier) * i_portions["customer"]
  fc_incen = INCENTIVE_AMOUNT * i_portions["FullCycle"] + fc_delta

  #give incentives to customer, factory, disposal, and FullCycle
  ##0.5 to customer
  db.child("incentives").push({
    "product_id": item_info["product_id"],
    "item_id": item_info["item_id"],
    "customer_id": customer_id,
    "disposal_id": disposal_id,
    "factory_id": factory_id,
    "incentive_amount": [c_incen, f_incen, d_incen, fc_incen, lo_incen, le_incen],
    "c_incen_left": c_incen,
    "f_incen_left": f_incen,
    "d_incen_left": d_incen,
    "fc_incen_left": fc_incen,
    "lo_incen_left": lo_incen,
    "le_incen_left": le_incen,
    "timestamp": int(time.time()),
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