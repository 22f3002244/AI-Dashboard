from flask import Flask
from routes.routes import main
from routes.ai import ai
from models.database import db
import os
from dotenv import load_dotenv  

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///app.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()
    app.register_blueprint(main)
    app.register_blueprint(ai)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)