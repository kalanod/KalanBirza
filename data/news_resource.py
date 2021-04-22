from data import db_session
from data.news import News
from flask_restful import reqparse, abort, Api, Resource
from flask import jsonify
from data.news_resource_parser import parser


def abort_if_news_not_found(news_id):
    session = db_session.create_session()
    news = session.query(News).get(news_id)
    if not news:
        abort(404, message=f"News {news_id} not found")


class NewsResource(Resource):
    def get(self, news_id):
        abort_if_news_not_found(news_id)
        session = db_session.create_session()
        news = session.query(News).get(news_id)
        return jsonify({'news': news.to_dict(only=('id',
                                                   'creator_id',
                                                   'header',
                                                   'text',
                                                   'image_address'))})

    def delete(self, news_id):
        abort_if_news_not_found(news_id)
        session = db_session.create_session()
        news = session.query(News).get(news_id)
        session.delete(news)
        session.commit()
        return jsonify({'success': 'OK'})


class NewsListResource(Resource):
    def get(self):
        session = db_session.create_session()
        news = session.query(News).all()
        return jsonify(
            {
                'news':
                    [item.to_dict(only=('id',
                                        'creator_id',
                                        'header',
                                        'text',
                                        'image_address'))
                     for item in news]
            }
        )

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()
        news = News(
            creator_id=args['creator_id'],
            header=args['header'],
            text=args['text'],
            image_address=args['image_address']
        )
        session.add(news)
        session.commit()
        return jsonify({'success': 'OK'})