from flask import Flask, render_template, Blueprint, request
import pyrebase
import requests

from config import config, user_types
from auth import check_token


i_portions = {
  "customer": 0.5,
  "lottery": 0.1,
  "leaderboard": 0.1,
  "disposal": 0.1,
  "factory": 0.1,
  "FullCycle": 0.1
}

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()
storage = firebase.storage()

bp = Blueprint("incentives", __name__, url_prefix="/incentives")

@bp.route("/get", methods=["GET"])
def get_incentives():
  u_token = request.headers.get("Authorization")
  c_token = check_token(u_token)
  if c_token == "invalid token":
    return {"status": "Invalid token"}, 404
  
  account_type = request.args.get("account_type")
  unique_id = c_token['localId']

  incentive_list = db.child("incentives").order_by_child(account_type).equal_to(unique_id).get().val()
  if incentive_list == [] or incentive_list is None:
    return {}, 200
  
  print(incentive_list)

  return incentive_list, 200