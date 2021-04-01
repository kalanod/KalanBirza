from data import db_session
from data.rooms import Rooms
from flask_restful import reqparse, abort, Api, Resource
from flask import jsonify
from data.rooms_resource_parser import parser


def abort_if_rooms_not_found(rooms_id):
    session = db_session.create_session()
    rooms = session.query(Rooms).get(rooms_id)
    if not rooms:
        abort(404, message=f"Rooms {rooms_id} not found")


class RoomsResource(Resource):
    def get(self, rooms_id):
        abort_if_rooms_not_found(rooms_id)
        session = db_session.create_session()
        rooms = session.query(Rooms).get(rooms_id)
        return jsonify({'rooms': rooms.to_dict(only=('id',
                                                     'title',
                                                     'creator',
                                                     'players',
                                                     'status'))})

    def delete(self, rooms_id):
        abort_if_rooms_not_found(rooms_id)
        session = db_session.create_session()
        rooms = session.query(Rooms).get(rooms_id)
        session.delete(rooms)
        session.commit()
        return jsonify({'success': 'OK'})


class RoomsListResource(Resource):
    def get(self):
        session = db_session.create_session()
        rooms = session.query(Rooms).all()
        return jsonify(
            {
                'rooms':
                    [item.to_dict(only=('id',
                                        'title',
                                        'creator',
                                        'players',
                                        'status'))
                     for item in rooms]
            }
        )

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()
        rooms = Rooms(
            title=args['title'],
            creator=args['creator'],
            players=args['players'],
            status=args['status']
        )
        session.add(rooms)
        session.commit()
        return jsonify({'success': 'OK'})