from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from extensions import mongo

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def home():
    if "user" in session:
        return redirect(url_for("main.shop"))
    return render_template("home.html")

@main_bp.route("/shop")
def shop():
    if "user" not in session:
        return redirect(url_for("auth.login"))
        
    search_query = request.args.get("q", "").lower()
    category_filter = request.args.get("category", "")
    
    query = {}
    if category_filter:
        query["category"] = category_filter
        
    filtered_products = list(mongo.db.products.find(query, {"_id": 0}))
    
    if search_query:
        filtered_products = [p for p in filtered_products if search_query in p["name"].lower() or search_query in p["description"].lower()]
        
    categories = mongo.db.products.distinct("category")
    
    wishlist_ids = [w["product_id"] for w in mongo.db.wishlist.find({"user": session.get("user")})]
        
    return render_template("shop.html", products=filtered_products, categories=categories, current_category=category_filter, search_query=search_query, wishlist_ids=wishlist_ids)

@main_bp.route("/product/<int:pid>")
def product(pid):
    if "user" not in session:
        return redirect(url_for("auth.login"))
        
    prod = mongo.db.products.find_one({"id": pid})
    if not prod:
        flash("Product not found.", "danger")
        return redirect(url_for("main.shop"))
        
    wishlist_ids = [w["product_id"] for w in mongo.db.wishlist.find({"user": session.get("user")})]
    is_wishlisted = pid in wishlist_ids
        
    return render_template("product.html", product=prod, is_wishlisted=is_wishlisted)

@main_bp.route("/wishlist")
def wishlist():
    if "user" not in session:
        return redirect(url_for("auth.login"))
    
    w_items = mongo.db.wishlist.find({"user": session.get("user")})
    product_ids = [w["product_id"] for w in w_items]
    
    products = list(mongo.db.products.find({"id": {"$in": product_ids}}))
    return render_template("wishlist.html", products=products)

@main_bp.route("/add_wishlist/<int:pid>")
def add_wishlist(pid):
    if "user" not in session:
        return redirect(url_for("auth.login"))
        
    existing = mongo.db.wishlist.find_one({"user": session.get("user"), "product_id": pid})
    if not existing:
        mongo.db.wishlist.insert_one({"user": session.get("user"), "product_id": pid})
        flash("Added to wishlist <i class='bi bi-heart-fill pe-1'></i>", "success")
    else:
        mongo.db.wishlist.delete_one({"user": session.get("user"), "product_id": pid})
        flash("Removed from wishlist", "info")
        
    return redirect(request.referrer or url_for("main.shop"))

@main_bp.route("/profile")
def profile():
    if "user" not in session:
        return redirect(url_for("auth.login"))
        
    user_email = session.get("user")
    orders = list(mongo.db.orders.find({"user": user_email}))
    
    enriched_orders = []
    for order in orders:
        product_ids = [i["product_id"] for i in order["items"]]
        products_cursor = mongo.db.products.find({"id": {"$in": product_ids}})
        product_map = {p["id"]: p for p in products_cursor}
        
        enriched_items = []
        for item in order["items"]:
            product = product_map.get(item["product_id"])
            if product:
                enriched_items.append({
                    "name": product["name"],
                    "price": product["price"],
                    "quantity": item.get("quantity", 1)
                })
        order["enriched_items"] = enriched_items
        enriched_orders.append(order)
        
    return render_template("profile.html", user_email=user_email, orders=enriched_orders)
