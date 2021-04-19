from data import db_session
from data.rooms import Rooms
from data.users import User

import random
import json

from main import update_case, update_stock_cards, clear_playzone, update_stock_table, win

START_BUDGET = 1000000


class InGameRoom:
    def __init__(self, id, title, data_string='', players_string=''):
        self.id = id
        self.title = title

        # дальше будем загружать всю информацию из строки
        # пока в строке только стоимость акций и ID

        self.stock_list = []
        self.realty_list = []
        with open('./data/stock.json') as file:
            companies = json.loads(file.read())['companies']

            data_from_bd = dict()
            for line in data_string.split():
                data_from_bd[line.split(',')[0]] = float(line.split(',')[1])

            for company in companies:
                if company["id"] in data_from_bd.keys():
                    self.stock_list.append(Stock({"id": company["id"],
                                                  "department_id": company["department_id"],
                                                  "name": company["name"],
                                                  "short_name": company["short_name"],
                                                  "cost": data_from_bd[company["id"]],
                                                  "lowest_cost": company["stock_lowest_cost"],
                                                  "img": company["img"]}))

                else:
                    self.stock_list.append(Stock(company))

                self.realty_list.append(Realty(company))
                # пока все недвижимость свободна, она будет куплена при загрузке игроков

        # загружаем игроков
        self.players = list()
        players_string = players_string.split()
        for player_data in players_string:
            self.players.append(InGamePlayer(player_data, self))

        #print('')
        #print(f'load of room with id {self.id} complete')
        #print('')
        #print('loaded stocks:')
        for stock in self.stock_list:
            print(stock)
        #print('')
        #print('loaded realty:')
        for realty in self.realty_list:
            print(realty)
        #print('')
        #print('loaded players:')
        for player in self.players:
            print(player)
        #print('')

        self.stages = {
            -1: "Подготовка к игре между играми",
            0: "Подготовка к игре между ходами",
            1: "Покупка акций и недвижимости ",
            2: "Аукцион",
            3: "Событие"
        }
        self.stage = -1
        self.stocks_cards = []
        self.decisions_queue = []

    def save_to_db(self):
        #print('')
        #print(f'saving room {self.id} to bd...')
        # создаем строки на основе данных комнаты и игроков для сохранения в ДБ
        data = ' '.join(list(map(lambda x: x.get_string_for_bd(), self.stock_list)))
        players = ' '.join(list(map(lambda x: x.get_string_for_bd(), self.players)))
        db_sess = db_session.create_session()
        room = db_sess.query(Rooms).filter(Rooms.id == self.id).first()
        if room:
            room.data = data
            room.players = players
            db_sess.commit()

            #print(f'saving room {self.id} to bd complete')
            ##print(f'stocks data: {data}')
            #(f'players data: {players}')
            #print(self.players)
            #print('')

        else:
            print(f"not find room {self.id}")

    def add_decision_to_queue(self, json):
        player = self.get_player(int(json['player_id']))
        code = (json['code'])
        #print('')
        #print(f'decision added to queue of {self} by {player}')
        #print(f'code: {code}')
        #print(f'json: {json}')
        #print('')
        self.decisions_queue.append(Decision(player, json))

    def add_player(self, player_id):
        if not self.player_in_room(player_id):
            self.players.append(InGamePlayer(f'{player_id},{START_BUDGET},,', self))
            self.save_to_db()

        self.get_player(player_id).online = True

        #print('')
        #print(f'{self.get_player(player_id)} join to {self}')
        #print(f'online players: {self.get_online_players()}')
        #print(f'ingame players: {self.players}')
        #print('')

    def leave_player(self, player_id):
        if self.player_in_room(player_id):
            if self.stage == -1:
                self.players.remove(self.get_player(player_id))
                self.save_to_db()

            else:
                self.get_player(player_id).online = False

        #('')
        #print(f'{self.get_player(player_id)} leave from {self}')
        #print(f'online players: {self.get_online_players()}')
        #print(f'ingame players: {self.players}')
        #print('')

    def player_in_room(self, player_id):
        return any([player_id == player.id for player in self.players])

    def player_online(self, player_id):
        try:
            return self.get_player(player_id).online

        except Exception:
            return False

    def get_player(self, player_id):
        for player in self.players:
            if player.id == player_id:
                return player

        return None

    def get_unready_players(self):
        unready_players = []
        for player in self.players:
            if not player.ready:
                unready_players.append(player)

        return unready_players

    def get_online_players(self):
        return list(filter(lambda x: x.online, self.players))

    def get_stock(self, stock_id):
        for stock in self.stock_list:
            if stock.id == stock_id:
                return stock

        return None

    def get_realty(self, realty_id):
        for realty in self.realty_list:
            if realty.id == realty_id:
                return realty

        return None

    def sell_stock_to_player(self, player, stock, quantity):  # эта функция потом уйдет в стадию аукциона
        cost = stock.cost * quantity
        if player.budget < cost:
            return

        else:
            player.budget -= cost
            if not stock in player.stocks.keys():
                player.stocks[stock.id] = 0
            player.stocks[stock] += quantity

    def share_generator(self):
        conclusion = list(map(lambda x: StockCard(x, random.randint(1, 10)), random.sample(self.stock_list, 3)))
        return conclusion

    def decision_handler(self):
        #print('')
        #print(f'decision_handler of {self} started')
        #print('decisions:')

        while len(self.decisions_queue) > 0:
            decision = self.decisions_queue.pop(0)
            code = decision.code
            player = decision.player

            #print(decision)

            # игрок готов
            if code == 1:
                player.ready = True
                if len(self.get_unready_players()) == 0:
                    self.next_stage()  # как только все игроки готовы начинается следующая стадия хода

            # нажатие на карту акций
            elif code == 2:
                if self.stage != 1:
                    continue

                if int(decision.data['card_num']) not in [0, 1, 2]:
                    continue

                card = self.stocks_cards[int(decision.data['card_num'])]

                if player.budget < card.cost:  # это надо будет показывать на самой карте
                    continue

                if player in card.players:  # это надо будет показывать на самой карте
                    continue

                card.players.append(player)
                player.ready = True
                if len(self.get_unready_players()) == 0:
                    self.next_stage()  # как только все игроки готовы начинается следующая стадия хода

            # продажа акций
            elif code == 3:
                stock = self.get_stock(decision.data['company_id'])
                quantity = decision.data['quantity']

                cost = stock.cost * quantity
                if player.stocks[stock.id] < quantity:
                    continue

                else:
                    player.budget += cost
                    player.stocks[stock.id] -= quantity

            # покупка недвижимости
            elif code == 4:
                realty = self.get_realty(decision.data['company_id'])

                if realty is None:
                    continue

                if realty.owner is not None:
                    continue

                if player.budget < realty.cost:
                    continue

                if realty in player.realty:
                    continue

                player.budget -= realty.cost

                if realty.need_for_win:
                    self.player_win(player)
                    return None  # завершение работы обработчика

                player.realty.append(realty)
                realty.owner = player

            # продажа недвижимости
            elif code == 5:
                realty = self.get_realty(decision.data['company_id'])

                if realty is None:
                    continue

                if realty.owner != player:
                    continue

                if realty not in player.realty:
                    continue

                player.budget += realty.cost
                player.realty.remove(realty)
                realty.owner = None

        #print('')

    def make_all_players_unready(self):
        for player in self.players:
            player.ready = False

    def next_stage(self):
        #('')
       # print(f'{self} go to next stage')
        #print(f'{self} last stage is {self.stage} stage - {self.stages[self.stage]}')

        if self.stage == -1:
            self.stage = 1
           # print(f'{self} go to {self.stage} stage - {self.stages[self.stage]}')
           #print('')

            self.make_all_players_unready()
            self.stocks_cards = self.share_generator()

            for player in self.players:
                for realty in player.realty:
                    player.budget += realty.bonus

            out_json = {}
            for card in self.stocks_cards:
                out_json[card.stock.name] = {"quantity": card.quantity,
                                             "price": card.stock.cost,  # стоимость одной акции
                                             "cost": card.cost,
                                             "img": card.stock.company_logo_address}

            update_stock_cards(self.id, out_json)

        elif self.stage == 0:  # отличие только в том, что в комнату нельзя зайти и выйти из нее полностью
            self.stage = 1
            #print(f'{self} go to {self.stage} stage - {self.stages[self.stage]}')
            #print('')

            self.make_all_players_unready()
            self.stocks_cards = self.share_generator()

            for player in self.players:
                for realty in player.realty:
                    player.budget += realty.bonus

            out_json = {}
            for card in self.stocks_cards:
                out_json[card.stock.name] = {"quantity": card.quantity,
                                             "price": card.stock.cost,  # стоимость одной акции
                                             "cost": card.cost,
                                             "img": card.stock.company_logo_address}

            update_stock_cards(self.id, out_json)

        elif self.stage == 1:
            self.stage = 2
            #print(f'{self} go to {self.stage} stage - {self.stages[self.stage]}')
            #print('')

            # аукцион и добавление акций пока пропустим, для теста их получат все, кто купил
            for card in self.stocks_cards:
                for player in card.players:
                    self.sell_stock_to_player(player, card.stock, card.quantity)
            self.next_stage()

        elif self.stage == 2:
            self.stage = 3
            #print(f'{self} go to {self.stage} stage - {self.stages[self.stage]}')
            #print('')

            self.make_all_players_unready()
            with open('./data/events.json', encoding='utf-8') as file:
                all_events = json.loads(file.read())['events']

                out_json = {}

                for i in range(2):
                    event = random.choice(all_events)
                    #print(f'event {i + 1}: {event}')
                    # показываем событие игрокам
                    out_json[event['description']] = dict()

                    for change in event['changes']:
                        for stock in self.stock_list:
                            if stock.department_id == change['department_id']:
                                stock.cost += change['value']
                                if stock.cost < stock.lowest_cost:
                                    stock.cost = stock.lowest_cost
                                if change['value'] != 0:
                                    out_json[event['description']][stock.name] = change['value']

                update_case(self.id, out_json)
                update_stock_table(self.id)

        elif self.stage == 3:  # после события, когда все нажмут ок, мы опять переходим к покупке акций по карточкам
            self.stage = 0
            #print(f'{self} go to {self.stage} stage - {self.stages[self.stage]}')
            #('')

            self.save_to_db()
            clear_playzone(self.id)

    def player_win(self, player_obj):
        #print('')
        #print(f'clearing all data in {self}')
        for player in self.players:  # сброс игроков
            player.ready = False
            player.budget = START_BUDGET

            start_stocks = dict()
            for stock in self.stock_list:
                start_stocks[stock] = 0

            player.stocks = start_stocks
            player.realty = []

        with open('./data/stock.json') as file:
            companies = json.loads(file.read())['companies']

        for stock in self.stock_list:  # сброс цен акций
            stock.cost = companies[stock.id]['cost']

        self.stage = -1

        win(self.id, player_obj)
        update_stock_table(self.id)

        #print(f'players: {self.players}')
        #print(f'stock: {self.stock_list}')
        #print('')

        self.save_to_db()

    def __repr__(self):
        return f'<InGameRoom> id: {self.id} title: {self.title}'


class InGamePlayer:
    def __init__(self, player_data: str, room: InGameRoom):
        self.online = False
        self.ready = False  # нажал ли игрок
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

        # загружаем недвижимость
        self.realty = []
        for realty_id in player_data[3].split('|'):
            if realty_id == '':
                break

            for realty in self.room.realty_list:
                if realty.id == realty_id:
                    self.realty.append(realty)
                    realty.owner = self

        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == self.id).first()
        if user:
            self.nickname = user.nickname

        else:
            raise ValueError

    def get_string_for_bd(self):
        return f'{self.id},' \
               f'{self.budget},' \
               f'{"|".join(list(map(lambda x: f"{x.id}:{self.stocks[x]}", self.stocks.keys())))},' \
               f'{"|".join(list(map(lambda x: x.id, self.realty)))}'

    def __repr__(self):
        return f'<InGamePlayer> id: {self.id} nickname: {self.nickname}'


class Decision:
    def __init__(self, player: InGamePlayer, data):
        self.player = player
        self.code = int(data['code'])
        self.data = data

    def __repr__(self):
        return f'<Decision> owner: {self.player} code: {self.code} data: {self.data}'


class StockCard:
    def __init__(self, stock, quantity):
        self.stock = stock
        self.quantity = quantity
        self.cost = stock.cost * quantity
        self.players = []


class Stock:
    def __init__(self, stock_dict):
        if isinstance(stock_dict, dict):
            self.id = stock_dict["id"]
            self.department_id = stock_dict["department_id"]
            self.name = stock_dict["name"]
            self.short_name = stock_dict["short_name"]
            self.cost = stock_dict["stock_cost"]
            self.lowest_cost = stock_dict["stock_lowest_cost"]
            self.company_logo_address = stock_dict["img"]

        else:
            raise ValueError

    def get_string_for_bd(self):
        return f'{self.id},{self.cost}'

    def __repr__(self):
        return f'<Stock> id: {self.id}, short_name: {self.short_name}, cost: {self.cost}'


class Realty:
    def __init__(self, realty_dict):
        self.id = int(realty_dict["id"])
        self.need_for_win = bool(realty_dict["need_for_win"])
        self.name = str(realty_dict["realty_name"])
        self.cost = int(realty_dict["realty_cost"])
        self.bonus = int(realty_dict["realty_bonus"])
        self.owner = None  # куплена ли игроком

    def __repr__(self):
        return f'<Realty> {self.id} owner: {self.owner}'


# что происходит?
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

