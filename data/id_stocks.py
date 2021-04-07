def ib_stocks(id):
	check_file = open('stocks.txt', 'r')
	text = check_file.read().split('\n')
	back = ''
	for i in text:
		if str(id + 1) in i:
			i = i.split()
			i = i[-1].split('-')
			back = i[1]
			break
	return back