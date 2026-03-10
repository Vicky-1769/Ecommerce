from flask import Flask, render_template, session
from extensions import mongo, mail
from routes import auth_bp, main_bp, cart_bp, admin_bp
from flask_dance.contrib.google import make_google_blueprint
import os
from dotenv import load_dotenv

from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

    # Single MongoDB database for all collections: users, products, cart, orders, wishlist
    app.config["MONGO_URI"] = os.environ.get("MONGO_URI", "mongodb://localhost:27017/ecommerce_db")
    
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USE_SSL"] = False
    app.config["MAIL_USERNAME"] = os.environ.get("EMAIL_USER")
    app.config["MAIL_PASSWORD"] = os.environ.get("EMAIL_PASS")
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("EMAIL_USER")
    app.config["MAIL_TIMEOUT"] = 10
    mongo.init_app(app)
    mail.init_app(app)

    # Auth via Google (Flask-Dance)
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = os.environ.get("OAUTHLIB_INSECURE_TRANSPORT", "1")
    google_bp = make_google_blueprint(
        client_id=os.environ.get("GOOGLE_OAUTH_CLIENT_ID", ""),
        client_secret=os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", ""),
        scope=["profile", "email"],
        redirect_url="/google_login"
    )

    # Register Blueprints natively pointing to internal modules
    app.register_blueprint(google_bp, url_prefix="/login")
    app.register_blueprint(auth_bp, url_prefix="")
    app.register_blueprint(main_bp, url_prefix="")
    app.register_blueprint(cart_bp, url_prefix="")
    app.register_blueprint(admin_bp, url_prefix="")

    # Proper Application Error Handling Layer
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    # Inject cart count into all templates generically
    @app.context_processor
    def inject_cart_count():
        if "user" not in session:
            return dict(cart_count=0)
        cart_items = list(mongo.db.cart.find({"user": session.get("user")}))
        count = sum([item.get("quantity", 1) for item in cart_items])
        return dict(cart_count=count)
        
    return app

app = create_app()

with app.app_context():
    # Setup Default Products on boot if missing
    DEFAULT_PRODUCTS = [
        {"id": 1, "name": "Laptop Pro", "category": "Electronics", "price": 50000, "description": "High performance laptop with 16GB RAM and 512GB SSD.", "image": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=500&auto=format&fit=crop&q=60"},
        {"id": 2, "name": "Smart Mobile", "category": "Electronics", "price": 20000, "description": "Latest 5G smartphone with immersive OLED display.", "image": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=500&auto=format&fit=crop&q=60"},
        {"id": 3, "name": "Wireless Headphones", "category": "Accessories", "price": 2000, "description": "Noise cancelling over-ear headphones with 40h battery.", "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&auto=format&fit=crop&q=60"},
        {"id": 4, "name": "Mechanical Keyboard", "category": "Accessories", "price": 4000, "description": "RGB mechanical keyboard with tactile blue switches.", "image": "https://images.unsplash.com/photo-1595225476474-87563907a212?w=500&auto=format&fit=crop&q=60"},
        {"id": 5, "name": "Gaming Mouse", "category": "Accessories", "price": 1500, "description": "Ergonomic gaming mouse with adjustable DPI and RGB.", "image": "/static/gaming_mouse.png"},
        {"id": 6, "name": "Smart Watch", "category": "Accessories", "price": 2500, "description": "Fitness tracker with heart rate monitor, waterproof.", "image": "https://images.unsplash.com/photo-1579586337278-3befd40fd17a?w=500&auto=format&fit=crop&q=60"},
        {"id": 7, "name": "4K UHD Monitor", "category": "Electronics", "price": 15000, "description": "27-inch 4K UHD monitor with HDR support.", "image": "https://images.unsplash.com/photo-1527443154391-507e9dc6c5cc?w=500&auto=format&fit=crop&q=60"},
        {"id": 8, "name": "Portable Bluetooth Speaker", "category": "Accessories", "price": 3000, "description": "Portable waterproof bluetooth speaker with deep bass.", "image": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=500&auto=format&fit=crop&q=60"},
        {"id": 9, "name": "Gaming Video Console", "category": "Electronics", "price": 45000, "description": "Next-gen gaming console with 1TB SSD and 4K support.", "image": "https://images.unsplash.com/photo-1606813907291-d86efa9b94db?w=500&auto=format&fit=crop&q=60"},
        {"id": 10, "name": "HD Webcam 1080p", "category": "Accessories", "price": 1500, "description": "HD webcam with built-in microphone for streaming.", "image": "/static/hd_webcam.png"}
    ]
    for product in DEFAULT_PRODUCTS:
        if not mongo.db.products.find_one({"id": product["id"]}):
            mongo.db.products.insert_one(product)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = (os.environ.get("FLASK_ENV") != "production")
    app.run(host="0.0.0.0", port=port, debug=debug_mode, use_reloader=False)
