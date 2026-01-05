from flask import Flask
from routes import main
from models.database import db

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-secret"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()
    app.register_blueprint(main)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)