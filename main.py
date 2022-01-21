from flask import Flask, redirect, render_template
from flask_login import LoginManager, logout_user, login_required
from flask_restful import reqparse, abort, Api, Resource
from flask import Flask, render_template, redirect, request
from forms.register import RegisterForm
from forms.login import LoginForm
from flask import make_response
from flask import jsonify
from requests import get, post
from flask_login import login_user, logout_user, current_user
from data import db_session
from data.users import User
from data import users_resource
from data.rooms import Rooms
from data import rooms_resource
from data.news import News
from data import news_resource
from in_game import *
from flask_socketio import SocketIO, send, emit, join_room, leave_room
import os
import random
import time

# print(os.getcwd())

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
api.add_resource(news_resource.NewsListResource, '/api/news')
api.add_resource(news_resource.NewsResource, '/api/news/<int:news_id>')
active_rooms = []  # список со всеми комнатами


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.errorhandler(404)
def not_found(error):
    return make_response(render_template('not_found.html'))


@app.errorhandler(405)
def method_not_allowed(error):
    return make_response(jsonify({'error': 'Method Not Allowed - 405'}), 405)


@app.route('/rooms', methods=['GET', 'POST'])
def base():
    params = dict()
    params["title"] = "Список комнат"
    params["rooms"] = active_rooms
    print(active_rooms)
    return render_template('index.html', **params)


@app.route('/home', methods=['GET', 'POST'])
def home():
    return render_template('home.html')


@app.route('/', methods=['GET', 'POST'])
def home2():
    return render_template('home.html')


@app.route('/news', methods=['GET', 'POST'])
def news():
    db_sess = db_session.create_session()
    params = dict()
    params["title"] = "Новости"
    params["news_list"] = reversed(db_sess.query(News).all())
    print(params["news_list"])

    return render_template('news.html', **params)

@app.route('/devs', methods=['GET', 'POST'])
def devs():
    params = dict()
    params["title"] = "Разработчики"
    params["devs_list"] = [
        {"nickname": "Андрей Трофимов",
         "dev": ["разработка и поддержка игры", "Писать по вопросам и предложениям"],
         "link_text": "VK",
         "link": "https://vk.com/kalanod"},
        {"nickname": "Михаил Буянов",
         "dev": ["дизайн",
                 "бэкенд"],
         "link_text": "VK",
         "link": "https://vk.com/deep_dark_fantasies_vana"},
        {"nickname": "Прошак Валерий",
         "dev": [""],
         "link_text": "VK",
         "link": "https://vk.com/vproshak"},
        {"nickname": "Влад Ревякин",
         "dev": [""],
         "link_text": "VK",
         "link": "https://vk.com/id515647622"}
    ]

    return render_template('devs.html', **params)


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
            return redirect('/rooms')
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
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        user = User(
            nickname=form.nickname.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        login_user(user, remember=True)
        return redirect('/rooms')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/register_to_room/<int:room_id>', methods=['GET', 'POST'])
def reqister_to_room(room_id):
    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        user = User(
            nickname=form.nickname.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        login_user(user, remember=True)
        return redirect(f'/connect_to_room/{room_id}')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/create_room/<title>/<creator_id>')
def create_room(title, creator_id):
    print('creating room', title, creator_id)
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
    return redirect('/rooms')


@app.route('/connect_to_room/<int:room_id>/<int:player_id>', methods=['GET', 'POST'])
def connect_to_room(room_id, player_id):
    room = get_room(room_id)
    if room.player_in_room(player_id) or room.stage == -1:

        return redirect(f'/room/{room_id}')

    else:
        return redirect('/rooms')


@app.route('/connect_to_room/<int:room_id>', methods=['GET', 'POST'])
def connect_to_room_byId(room_id):
    if current_user.is_authenticated:
        room = get_room(room_id)
        if room.player_in_room(current_user.id) or room.stage == -1:
            room.add_player(current_user.id)
            return redirect(f'/room/{room_id}')

        else:
            return redirect('/rooms')
    else:
        return redirect(f'/register_to_room/{room_id}')


@app.route('/leave_game/<int:room_id>/<int:player_id>', methods=['GET', 'POST'])
@socketIO.on('remove_user')
def remove_user(room_id, player_id):
    room = get_room(room_id)
    if room.player_in_room(player_id):
        room.remove_player(player_id)
        json = {'data': []}

        # send_notif(room, text="вышел", head="игрок покинул игру", img="/static/img/yellow_sq.png")
        return redirect(f'/rooms')
    else:
        return redirect('/rooms')


@app.route('/leave_from_room/<int:room_id>/<int:player_id>', methods=['GET', 'POST'])
def leave_from_room(room_id, player_id):
    # какие-нибудь проверки
    get_room(room_id).leave_player(player_id)
    return redirect('/rooms')


@app.route('/room/<int:room_id>', methods=['GET', 'POST'])
def in_room(room_id):
    current_room = get_room(room_id)

    return render_template('in_room.html', current_room=current_room, title="В игре")


def update_stock_cards(room_id, json):
    # print('updating stock cards...')
    # print(json)
    emit('update_stock_cards', json, to=room_id)
    # emit('update_user_ingame', list(map(lambda x: x.id, get_room(room_id).players)), to=room_id)


def show_stock_cards(room_id):
    # print('showing stock cards...')
    emit('show_stock_cards', [], to=room_id)


def update_stock_table(room_id, json):
    emit('update_stock_table', json, to=room_id)
    # emit('update_user_ingame', list(map(lambda x: x.id, get_room(room_id).players)), to=room_id)


def update_case(room_id, json):
    emit('update_case', json, to=room_id)


def clear_playzone(room_id):
    emit('clear_playzone', to=room_id)


def win(room_id, json):
    emit('win', json, to=room_id)


def my_des(json):
    room_id = int(json["room_id"])
    room = get_room(room_id)
    player = room.get_player(int(json['player_id']))
    code = (json['code'])
    # нажатие на карту акций
    print("codecode=" + str(code))
    if code == "2":
        if room.stage != 1:
            return False
        if int(json['card_num']) not in [0, 1, 2]:
            return False
        card = room.stocks_cards[int(json['card_num'])]
        if player.budget < card.cost:  # это надо будет показывать на самой карте
            return False
        if player in card.players:  # это надо будет показывать на самой карте
            return False
        answer = {"text": f"акции ({card.quantity}) компании {card.stock.name} куплены за {card.cost}",
                  "head": "Покупка акций", "img": "/static/img/green_sq.png", "id": current_user.id}
        return answer
    elif code == "3":
        if not json['company_id'].isdigit():
            stock = room.get_stock_from_short_name(json['company_id'])
        else:
            stock = room.get_stock(json['company_id'])
        quantity = int(json['quantity'])
        if quantity <= 0:
            answer = {"text": f"брооо, это ты конечно ловко придумал", "head": "Продажа акций",
                      "id": current_user.id, "img": "/static/img/red_sq.png"}
            return answer
        if player.stocks[stock] < quantity:
            answer = {"text": f"Не хватает акций для продажи", "head": "Продажа акций", "id": current_user.id,
                      "img": "/static/img/red_sq.png"}
            return answer
        answer = {"text": f"акции ({quantity}) компании {stock.name} проданы",
                  "head": "Продажа акций", "id": current_user.id, "img": "/static/img/green_sq.png"}
        return answer

    # покупка недвижимости можно краткое название, но лучше не надо
    elif code == 4:
        if json['company_id']:
            realty = room.get_realty(json['company_id'])

        elif json['title']:

            title = json['title']
            realty = None
            for realty_in_list in room.realty_list:
                if realty_in_list.name == title:
                    realty = realty_in_list
                    break

        else:
            return False

        if realty is None:
            answer = {"text": f"Похоже, такой недвижимости нет", "head": "Покупка недвижимости",
                      "id": current_user.id, "img": "/static/img/red_sq.png"}
            return answer

        if realty.owner is not None:
            answer = {"text": f"Похоже, уже кто то купил эту компанию", "head": "Покупка недвижимости",
                      "id": current_user.id, "img": "/static/img/red_sq.png"}
            return answer

        if player.budget < realty.cost:
            answer = {"text": f"Тебе не хватает денег(", "head": "Покупка недвижимости",
                      "id": current_user.id, "img": "/static/img/red_sq.png"}
            return answer

        if realty in player.realty:
            answer = {"text": f"Ты и так владелец этой компании)", "head": "Покупка недвижимости",
                      "id": current_user.id, "img": "/static/img/red_sq.png"}
            return answer

        if room.get_stock(realty.id) in player.stocks and player.stocks[
            room.get_stock(realty.id)] < realty.realty_stock_quantity:
            answer = {"text": f"Похоже, тебе не хватает акций этой компании для покупки её недвижимости",
                      "head": "Покупка недвижимости", "id": current_user.id, "img": "/static/img/red_sq.png"}
            return answer

        answer = {"text": json['title'] + " куплена!", "head": "Покупка недвижимости",
                  "id": current_user.id, "img": "/static/img/green_sq.png"}
        return answer

    # продажа недвижимости
    elif code == "5":
        realty = room.get_realty(json['company_id'])

        if realty is None:
            return False

        if realty.owner != player:
            return False

        if realty not in player.realty:
            return False
    else:
        return False


@socketIO.on('decision')
def make_decision(json):
    # print('get_decision from server')
    # print(f'json: {json}')
    data = ''
    room_id = int(json["room_id"])

    room = get_room(room_id)
    if json['code'] == '1':
        data = 'Игрок готов'
        log(json['room_id'], data)
        if int(room.stage) == 3:
            emit("show_pass", current_user.id, to=room_id)
    elif json['code'] == '2':
        data = f'Выбор карты акций {list(json.keys())[-1]} от 0 до 2 покупка будет происходить во время аукциона'
        log(json['room_id'], data)
    elif json['code'] == '3':
        data = 'Продажа акций'
        log(json['room_id'], data)
    elif json['code'] == '4':
        data = 'Покупка недвижимости'
        log(json['room_id'], data)
        for _, i in enumerate(get_room(json['room_id']).realty_list):
            if i.name == json['title']:
                idd = _ + 1
                json['company_id'] = idd
    elif json['code'] == '5':
        data = 'Покупка недвижимости'
        log(json['room_id'], data)

    # СОРИ ЗА КОСТЫЛИ ОТ АНДРЮЮЮШИИИ, НОкак иначе идей нет!

    answer = my_des(json)
    if answer:
        send_notif(room_id, text=answer["text"], head=answer["head"], id=answer["id"], img=answer["img"])
    room.add_decision_to_queue(json)
    # пока добавим обработку всех решений в очереди сюда
    room.decision_handler()
    players = [len(room.players), len([i for i in room.players if i.ready])]
    emit('make_turn', players, to=room_id)
    # emit('new_ready_user_ingame', current_user.id, to=room_id)
    emit('decision_on', to=room_id)

    d_stonks = dict()
    d_stonks.clear()
    for i in room.get_player(int(json['player_id'])).d_stocks:
        if str(i.id) in d_stonks:
            d_stonks[str(i.id)][0] += 1
            d_stonks[str(i.id)][1] += i.price
        else:
            d_stonks[str(i.id)] = [1, i.price]
    print('\n\n\n\n')

    for i in d_stonks:
        # print(str(d_stonks[i][1] / d_stonks[i][0]), str(room.stock_list[int(i) - 1].cost))
        d_stonks[i] = str(d_stonks[i][0] * room.stock_list[int(i) - 1].cost - d_stonks[i][1])

    print(list(map(lambda x: x.id, get_room(room_id).players)))
    print('\n\n\n\n')
    for i in room.get_player(int(json['player_id'])).stocks:
        if str(i.id) not in d_stonks:
            d_stonks[str(i.id)] = '+0'
        else:
            if int(d_stonks[str(i.id)]) > 0:
                d_stonks[str(i.id)] = '+' + d_stonks[str(i.id)]
    # print(room.stock_list)
    stonks = {'id': int(json['player_id']),
              'data': [
                  {'short_name': i.short_name,
                   'cost': i.cost,
                   'stocks': room.get_player(int(json['player_id'])).stocks[i],
                   'delta': d_stonks[str(i.id)]
                   } for i in room.get_player(int(json['player_id'])).stocks]
              }

    emit('update_bag', stonks, to=room_id)

    # Это просто обновление недвижимости
    com = {}
    for i in room.realty_list:
        if i.owner:
            com[i.name] = {'id': i.owner.id, 'name': i.owner.get_name()}
        else:
            com[i.name] = None
    com1 = {'id': current_user.id, 'data': com}
    emit('update_com', com1, to=room_id)
    json = {'data': []}
    for player in room.players:
        json['data'].append(
            {'nickname': player.nickname, 'budget': player.budget, 'id': player.id, 'ready': player.ready})
    emit('update_players', json, to=room_id)
    # emit('new_ready_user_ingame', current_user.id, to=room_id)
    # emit('update_decision') здесь передадим что то, что в последствии покажет решение игрока


@app.route('/delete_room/<room_id>')
def detele_room(room_id):
    room_id = int(room_id)
    global active_rooms
    # ('')
    room = get_room(room_id)
    if room is None:
        print(f'room with id {room_id} not found')
        return redirect('/rooms')

    if room.stage != -1:
        print(f'room with id {room_id} in game')
        return redirect('/rooms')

    if room.players:
        print(f'room with id {room_id} not empty')
        return redirect('/rooms')

    print(f'deleting {room}')
    print(f'rooms before deleting: {active_rooms}')
    active_rooms.remove(room)
    db_sess = db_session.create_session()
    room_from_bd = db_sess.query(Rooms).get(room_id)
    db_sess.delete(room_from_bd)
    db_sess.commit()
    print(f'rooms before deleting: {active_rooms}')
    print('')

    return redirect('/rooms')


@socketIO.on('my_join')
@socketIO.on('join')
def on_join(room):
    join_room(room)
    current_room = get_room(room)
    current_room.add_player(current_user.id)
    json = {'data': []}
    for player in current_room.players:
        json['data'].append(
            {'nickname': player.nickname, 'budget': player.budget, 'id': player.id})
    emit('update_players', json, to=room)
    com = {}
    for i in current_room.realty_list:
        if i.owner:
            com[i.name] = {'id': i.owner.id, 'name': i.owner.get_name()}
            print("nanme=" + i.owner.get_name())
        else:
            com[i.name] = None

    com1 = {'id': current_user.id, 'data': com}
    emit('update_com', com1, to=room)
    stonks = {'id': current_user.id, 'data': [
        {'short_name': i.short_name, 'cost': i.cost, 'stocks': get_room(room).get_player(current_user.id).stocks[i]} for
        i
        in get_room(room).get_player(current_user.id).stocks]}
    emit('update_bag', stonks, to=room)
    players = [len(get_room(room).players), len([i for i in get_room(room).players if i.ready])]
    emit('make_turn', players, to=room)
    # emit('new_ready_user_ingame', current_user.id, to=room)
    update_money(room, {"id": current_user.id, "money": get_room(room).get_player(current_user.id).budget})
    send_notif(room, text=current_user.nickname + " входит в комнату",
               head="новый игрок", img="/static/img/blue_sq.png")


def send_notif(room, text="text", id="all", head="head", img="/static/img/blue_sq.png"):
    data = {"id": id, "head": head, "text": text, "img_src": img}
    emit('new_notice', data, to=room)
    print("tess")
    print(room, "aaaa")


@socketIO.on('disconnect')
def disconnect():
    for room in active_rooms:
        room.leave_player(current_user.id)
        current_room = room
        json = {'data': []}
        for player in current_room.players:
            json['data'].append(
                {'nickname': player.nickname, 'budget': player.budget, 'id': player.id})
        emit('update_players', json, to=room)
        send_notif(room, text=current_user.nickname + "вышел из комнаты",
                   head="игрок отключился", img="/static/img/blue_sq.png")


@socketIO.on('leave')
def on_leave(room):
    print(room, 'leave socket')
    leave_room(room)
    user = current_user.id
    get_room(room).leave_player(user)
    current_room = get_room(room)
    json = {'data': []}
    for player in current_room.players:
        json['data'].append(
            {'nickname': player.nickname, 'budget': player.budget, 'id': player.id})
    emit('update_players', json, to=room)
    send_notif(room, text=current_user.nickname + " вышел из комнаты", head="игрой отключился", img="/static/img/red_sq.png")


@socketIO.on('sell')
def sell(json):
    print(json, 'sell socket')
    make_decision(json)
    # emit('', to=json['room'])


@socketIO.event
def add_message(json, room_id):
    get_room(room_id)
    room = '1'
    emit('new_message', json, to=room)


@socketIO.on('ready_to_start')
def ready_to_start(json1):
    room = int(json1['room_id'])
    id1 = json1['player_id']
    emit('new_ready_user', id1, to=room)


@socketIO.on('get_com_buy')
def get_com_buy(json):
    room = json['room_id']
    id = json['player_id']
    title = json['title']
    com = ''
    for i in get_room(room).realty_list:
        if i.name == title:
            com = i
    if com.owner:
        json1 = {
            'des': com.des,
            'player_id': id,
            'room_id': room,
            'title': title,
            'bonus': com.bonus,
            'cost': com.cost,
            'owner': com.owner.nickname,
            'count': com.realty_stock_quantity
        }
    else:
        json1 = {
            'des': com.des,
            'player_id': id,
            'room_id': room,
            'title': title,
            'bonus': com.bonus,
            'cost': com.cost,
            'owner': com.owner,
            'count': com.realty_stock_quantity
        }
    emit('get_com_buy', json1, to=room)


def main():
    db_session.global_init("db/project_db.db")
    db_sess = db_session.create_session()

    rooms_from_db = db_sess.query(Rooms).all()
    global active_rooms
    for room_from_db in rooms_from_db:
        new_room = InGameRoom(room_from_db.id, room_from_db.title, room_from_db.data, room_from_db.players)
        active_rooms.append(new_room)

    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    # app.run(debug=True)


def get_room(room_id):
    for room in active_rooms:
        if room:
            if room.id == room_id:
                return room
    return None


def log(room_id, data):
    emit('log', data, to=room_id)


def update_money(room_id, json):
    emit('update_money', json, to=room_id)


def add_friend(self_id, friend_id):
    user = User()
    db_sess = db_session.create_session()
    friends = db_sess.query(User).filter(User.id == self_id).split()[-1] + [str(friend_id)]
    user.friends = ','.join(friends)
    db_sess.commit()
    return True


def del_friend(self_id, friend_id):
    user = User()
    db_sess = db_session.create_session()
    friends = db_sess.query(User).filter(User.id == self_id).split()[-1]
    friends.remove(str(friend_id))
    user.friends = ','.join(friends)
    db_sess.commit()
    return True


if __name__ == '__main__':
    main()
