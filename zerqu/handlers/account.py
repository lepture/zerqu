# coding: utf-8

from flask import Blueprint

bp = Blueprint('account', __name__)


@bp.route('', methods=['POST'])
def request_change_password():
    pass


@bp.route('/-/<token>', methods=['GET', 'POST'])
def change_password(token):
    pass


def create_signature(email):
    # save email to redis
    return


def verify_signature(token):
    # verify in redis
    return True


def destroy_signature(token):
    # remove from redis
    pass
