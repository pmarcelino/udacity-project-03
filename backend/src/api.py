import os
import sys
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink, db
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

with app.app_context():
    db_drop_and_create_all()

# ROUTES


@app.route("/drinks")
def get_drinks():
    drinks = Drink.query.all()

    drinks = [drink.short() for drink in drinks]

    return (jsonify({"success": True,
                     "drinks": drinks}), 200)


@app.route("/drinks-detail")
@requires_auth("get:drinks-detail")
def get_drinks_detail(payload):
    drinks = Drink.query.all()

    drinks = [drink.long() for drink in drinks]

    return (jsonify({"success": True,
                     "drinks": drinks}), 200)


@app.route("/drinks", methods=["POST"])
@requires_auth("post:drinks")
def post_drinks(payload):

    body = request.get_json()
    title = body.get("title", None)
    recipe = body.get("recipe", None)
    recipe = str(json.dumps(recipe))

    if "" in (title, recipe):
        abort(422)

    try:
        new_drink = Drink(title, recipe)
        new_drink.insert()
    except BaseException:
        print(sys.exc_info())
        db.session.rollback()
        abort(500)
    finally:
        db.session.close()

    return (jsonify({"success": True,
                     "drinks": [{"title": title,
                                 "recipe": recipe}]}), 200)


@app.route("/drinks/<int:drink_id>", methods=["PATCH"])
@requires_auth("patch:drinks")
def update_drinks(payload, drink_id):

    drink = Drink.query.filter_by(id=drink_id).one_or_none()

    if drink is None:
        abort(404)

    body = request.get_json()
    title = body.get("title", None)
    recipe = body.get("recipe", None)
    recipe = str(json.dumps(recipe))

    try:
        drink.title = title
        drink.recipe = recipe
        drink.update()
    except BaseException:
        print(sys.exc_info())
        db.session.rollback()
        abort(500)
    finally:
        db.session.close()

    return (jsonify({"success": True,
                     "drinks": [{"title": title,
                                 "recipe": recipe}]}), 200)


@app.route("/drinks/<int:drink_id>", methods=["DELETE"])
@requires_auth("delete:drinks")
def delete_drinks(payload, drink_id):

    drink = Drink.query.filter_by(id=drink_id).one_or_none()

    if drink is None:
        abort(404)

    try:
        drink.delete()
    except BaseException:
        db.session.rollback()
        abort(500)
    finally:
        db.session.close()

    return (jsonify({"success": True,
                     "delete": drink_id}), 200)


# Error Handling
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(404)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": "resource_not_found",
        "message": "Resource not found."
    }), 404


@app.errorhandler(500)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": "internal_server_error",
        "message": "Internal server error."
    }), 500


@app.errorhandler(AuthError)
def unprocessable(ex):
    return jsonify({
        "success": False,
        "error": ex.error["code"],
        "message": ex.error["description"]
    }), ex.status_code
