from flask import Flask, render_template, Blueprint, request
import pyrebase
import requests

from config import config, user_types

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()
storage = firebase.storage()

bp = Blueprint("incentives", __name__, url_prefix="/incentives")