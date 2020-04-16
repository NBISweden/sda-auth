from flask import Blueprint, render_template, url_for, redirect, flash
from ega_authenticator import EgaAuthenticator
import sda_auth.forms as forms
import logging

ega_bp = Blueprint("ega", __name__, url_prefix="/ega")
ega_authenticator = EgaAuthenticator()

LOG = logging.getLogger("ega")
LOG.propagate = False


def login():
    """Sign in to EGA."""
    if ega_authenticator.is_logged_in():
        return redirect(url_for("ega.info"), 302)
    else:
        form = forms.EgaLoginForm()
        if form.validate_on_submit():
            LOG.debug("Login form was successfullly validated")
            if ega_authenticator.authenticate_with_ega(username=form.username.data, password=form.password.data):
                return redirect(url_for("ega.info"), 302)
            else:
                flash('Wrong username or password.')
        else:
            LOG.debug("Login form was not validated")
    return render_template('ega_login_form.html', title='EGA login', form=form)


def info():
    """Display EGA user info."""
    logged_in_user = ega_authenticator.is_logged_in()
    if logged_in_user:
        return render_template('ega_login_success.html',
                               user_name=logged_in_user.get_id(),
                               access_token=logged_in_user.get_jwt_token())
    else:
        return redirect(url_for("index"), 302)


def logout():
    """Sign out from EGA."""
    return ega_authenticator.logout_from_ega()


ega_bp.add_url_rule('/login', 'login', view_func=login, methods=['GET', 'POST'])
ega_bp.add_url_rule('/info', 'info', view_func=info)
ega_bp.add_url_rule('/logout', 'logout', view_func=logout)
