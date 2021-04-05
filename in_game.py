from data import db_session
from data.rooms import Rooms
from data.users import User

START_BUDGET = 1000000


class InGameRoom:
    def __init__(self, id, title, data_string, players_string):
        self.id = id
        self.title = title

        # дальше будем загружать всю информацию из строки
        # пока в строке только стоимость акций
        data_string = data_string.split()
        self.stock_dict = dict()
        for stock in data_string:
            self.stock_dict[stock.split(':')[0]] = float(stock.split(':')[1])

        # загружаем игроков
        players_string = players_string.split()
        self.players = list()
        for player_data in players_string:
            self.players.append(InGamePlayer(player_data))

    def add_player(self, player_id):
        if self.player_in_room(player_id):
            self.get_player(player_id).online = True

        else:
            self.players.append(InGamePlayer(f'{player_id},{START_BUDGET}'))

    def del_player(self, player_id):
        if self.player_in_room(player_id):
            self.get_player(player_id).online = False

    def player_in_room(self, player_id):
        return any([player_id == player.id for player in self.players])

    def player_online(self, player_id):
        return self.del_player(player_id).online

    def get_player(self, player_id):
        for player in self.players:
            if player.id == player_id:
                return player

        return None

    def load_to_db(self):
        # создаем строки на основе данных комнаты и игроков для сохранения в ДБ
        data = ' '.join(list(map(lambda x: f'{str(x)}:{str(self.stock[x])}', self.stock.keys())))
        players = ' '.join(list(map(lambda x: x.get_string_for_bd(), self.players)))
        db_sess = db_session.create_session()
        room = db_sess.query(Rooms).filter(Rooms.id == self.id).first()
        if room:
            room.data = data
            room.players = players
            db_sess.commit()

    def turn(self):
        self.load_to_db()
        # вызываем эту функцию каждый ход
        # каждый ход сохраняемся в бд


class InGamePlayer:
    def __init__(self, player_data):
        self.online = False

        # дальше будем загружать всю информацию из строки
        # пока в строке только ID и бюджет игрока
        player_data = player_data.split(',')
        self.id = int(player_data[0])
        self.budget = int(player_data[1])

        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == self.id).first()
        if user:
            self.nickname = user.nickname

        else:
            raise ValueError

    def get_string_for_bd(self):
        return f'{self.id},{self.budget}'

