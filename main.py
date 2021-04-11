from flask import Flask, redirect, render_template
from flask_login import LoginManager, logout_user, login_required

from flask_restful import reqparse, abort, Api, Resource
from flask import Flask, render_template, redirect, request
from forms.register import RegisterForm
from forms.login import LoginForm
from flask import make_response
from flask import jsonify
from requests import get, post
from flask_login import login_user, logout_user

from data import db_session
from data.users import User
from data import users_resource
from data.rooms import Rooms
from data import rooms_resource
from in_game import *
from flask_socketio import SocketIO, send, emit, join_room, leave_room
import os
import random

print(os.getcwd())

app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = 'key'

login_manager = LoginManager()
login_manager.init_app(app)
socketIO = SocketIO(app)
api.add_resource(users_resource.UserListResource, '/api/users')
api.add_resource(users_resource.UserResource, '/api/users/<int:users_id>')
api.add_resource(rooms_resource.RoomsListResource, '/api/rooms')
api.add_resource(rooms_resource.RoomsResource, '/api/rooms/<int:rooms_id>')
roomes = {'1': ['1', '2']}
active_rooms = []  # список со всеми комнатами


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found - 404'}), 404)


@app.errorhandler(405)
def method_not_allowed(error):
    return make_response(jsonify({'error': 'Method Not Allowed - 405'}), 405)


@app.route('/', methods=['GET', 'POST'])
def base():
    db_sess = db_session.create_session()
    params = dict()
    params["title"] = "Title"
    print(db_sess.query(Rooms).all())
    params["rooms"] = active_rooms

    return render_template('index.html', **params)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            param = dict()
            param["title"] = "Успех"
            return redirect('/')
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            nickname=form.nickname.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/create_room/<title>/<creator_id>')
def create_room(title, creator_id):
    db_sess = db_session.create_session()
    id = random.randint(1, 2 ** 32)
    room = Rooms(
        id=id,
        title=title,
        creator=creator_id,
        data='',
        players=''
    )
    db_sess.add(room)
    db_sess.commit()
    active_rooms.append(InGameRoom(id, title))
    # return redirect('/')
    # нам надо на главную страницу, а не результат
    return redirect('/')


@app.route('/connect_to_room/<int:room_id>/<int:player_id>', methods=['GET', 'POST'])
def connect_to_room(room_id, player_id):
    # какие-нибудь проверки
    get_room(room_id).add_player(player_id)
    return redirect(f'/room/{room_id}')


@app.route('/leave_from_room/<int:room_id>/<int:player_id>', methods=['GET', 'POST'])
def leave_from_room(room_id, player_id):
    # какие-нибудь проверки
    get_room(room_id).leave_player(player_id)
    return redirect('/')


@app.route('/room/<int:room_id>', methods=['GET', 'POST'])
def in_room(room_id):
    current_room = get_room(room_id)
    return render_template('in_room.html', current_room=current_room, title="В игре")


@socketIO.on('join')
def on_join(room):
    join_room(room)
    emit('add_players', json, to=room)


@socketIO.on('leave')
def on_leave(data):
    room = data['room']
    leave_room(room)
    send('Someone has left the room ' + room, to=room)


@socketIO.event
def add_message(json, room_id):
    get_room(room_id)
    room = '1'
    text = json['text']
    if room not in roomes:
        roomes[room] = []
    roomes[room][0] = text
    emit('new_message', json, to=room)


@socketIO.on('add_players')
def add_players(data):
    room = '1'
    emit('add_players', data, to=room)


@socketIO.on('remove_players')
def add_players(data):
    room = '1'
    emit('remove_players', data, to=room)


def main():
    db_session.global_init("db/project_db.db")
    db_sess = db_session.create_session()

    rooms_from_db = db_sess.query(Rooms).all()
    global active_rooms
    for room_from_db in rooms_from_db:
        print(f'main: {room_from_db.id, room_from_db.title, room_from_db.data, room_from_db.players}')
        new_room = InGameRoom(room_from_db.id, room_from_db.title, room_from_db.data, room_from_db.players)
        active_rooms.append(new_room)

    port = int(os.environ.get("PORT", 5000))
    # app.run(host='0.0.0.0', port=port)
    app.run(debug=True)


def get_room(room_id):
    for room in active_rooms:
        if room.id == room_id:
            return room
    return None


if __name__ == '__main__':
    main()
