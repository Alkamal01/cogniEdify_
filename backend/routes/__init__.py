from flask import Blueprint

def register_blueprints(app):
    from .auth import auth_blueprint
    from .topics import topics_blueprint
    from .interactions import interactions_blueprint
    from .progress import progress_blueprint
    from .language import language_blueprint

    app.register_blueprint(auth_blueprint)
    app.register_blueprint(topics_blueprint)
    app.register_blueprint(interactions_blueprint)
    app.register_blueprint(progress_blueprint)
    app.register_blueprint(language_blueprint)