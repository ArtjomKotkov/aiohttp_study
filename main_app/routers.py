from .views import main_view

def setup_routers(app):
    app.router.add_get('/', main_view)