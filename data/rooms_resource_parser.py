from flask_restful import reqparse

parser = reqparse.RequestParser()
parser.add_argument('title', required=True, type=str)
parser.add_argument('creator', required=True, type=int)
parser.add_argument('players', required=True, type=str)
parser.add_argument('status', required=True, type=int)

