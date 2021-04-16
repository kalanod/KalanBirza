from data import db_session
from data.users import User
from flask_restful import reqparse, abort, Api, Resource
from flask import jsonify
from data.users_resource_parser import parser


def abort_if_user_not_found(user_id):
    session = db_session.create_session()
    user = session.query(User).get(user_id)
    if not user:
        abort(404, message=f"User {user_id} not found")


class UserResource(Resource):
    def get(self, user_id):
        abort_if_user_not_found(user_id)
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        return jsonify({'user': user.to_dict(only=('id',
                                                   'nickname',
                                                   'email',
                                                   'hashed_password',
                                                   'friends'))})

    def delete(self, user_id):
        abort_if_user_not_found(user_id)
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        session.delete(user)
        session.commit()
        return jsonify({'success': 'OK'})


class UserListResource(Resource):
    def get(self):
        session = db_session.create_session()
        user = session.query(User).all()
        return jsonify(
            {
                'user':
                    [item.to_dict(only=('id',
                                        'nickname',
                                        'email',
                                        'hashed_password',
                                        'friends'))
                     for item in user]
            }
        )

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()
        user = User(
            nickname=args['nickname'],
            email=args['email'],
            hashed_password=args['hashed_password']
        )
        session.add(user)
        session.commit()
        return jsonify({'success': 'OK'})