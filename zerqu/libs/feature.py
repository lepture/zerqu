
from flask import current_app
from werkzeug.utils import import_string

__all__ =['FeatureError', 'process']


class FeatureError(Exception):
    pass


def process_link(value, topic):
    # TODO: validate link value
    topic.info = {
        'type': 'link',
        'value': value
    }
    if not topic.link:
        topic.link = value


def process_image(value, topic):
    topic.info = {
        'type': 'image',
        'value': value
    }


def process_video(value, topic):
    topic.info = {
        'type': 'video',
        'value': value
    }


def process_audio(value, topic):
    topic.info = {
        'type': 'audio',
        'value': value
    }


SUPPORTED_PROCESSORS = {
    'link': process_link,
    'image': process_image,
}


def process(feature_type, feature_value, topic):
    processors = current_app.config.get('ZERQU_FEATURE_PROCESSORS')

    # use custom processors
    module = processors.get(feature_type)
    if module:
        func = import_string(module)
        return func(feature_value, topic)

    func = SUPPORTED_PROCESSORS.get(feature_type)
    if not func:
        raise FeatureError('Invalid feature_type')

    return func(feature_type, topic)
