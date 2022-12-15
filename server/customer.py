from flask import Flask, render_template, Blueprint, request, redirect, url_for, g, session
import pyrebase
import requests
import functools

from config import config, user_types
from auth import check_token

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()
storage = firebase.storage()

bp = Blueprint("customer", __name__, url_prefix="/customer")

def c_login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
          return redirect(url_for('auth.login_page'))
        elif g.user["u_type"] != "customer":
          if (g.user["u_type"] == "factory"):
            return redirect(url_for('factory.get_factory_home'))
          if (g.user["u_type"] == "disposal"):
            return redirect(url_for('disposal.get_disposal_home'))
        return view(**kwargs)
    return wrapped_view

@bp.route("/home", methods=["GET"])
@c_login_required
def get_customer_home():
  return render_template("customer/customer_home.html")

@bp.route("/register/products", methods=["GET"])
@c_login_required
def c_register_products():
  return render_template("customer/customer_register_products.html")

@bp.route("/item/ownership", methods=["PATCH"])
@c_login_required
def item_ownership():
  u_token = session['user_id'] 
  user_data = check_token(u_token)
  if user_data == "invalid token":
    g.user = None
    session.clear()
    return redirect(url_for('auth.login_user'))

  customer_id = user_data['localId']

  params = request.get_json()
  item_id = params["item_id"]  

  #update item status
  db.child("items").child(item_id).update({
    "item_location": customer_id
  })
  
  return {"status": "post success"}

@bp.route("/get/item-list",  methods=["GET"])
@c_login_required
def get_user_item_list():
  u_token = session['user_id'] 
  user_data = check_token(u_token)
  if user_data == "invalid token":
    g.user = None
    session.clear()
    return redirect(url_for('auth.login_user'))

  customer_id = user_data['localId']
  c_ilist = db.child("items").order_by_child("item_location").equal_to(customer_id).get().val()
  if c_ilist == []:
    c_ilist = {}

  return render_template("customer/customer_items.html", ilist=c_ilist.items())

@bp.route("/get/incentive/status",  methods=["GET"])
@c_login_required
def get_disposal_status():
  item_id = request.args.get('item_id')
  incentive_status = db.child("items").child(item_id).get().val()["incentive_status"]
  return {"incentive_status": incentive_status}, 200