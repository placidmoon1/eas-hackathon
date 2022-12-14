from flask import Flask, render_template, Blueprint, request
import pyrebase
import requests

from config import config, user_types
from auth import check_token

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()
storage = firebase.storage()

bp = Blueprint("customer", __name__, url_prefix="/customer")

@bp.route("/item/ownership", methods=["POST"])
def item_ownership():
  u_token = request.headers.get("Authorization")
  customer_id = check_token(u_token)['localId']

  params = request.get_json()
  item_id = params["item_id"]  

  #update item status
  db.child("items").child(item_id).update({
    "item_location": customer_id
  })
  
  return {"status": "post success"}

@bp.route("/get/item-list")
def get_user_item_list():
  u_token = request.headers.get("Authorization")
  customer_id = check_token(u_token)['localId']

  c_ilist = db.child("items").order_by_child("item_location").equal_to(customer_id).get().val()
  if c_ilist == []:
    return {}, 200

  return c_ilist, 200