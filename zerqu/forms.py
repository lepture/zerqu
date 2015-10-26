# coding: utf-8

import hashlib

from flask import request
from flask_wtf import Form as BaseForm
from flask_oauthlib.utils import to_bytes
from wtforms.fields import StringField, PasswordField
from wtforms.fields import TextAreaField, IntegerField
from wtforms.validators import DataRequired, Optional
from wtforms.validators import Email, Length, Regexp, URL
from wtforms.validators import StopValidation
from werkzeug.datastructures import MultiDict
from zerqu.libs.errors import FormError
from zerqu.libs.cache import cache
from zerqu.models import db, User, Cafe, Comment, Topic


class Form(BaseForm):
    @classmethod
    def create_api_form(cls, obj=None):
        formdata = MultiDict(request.get_json())
        form = cls(formdata=formdata, obj=obj, csrf_enabled=False)
        form._obj = obj
        if not form.validate():
            raise FormError(form)
        return form

    def _validate_obj(self, key, value):
        obj = getattr(self, '_obj', None)
        return obj and getattr(obj, key) == value


class UserForm(Form):
    username = StringField(validators=[
        DataRequired(),
        Length(min=3, max=20),
        Regexp(r'^[a-z0-9]+$'),
    ])
    password = PasswordField(validators=[DataRequired()])


class PasswordForm(Form):
    password = PasswordField(validators=[DataRequired()])


class FindPasswordForm(Form):
    username = StringField('Username or Email', validators=[DataRequired()])

    def validate_username(self, field):
        username = field.data
        if '@' in username:
            user = User.cache.filter_first(email=username)
        else:
            user = User.cache.filter_first(username=username)

        if not user:
            raise StopValidation('User not found.')

        self.user = user


class LoginForm(PasswordForm):
    username = StringField('Username or Email', validators=[DataRequired()])

    def validate_password(self, field):
        username = self.username.data
        if '@' in username:
            user = User.cache.filter_first(email=username)
        else:
            user = User.cache.filter_first(username=username)

        if not user or not user.check_password(field.data):
            raise StopValidation('Invalid account or password')

        self.user = user


class EmailForm(Form):
    email = StringField(validators=[DataRequired(), Email()])

    def validate_email(self, field):
        if User.cache.filter_first(email=field.data):
            raise StopValidation('Email has been registered.')


class UserProfileForm(Form):
    name = StringField(validators=[Length(min=0, max=24)])
    description = StringField(validators=[Length(min=0, max=280)])


class RegisterForm(UserForm, EmailForm):
    def validate_username(self, field):
        if User.cache.filter_first(username=field.data):
            raise StopValidation('Username has been registered.')

    def create_user(self):
        user = User(
            username=self.username.data,
            email=self.email.data,
        )
        user.password = self.password.data
        user.role = User.ROLE_ACTIVE
        with db.auto_commit():
            db.session.add(user)
        return user


class CafeForm(Form):
    name = StringField(validators=[
        Length(min=3, max=30),
    ])
    slug = StringField(validators=[
        Length(min=3, max=30),
        Regexp(r'^[a-z0-9\-]{3,30}$')
    ])
    description = TextAreaField(validators=[Length(max=180)])
    permission = StringField()

    cover = StringField(validators=[Optional(), URL()])
    color = StringField(validators=[
        Optional(),
        Regexp(r'^#[a-f0-9]{6}$'),
    ])
    logo = StringField(validators=[Optional(), URL()])

    @property
    def style(self):
        return {
            'color': self.color.data,
            'cover': self.cover.data,
            'logo': self.logo.data,
        }

    def validate_slug(self, field):
        if self._validate_obj('slug', field.data):
            return
        if Cafe.cache.filter_first(slug=field.data):
            raise StopValidation('Slug has been registered')

    def validate_name(self, field):
        if self._validate_obj('name', field.data):
            return
        if Cafe.cache.filter_first(name=field.data):
            raise StopValidation('Name has been registered')

    def validate_permission(self, field):
        obj = getattr(self, '_obj', None)

        if not obj and field.data not in Cafe.PERMISSIONS:
            raise StopValidation('Invalid choice for permission')

    def create_cafe(self, user_id):
        cafe = Cafe(
            name=self.name.data,
            slug=self.slug.data,
            description=self.description.data,
            permission=Cafe.PERMISSIONS[self.permission.data],
            user_id=user_id,
            style=self.style,
        )
        with db.auto_commit():
            db.session.add(cafe)
        return cafe

    def update_cafe(self, cafe, user_id):
        keys = ['name', 'description']
        # Only owner can change slug
        if user_id == cafe.user_id:
            keys.append('slug')

        for k in keys:
            value = self.data.get(k)
            if value:
                setattr(cafe, k, value)

        cafe.style = self.style
        if self.permission.data:
            cafe.permission = Cafe.PERMISSIONS[self.permission.data]
        with db.auto_commit():
            db.session.add(cafe)
        return cafe


class TopicForm(Form):
    title = StringField(validators=[DataRequired()])
    link = StringField(validators=[Optional(), URL()])
    content = TextAreaField()

    def validate_title(self, field):
        data = u'%s%s' % (field.data, self.content.data)
        key = hashlib.md5(to_bytes(data)).hexdigest()
        if cache.get(key):
            raise StopValidation("Duplicate requesting")
        # avoid duplicate requesting
        cache.set(key, 1, 100)

    def create_topic(self, user_id):
        topic = Topic(
            title=self.title.data,
            content=self.content.data,
            user_id=user_id,
            link=self.link.data,
        )
        with db.auto_commit():
            db.session.add(topic)
        return topic

    def update_topic(self, user_id):
        topic = getattr(self, '_obj')
        topic.title = self.title.data
        topic.content = self.content.data
        topic.update_link(self.link.data, user_id)
        with db.auto_commit():
            db.session.add(topic)
        return topic


class CommentForm(Form):
    reply_to = IntegerField()
    content = TextAreaField()

    def validate_content(self, field):
        key = hashlib.md5(to_bytes(field.data)).hexdigest()
        if cache.get(key):
            raise StopValidation("Duplicate requesting")
        # avoid duplicate requesting
        cache.set(key, 1, 100)

    def create_comment(self, user_id, topic_id):
        c = Comment(
            content=self.content.data,
            topic_id=topic_id,
            user_id=user_id,
            reply_to=self.reply_to.data
        )

        with db.auto_commit():
            db.session.add(c)

        return c
