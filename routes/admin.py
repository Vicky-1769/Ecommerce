from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from extensions import mongo

admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/admin")
def admin():
    if session.get("user") != "admin@devstore.com":
        flash("Admin access restricted.", "danger")
        return redirect(url_for("main.home"))
    
    products = list(mongo.db.products.find())
    return render_template("admin.html", products=products)

@admin_bp.route("/admin/add_product", methods=["POST"])
def admin_add_product():
    if session.get("user") != "admin@devstore.com":
        return redirect(url_for("main.home"))
        
    max_id_prod = mongo.db.products.find_one(sort=[("id", -1)])
    new_id = (max_id_prod["id"] + 1) if max_id_prod else 1
    
    new_prod = {
        "id": new_id,
        "name": request.form.get("name"),
        "category": request.form.get("category"),
        "price": int(request.form.get("price")),
        "description": request.form.get("description"),
        "image": request.form.get("image")
    }
    mongo.db.products.insert_one(new_prod)
    flash("New Product added to catalog!", "success")
    return redirect(url_for("admin.admin"))

@admin_bp.route("/admin/delete_product/<int:pid>")
def admin_delete_product(pid):
    if session.get("user") != "admin@devstore.com":
        return redirect(url_for("main.home"))
        
    mongo.db.products.delete_one({"id": pid})
    flash("Product deleted successfully.", "info")
    return redirect(url_for("admin.admin"))
