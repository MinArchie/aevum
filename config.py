import os

class Config:
    SECRET_KEY = os.urandom(24)
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static/uploads')
    DATABASE = os.path.join(os.getcwd(), 'instance', 'social_network.sqlite')
