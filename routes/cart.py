from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from extensions import mongo
from bson.objectid import ObjectId

cart_bp = Blueprint('cart', __name__)

@cart_bp.route("/add_to_cart/<int:pid>")
def add_to_cart(pid):
    if "user" not in session:
        return redirect(url_for("auth.login"))
        
    user_email = session.get("user")
    
    existing_item = mongo.db.cart.find_one({"user": user_email, "product_id": pid})
    
    if existing_item:
        mongo.db.cart.update_one(
            {"_id": existing_item["_id"]},
            {"$inc": {"quantity": 1}}
        )
    else:
        product = {"product_id": pid, "user": user_email, "quantity": 1}
        mongo.db.cart.insert_one(product)
        
    flash("Item added to cart", "success")
    return redirect(url_for("cart.cart"))

@cart_bp.route("/update_cart/<cart_id>", methods=["POST"])
def update_cart(cart_id):
    if "user" not in session:
        return redirect(url_for("auth.login"))
        
    action = request.form.get("action")
    item = mongo.db.cart.find_one({"_id": ObjectId(cart_id), "user": session.get("user")})
    
    if item:
        if action == "increase":
            mongo.db.cart.update_one({"_id": ObjectId(cart_id)}, {"$inc": {"quantity": 1}})
        elif action == "decrease":
            if item.get("quantity", 1) > 1:
                mongo.db.cart.update_one({"_id": ObjectId(cart_id)}, {"$inc": {"quantity": -1}})
            else:
                mongo.db.cart.delete_one({"_id": ObjectId(cart_id)})
                
    return redirect(url_for("cart.cart"))

@cart_bp.route("/remove_from_cart/<cart_id>")
def remove_from_cart(cart_id):
    if "user" not in session:
        return redirect(url_for("auth.login"))
        
    mongo.db.cart.delete_one({"_id": ObjectId(cart_id), "user": session.get("user")})
    flash("Item removed from cart", "success")
    return redirect(url_for("cart.cart"))

@cart_bp.route("/cart")
def cart():
    if "user" not in session:
        return redirect(url_for("auth.login"))
        
    cart_items = list(mongo.db.cart.find({"user": session.get("user")}))
    
    # Pre-fetch all products referenced in cart for fast mapping
    product_ids = [i["product_id"] for i in cart_items]
    products_cursor = mongo.db.products.find({"id": {"$in": product_ids}})
    product_map = {p["id"]: p for p in products_cursor}
    
    items = []
    total_amount = 0
    
    for item in cart_items:
        product = product_map.get(item["product_id"])
        if product:
             qty = item.get("quantity", 1)
             item_total = product["price"] * qty
             items.append({
                 "cart_id": str(item["_id"]),
                 "product_id": product["id"],
                 "name": product["name"],
                 "price": product["price"],
                 "image": product["image"],
                 "quantity": qty,
                 "total": item_total
             })
             total_amount += item_total
            
    return render_template("cart.html", items=items, total_amount=total_amount)

@cart_bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    if "user" not in session:
        return redirect(url_for("auth.login"))
        
    cart_items = list(mongo.db.cart.find({"user": session.get("user")}))
    if not cart_items:
        flash("Your cart is empty.", "danger")
        return redirect(url_for("main.shop"))
        
    product_ids = [i["product_id"] for i in cart_items]
    products_cursor = mongo.db.products.find({"id": {"$in": product_ids}})
    product_map = {p["id"]: p for p in products_cursor}
    
    total_amount = sum([product_map.get(item["product_id"], {}).get("price", 0) * item.get("quantity", 1) for item in cart_items])
        
    if request.method == "POST":
        address = request.form.get("address")
        payment = request.form.get("payment")
        
        order = {
            "user": session.get("user"),
            "items": cart_items,
            "total_amount": total_amount,
            "address": address,
            "payment_method": payment,
            "status": "Confirmed"
        }
        mongo.db.orders.insert_one(order)
        mongo.db.cart.delete_many({"user": session.get("user")})
        
        flash("Order placed successfully!", "success")
        return redirect(url_for("cart.success"))
        
    return render_template("checkout.html", total_amount=total_amount)

@cart_bp.route("/success")
def success():
    if "user" not in session:
        return redirect(url_for("auth.login"))
    return render_template("success.html")
