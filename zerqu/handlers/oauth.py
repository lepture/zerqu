# coding: utf-8

from flask import Blueprint
from flask import request, render_template, jsonify
from flask_wtf import Form
from wtforms.fields import HiddenField, StringField, PasswordField
from wtforms.validators import DataRequired, StopValidation
from ..models.auth import oauth, User, AuthSession


bp = Blueprint('oauth', __name__)


class OAuthForm(Form):
    scope = HiddenField()


class LoginForm(OAuthForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

    def validate_password(self, field):
        username = self.username.data
        if '@' in username:
            user = User.query.filter_by(email=username).first()
        else:
            user = User.query.filter_by(username=username).first()

        if not user.check_password(field.data):
            raise StopValidation('Invalid username or password.')
        self.user = user


@bp.route('/authorize', methods=['GET', 'POST'])
@oauth.authorize_handler
def authorize(*args, **kwargs):
    """Authorize handler for OAuth"""
    user = AuthSession.get_current_user()
    if user:
        form = OAuthForm()
    else:
        form = LoginForm()
    if form.validate_on_submit():
        if hasattr(form, 'user'):
            AuthSession.login(form.user)
        confirm = request.form.get('confirm', 'no')
        return confirm == 'yes'
    return render_template(
        'oauth_authorize.html',
        user=user, form=form, **kwargs
    )


@bp.route('/token', methods=['POST'])
@oauth.token_handler
def access_token():
    return {}


@bp.route('/revoke', methods=['POST'])
@oauth.revoke_handler
def revoke_token():
    return {}


@bp.route('/errors')
def errors():
    error = request.args.get('error', None)
    return jsonify(error=error)
