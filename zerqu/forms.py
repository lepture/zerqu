# coding: utf-8

import hashlib
from flask import request
from werkzeug.datastructures import MultiDict
from flask_wtf import Form as BaseForm
from flask_wtf.recaptcha import RecaptchaField
from wtforms.fields import StringField, PasswordField
from wtforms.fields import TextAreaField
from wtforms.validators import DataRequired, Email
from wtforms.validators import StopValidation
from .models import db, cache
from .models import User, Cafe, Comment, Topic
from .errors import FormError


class Form(BaseForm):
    @classmethod
    def create_api_form(cls, obj=None):
        form = cls(MultiDict(request.get_json()), obj=obj, csrf_enabled=False)
        form._obj = obj
        if not form.validate():
            raise FormError(form)
        return form

    def _validate_obj(self, key, value):
        obj = getattr(self, '_obj', None)
        return obj and getattr(obj, key) == value


class UserForm(Form):
    username = StringField(validators=[DataRequired()])
    password = PasswordField(validators=[DataRequired()])


class UserProfileForm(Form):
    description = StringField()


class RegisterForm(UserForm):
    email = StringField(validators=[DataRequired(), Email()])

    def validate_username(self, field):
        if User.cache.filter_first(username=field.data):
            raise StopValidation('Username has been registered.')

    def validate_email(self, field):
        if User.cache.filter_first(email=field.data):
            raise StopValidation('Email has been registered.')

    def create_user(self):
        user = User(
            username=self.username.data,
            email=self.email.data,
        )
        user.password = self.password.data
        with db.auto_commit():
            db.session.add(user)
        return user


class RecaptchaForm(RegisterForm):
    recaptcha = RecaptchaField()


class CafeForm(Form):
    # TODO: validators
    name = StringField()
    slug = StringField()
    content = TextAreaField()
    permission = StringField()
    # TODO: multiple choices features

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
            content=self.content.data,
            permission=Cafe.PERMISSIONS[self.permission.data],
            user_id=user_id,
        )
        with db.auto_commit():
            db.session.add(cafe)
        return cafe

    def update_cafe(self, cafe, user_id):
        keys = ['name', 'content']
        # Only owner can change slug
        if user_id == cafe.user_id:
            keys.append('slug')

        for k in keys:
            value = self.data.get(k)
            if value:
                setattr(cafe, k, value)

        if self.permission.data:
            cafe.permission = Cafe.PERMISSIONS[self.permission.data]
        with db.auto_commit():
            db.session.add(cafe)
        return cafe


class TopicForm(Form):
    title = StringField(validators=[DataRequired()])
    link = StringField()
    content = TextAreaField()

    feature_type = StringField()
    feature_value = StringField()

    def validate_feature_type(self, field):
        pass

    def validate_feature_value(self, field):
        pass

    def validate_link(self, field):
        if not field.data:
            return

    def create_topic(self, cafe_id, user_id):
        # TODO: process feature

        if self.link.data:
            link = self.link.data
        else:
            link = None

        topic = Topic(
            title=self.title.data,
            content=self.content.data,
            link=link,
            cafe_id=cafe_id,
            user_id=user_id,
        )
        with db.auto_commit():
            db.session.add(topic)
        return topic

    def update_topic(self):
        topic = getattr(self, '_obj')
        topic.title = self.title.data
        topic.content = self.content.data
        with db.auto_commit():
            db.session.add(topic)
        return topic


class CommentForm(Form):
    content = TextAreaField()

    def validate_content(self, field):
        key = hashlib.md5(field.data).hexdigest()
        if cache.get(key):
            raise StopValidation("Duplicate requesting")
        # avoid duplicate requesting
        cache.set(key, 1, 100)

    def create_comment(self, user_id, topic_id):
        c = Comment(
            user_id=user_id,
            topic_id=topic_id,
            content=self.content.data,
        )
        with db.auto_commit():
            db.session.add(c)
        return c
