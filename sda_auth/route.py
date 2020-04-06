from gevent import monkey
monkey.patch_all() # noqa

import logging
from pathlib import Path
import datetime
import sda_auth.elixir_blueprint as elixir_blueprint
import sda_auth.ega_blueprint as ega_blueprint
from gevent.pywsgi import WSGIServer
from flask import (
    Flask, render_template
)
from flask_login import LoginManager
from sda_auth.settings import SERVICE_SETTINGS as config
from sda_auth.models import EgaUser


logging.basicConfig(level=config["LOG_LEVEL"])

app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")

app.config.update({'SERVER_NAME': config['SERVER_NAME'],
                   "OIDC_REDIRECT_ENDPOINT": config["ELIXIR_REDIRECT_URI"],
                   'SECRET_KEY': config['SECRET_KEY'],
                   'PERMANENT_SESSION_LIFETIME': datetime.timedelta(seconds=60),
                   'PREFERRED_URL_SCHEME': config['URL_SCHEME'],
                   "SESSION_PERMANENT": True,
                   'DEBUG': True})

# Setup EGA Authenticator
ega_login_manager = LoginManager()
ega_login_manager.init_app(app)


@ega_login_manager.user_loader
def load_user(loaded_ega_id):
    """Load logged in user."""
    return EgaUser(ega_id=loaded_ega_id)


@app.route("/")
def index():
    """Return the index page."""
    return render_template("index.html")


def start_app(flask_app):
    """Register EGA and Elixir blueprints."""
    flask_app.register_blueprint(elixir_blueprint.elixir_bp)
    flask_app.register_blueprint(ega_blueprint.ega_bp)


def verify_exist(files):
    """Check if the given files exist."""
    for f in files:
        if Path(f).is_file():
            continue
        else:
            logging.error(f'{f} does not exist')
            exit(1)


def main():
    """Start the wsgi serving the application."""
    start_app(app)
    logging.debug(">>>>> Starting authentication server at {}:{} <<<<<".format(config["BIND_ADDRESS"], config["PORT"]))
    logging.debug(f'TLS flag is {config["ENABLE_TLS"]}')

    # Create gevent WSGI server
    if config["ENABLE_TLS"] and config["CA_CERTS"] is not None:
        verify_exist([config["CERT_FILE"], config["KEY_FILE"], config["CA_CERTS"]])
        wsgi_server = WSGIServer((config["BIND_ADDRESS"], config["PORT"]),
                                 app.wsgi_app,
                                 certfile=config["CERT_FILE"],
                                 keyfile=config["KEY_FILE"],
                                 ca_certs=config["CA_CERTS"])

    elif config["ENABLE_TLS"] and config["CA_CERTS"] is None:
        verify_exist([config["CERT_FILE"], config["KEY_FILE"]])
        wsgi_server = WSGIServer((config["BIND_ADDRESS"], config["PORT"]),
                                 app.wsgi_app,
                                 certfile=config["CERT_FILE"],
                                 keyfile=config["KEY_FILE"])

    else:
        wsgi_server = WSGIServer((config["BIND_ADDRESS"], config["PORT"]),
                                 app.wsgi_app)

    # Start gevent WSGI server
    wsgi_server.serve_forever()


if __name__ == "__main__":
    main()
