from flask_restful import reqparse

parser = reqparse.RequestParser()
parser.add_argument('creator_id', required=True, type=int)
parser.add_argument('text', required=True, type=str)
parser.add_argument('image_address', required=True, type=str)