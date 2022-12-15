from flask import Flask, render_template, Blueprint, request, session, redirect, url_for, g
import pyrebase
import requests
import functools
import time

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

@bp.route("/register_item", methods=["GET"])
@f_login_required
def register_item():
  u_token = session['user_id'] 
  user_data = check_token(u_token)
  if user_data == "invalid token":
    g.user = None
    session.clear()
    return redirect(url_for('auth.login_user'))

  factory_id = user_data['localId']

  products =  db.child("products").order_by_child("factory_id").equal_to(factory_id).get().val()
  if products == []:
    products = {}
  
  print(products.items())
  
  return render_template("factory/register_item.html", products=products.items(), item_id="ITEM_NEED_TO_BE_REGISTERED_FIRST!")


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

  status = product_name + " registered."

  return render_template("factory/factory_home.html", status=status)

@bp.route("/record/item", methods=["POST"])
@f_login_required
def record_item():
  u_token = session['user_id'] 
  user_data = check_token(u_token)
  if user_data == "invalid token":
    g.user = None
    session.clear()
    return redirect(url_for('auth.login_user'))

  factory_id = user_data['localId']
  product_id = request.form["product_id"] 
  number_items = int(request.form["number_items"])

  for i in range(number_items):
    item_id = product_id + "-i" + db.generate_key()
    db.child("items").child(item_id).set({
      "timestamp": int(time.time()),
      "product_id": product_id,     # FK
      "factory_id": factory_id,     # FK
      "item_id": item_id,           # PK (w other 2 FKs)
      "item_location": factory_id,
      "scanned": 0,
      "incentive_status": 0         #not yet used (0) | used (1)
    })

  description = str(number_items) + " items created for " + item_id

  return render_template("factory/factory_home.html", status=description)

@bp.route("/get/plist", methods=["GET"])
@f_login_required
def get_product_list():
  u_token = session['user_id'] 
  user_data = check_token(u_token)
  if user_data == "invalid token":
    g.user = None
    session.clear()
    return redirect(url_for('auth.login_user'))

  factory_id = user_data['localId']  
  f_plist = db.child("products").order_by_child("factory_id").equal_to(factory_id).get().val()
  
  if f_plist == []:
    f_plist = {}

  return render_template("factory/factory_products.html", plist=f_plist.items())

@bp.route("/get/ilist/<pid>", methods=["GET"])
@f_login_required
def get_item_list(pid):

  p_itemlist = db.child("items").order_by_child("product_id").equal_to(pid).get().val()
  product_name = db.child("products").child(pid).get().val()["product_name"].replace(' ', '_')
  
  if p_itemlist == []:
    p_itemlist = {}

  return render_template("factory/factory_items.html", 
    ilist=p_itemlist.items(),
    product_name=product_name)

@bp.route("/get/incen_list", methods=["GET"])
@f_login_required
def get_incen_list():
  u_token = session['user_id'] 
  user_data = check_token(u_token)
  if user_data == "invalid token":
    g.user = None
    session.clear()
    return redirect(url_for('auth.login_user'))

  factory_id = user_data['localId']  
  incen_list = db.child("incentives").order_by_child("factory_id").equal_to(factory_id).get().val()
  
  if incen_list == []:
    incen_list = {}

  return render_template("factory/factory_incentives.html", 
    incen_list=incen_list.items())

@bp.route("/patch/item/scan", methods=["PATCH"])
@f_login_required
def patch_scan_status():
  params = request.get_json()
  iid = params["item_id"]  
  db.child("items").child(iid).update({
    "scanned": 1
  })
  
  return {"status": "ok"}, 200