import random


def share_generator():
    check_file = open('stocks.txt', 'r')
    stocks = check_file.read().split('\n')
    conclusion = []
    for i in range(3):
        new_share = random.choice(stocks)
        index = stocks.index(new_share)
        del stocks[index]
        conclusion.append([new_share[2:], random.randint(1, 5)])
    return conclusion


def event_generator():
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


class auction:
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