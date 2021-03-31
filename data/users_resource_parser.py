from flask_restful import reqparse

parser = reqparse.RequestParser()
parser.add_argument('nickname', required=True, type=str)
parser.add_argument('email', required=True, type=str)
parser.add_argument('hashed_password', required=True, type=str)