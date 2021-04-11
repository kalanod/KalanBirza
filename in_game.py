from data import db_session
from data.rooms import Rooms
from data.users import User

import random
import json

START_BUDGET = 1000000
EVENT_CHANCE = 3  # 1/3 ходов


class InGameRoom:
    def __init__(self, id, title, data_string='', players_string=''):
        self.id = id
        self.title = title

        # дальше будем загружать всю информацию из строки
        # пока в строке только стоимость акций и ID

        self.stock_list = []
        with open('./data/stock.json') as file:
            stocks = json.loads(file.read())['stock']

            data_from_bd = dict()
            for line in data_string.split():
                data_from_bd[line.split(',')[0]] = float(line.split(',')[1])

            for stock in stocks:
                if stock["id"] in data_from_bd.keys():
                    self.stock_list.append(Stock({"id": stocks["id"],
                                                  "department_id": stocks["department_id"],
                                                  "name": stock["name"],
                                                  "short_name": stock["short_name"],
                                                  "cost": data_from_bd[stocks["id"]],
                                                  "lowest_cost": stock["lowest_cost"]}))

                else:
                    self.stock_list.append(Stock(stock))

        # загружаем игроков
        self.players = list()
        players_string = players_string.split()
        for player_data in players_string:
            self.players.append(InGamePlayer(player_data, self))

        self.load_to_db()

        print(f'load of room with id {self.id} complete')
        print('')
        print('loaded stocks:')
        for stock in self.stock_list:
            print(stock)

        print('')
        print('loaded players:')
        for player in self.players:
            print(player)

        print('')

        self.stages = {
            0: "Подготовка к игре",
            1: "Покупка акций и недвижимости ",
            2: "Аукцион",
            3: "Событие"
        }
        self.stage = 0
        self.decisions = []

    def load_to_db(self):
        print(f'saving room {self.id} to bd...')
        # создаем строки на основе данных комнаты и игроков для сохранения в ДБ
        data = ' '.join(list(map(lambda x: x.get_string_for_bd(), self.stock_list)))
        players = ' '.join(list(map(lambda x: x.get_string_for_bd(), self.players)))
        db_sess = db_session.create_session()
        room = db_sess.query(Rooms).filter(Rooms.id == self.id).first()
        if room:
            room.data = data
            room.players = players
            db_sess.commit()
            print(f'saving room {self.id} to bd complete')
            print(f'data: {data}')
            print(f'players: {players}')
            print(self.players)

        else:
            print(f"not find room {self.id}")

    def add_player(self, player_id):
        if self.player_in_room(player_id):
            self.get_player(player_id).online = True

        else:
            self.players.append(InGamePlayer(f'{player_id},{START_BUDGET},', self))

        self.load_to_db()

    def leave_player(self, player_id):
        if self.player_in_room(player_id):
            self.get_player(player_id).online = False

    def player_in_room(self, player_id):
        return any([player_id == player.id for player in self.players])

    def player_online(self, player_id):
        return self.get_player(player_id).online

    def get_player(self, player_id):
        for player in self.players:
            if player.id == player_id:
                return player

        return None

    def get_stock(self, stock_id):
        for stock in self.stock_list:
            if stock.id == stock_id:
                return stock

        return None

    def sell_stock_to_player(self, player_id, stock_id, quantity):
        player = self.get_player(player_id)
        stock = self.get_stock(stock_id)
        cost = stock.cost * quantity
        if player.budget < cost:
            return

        else:
            player.budget -= cost
            player.stocks[stock_id] += quantity

    def buy_stock_from_player(self, player_id, stock_id, quantity):
        player = self.get_player(player_id)
        stock = self.get_stock(stock_id)
        cost = stock.cost * quantity
        if player.stocks[stock_id] < quantity:
            return

        else:
            player.budget += cost
            player.stocks[stock_id] -= quantity

    def turn(self):
        self.load_to_db()
        # вызываем эту функцию каждый ход
        # каждый ход сохраняемся в бд

    def event_generator(self):
        changes = []
        check_file = open('events.txt', 'r')
        events = check_file.read().split('\n')
        check_file.close()
        new_events = random.choice(events)
        new_events = new_events.split(':')
        events = new_events[1].split(',')
        for i in events:
            if '+' in i:
                i = i.split('+')
                changes.append(f'+{i[1]}')
            else:
                i = i.split('-')
                changes.append(f'-{i[1]}')
        new_list = []
        stocks_prase = []
        check_file = open('stocks.txt', 'r')
        for i in check_file.read().split('\n'):
            if i != '':
                i = i.split()
                stocks_prase.append(i[-1].split('-')[1:])
        back = ''
        for i, j in zip(stocks_prase, changes):
            if '+' in j:
                sum = int(i[0]) + int(j[1:])
                if sum > int(i[-1]):
                    new_list.append(str(sum))
                else:
                    new_list.append(i[1])
            else:
                sum = int(i[0]) - int(j[1:])
                if sum > int(i[-1]):
                    new_list.append(str(sum))
                else:
                    new_list.append(i[1])
        check_file = open('stocks.txt', 'r')
        for i, j in zip(check_file.read().split('\n'), new_list):
            i = i.split('-')
            back += f'{i[0]}-{str(j)}-{i[2]}\n'
        check_file.close()
        check_file = open('stocks.txt', 'w')
        check_file.truncate()
        for i in back:
            check_file.write(i)
        check_file.close()

    def share_generator(self):
        conclusion = list(map(lambda x: StockCard(x, random.randint(1, 10)), random.sample(self.stock_list, 3)))
        return conclusion


class InGamePlayer:
    def __init__(self, player_data: str, room: InGameRoom):
        self.online = False
        self.room = room

        # дальше будем загружать всю информацию из строки
        # пока в строке только ID и бюджет игрока
        player_data = player_data.split(',')
        self.id = int(player_data[0])
        self.budget = int(player_data[1])

        # загружаем акции
        stocks_from_bd = dict()
        for stock in player_data[2].split('|'):
            if stock == '':
                break
            stocks_from_bd[int(stock.split(':')[0])] = int(stock.split(':')[1])

        self.stocks = dict()
        for stock in self.room.stock_list:
            if stock.id in stocks_from_bd.keys():
                self.stocks[stock] = stocks_from_bd[stock.id]

            else:
                self.stocks[stock] = 0

        self.realty = dict()

        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == self.id).first()
        if user:
            self.nickname = user.nickname

        else:
            raise ValueError

    def get_string_for_bd(self):
        return f'{self.id},{self.budget},{"|".join(list(map(lambda x: f"{x.id}:{self.stocks[x]}", self.stocks.keys())))}'

    def buy_realty(self, realty):  # realty - строка 'название,цена,доход'
        realty = realty.split(',')
        if True:  # тут должна быть проверка на то, не купили ли ещё данную недвижимость
            if self.budget >= float(realty[1]):
                self.realty[realty[0]] = float(realty[2])
                self.budget -= float(realty[1])

    def sale_realty(self, realty):  # realty - строка 'название,цена,доход'
        realty = realty.split(',')
        if realty[1] in self.realty.keys():
            self.budget += float(realty[1])
            self.realty.pop(realty[0])

    def __repr__(self):
        return self.nickname


class StockCard:
    def __init__(self, stock, quantity):
        self.stock = stock
        self.quantity = quantity
        self.players = []


class Stock:
    def __init__(self, stock_dict):
        if isinstance(stock_dict, dict):
            self.id = stock_dict["id"]
            self.department_id = stock_dict["department_id"]
            self.name = stock_dict["name"]
            self.short_name = stock_dict["short_name"]
            self.cost = stock_dict["cost"]
            self.lowest_cost = stock_dict["lowest_cost"]

        else:
            raise ValueError

    def get_string_for_bd(self):
        return f'{self.id},{self.cost}'

    def __repr__(self):
        return f'<Stock> id: {self.id}, short_name: {self.short_name}, cost: {self.cost}'


class Property:
    def __init__(self):
        self.id = id
        self.description = 'Описание'


class Auction:
    def end_auction(self):
        check_file = open('auction.txt', 'r')
        check_file = check_file.read().split('\n')
        if check_file != '':
            max = -1
            winner = ''
            for i in check_file[:-1]:
                if int(i.split()[1]) > max:
                    max = int(i.split()[1])
                    winner = i.split()[0]
            check_file = open('auction.txt', 'w')
            check_file.truncate()
            return f'{winner} победил отдав {str(max)}'
        else:
            print('Нужно запустить аукцион')

    def new_bids(self, participants_prices):
        check_file = open('auction.txt', 'r')
        if check_file.read() == '':
            work_file = open('auction.txt', 'w')
            work_file.truncate()
            for i in participants_prices:
                work_file.write(f'{i[0]} {i[1]}\n')
            check_file.close()
        else:
            print('Нужно запустить аукцион')

