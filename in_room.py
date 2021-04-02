class InGameRoom:
    def __init__(self, id):
        self.id = id
        self.players = list()
        # при инициализации надо смотреть есть ли сохранение в БД:
        # если нет то создавть новую игру
        # если есть то вызывать load_from_bd

    def add_player(self, player_id):
        if not self.player_in_room(player_id):
            self.players.append(InGamePlayer(player_id))

    def player_in_room(self, player_id):
        return any([player.id == player_id for player in self.players])

    def load_from_db(self):
        pass
        # для загрузки сохранения из БД

    def load_to_db(self):
        pass
        # для сохранения в БД

class InGamePlayer:
    def __init__(self, id):
        self.id = id
        self.nickname = f'{self.id} заглушка'