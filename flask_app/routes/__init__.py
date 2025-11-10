from .busz import busz_bp
from .garazs import garage_bp
from .lines import lines_bp
from .muszaki_hiba import hiba_bp
from .user import user_bp
from .market import market_bp
from .schedules import schedule_bp

def register_routes(app):
    app.register_blueprint(busz_bp)
    app.register_blueprint(garage_bp)
    app.register_blueprint(lines_bp)
    app.register_blueprint(hiba_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(market_bp)
    app.register_blueprint(schedule_bp)

