import requests
import json
import csv
from bs4 import BeautifulSoup
import sqlite3
import sys
import plotly.plotly as py
import plotly.graph_objs as go
from datetime import datetime

###CACHE AND REQUEST
CACHE_FNAME = 'final_project_cache.json'
try:
    cache_file = open(CACHE_FNAME, 'r')
    cache_contents = cache_file.read()
    CACHE_DICTION = json.loads(cache_contents)
    cache_file.close()
except:
    CACHE_DICTION = {}

def make_request_using_cache(unique_ident):
    ## first, look in the cache to see if we already have this data
    if unique_ident in CACHE_DICTION:
        return CACHE_DICTION[unique_ident]
    else:
        resp = requests.get(unique_ident)
        CACHE_DICTION[unique_ident] = resp.text
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close() # Close the open file
        return CACHE_DICTION[unique_ident]

######CLASSES

class Coin():
    def __init__(self, name, curr_price, m_cap, link):
        URL = 'https://coinmarketcap.com'
        self.name = name
        self.curr_price = curr_price
        self.m_cap = m_cap
        self.link = URL + link
        self.hist_link = self.link + 'historical-data/'

class Coin_Per_Day():
    def __init__(self, date, open, high, low, close, volume, m_cap):
        self.date = date
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.m_cap = m_cap

####FUNCTIONS FOR DATA COLLECTION

def table_rows_to_objects(list_data):
    coin_list = []
    for i in list_data:
        name = i.find('a', {'class':"currency-name-container"}).text
        curr_price = i.find('a', {'class':'price'}).text
        m_cap = i.find('td', {'class': 'no-wrap market-cap text-right'}).text.replace('\n', '')
        link_a = i.find('span', {'class':'currency-symbol'})
        link = link_a.find('a')['href']
        coin = Coin(name=name, curr_price = curr_price, m_cap=m_cap, link = link)
        coin_list.append(coin)
    return coin_list

def get_data_per_coin(coin_class_list):
    coin_data_dict = {}
    for i in coin_class_list:
        request_data = make_request_using_cache(i.hist_link)
        soup= BeautifulSoup(request_data, 'html.parser')
        table_per_coin = soup.find('tbody')
        rows = table_per_coin.find_all('tr')
        for k in rows:
            data = k.find_all('td')
            date = data[0].text
            open = data[1].text.replace(',', '')
            high = data[2].text.replace(',', '')
            low = data[3].text.replace(',', '')
            close = data[4].text.replace(',', '')
            volume = data[5].text.replace(',', '')
            m_cap = data[6].text.replace(',', '')
            coin_per_day_row = Coin_Per_Day(date = date, open = open, high = high, low = low, close = close, volume = volume, m_cap = m_cap)
            if i.name in coin_data_dict:
                coin_data_dict[i.name].append(coin_per_day_row)
            else:
                coin_data_dict[i.name] = [coin_per_day_row]
    return coin_data_dict


###### DATABASE

def init_dbs(data_per_day):
    table_names = data_per_day.keys()
    conn = sqlite3.connect('crypto.sqlite')
    cur = conn.cursor()

    for i in table_names:
        statement = '''
                DROP TABLE IF EXISTS Cryptos
                '''
        cur.execute(statement)

        statement = '''
        CREATE TABLE IF NOT EXISTS Cryptos(
                'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
                'Name' TEXT
        );
        '''
        cur.execute(statement)
        conn.commit()

        statement = '''
                DROP TABLE IF EXISTS '{}';
                '''.format(i)
        cur.execute(statement)

        statement = '''
            CREATE TABLE IF NOT EXISTS '{}' (
                'ID' INTEGER PRIMARY KEY AUTOINCREMENT,
                'Date' TEXT,
                'CoinId' INTEGER,
                'Open' Real,
                'High' Real,
                'Low' Real,
                'Close' Real,
                'Volume' Real,
                'MarketCap' Real,
                FOREIGN KEY ('CoinId') REFERENCES Cryptos(Id)
            );
        '''.format(i)
        cur.execute(statement)
        conn.commit()
    conn.close()

def insert_crypto_data(data_per_day):
    conn = sqlite3.connect('crypto.sqlite')
    cur = conn.cursor()
    for i in data_per_day:

        statement = '''
                INSERT INTO Cryptos(Name) VALUES('{}')
        '''.format(i)

        cur.execute(statement)
        conn.commit()

        statement = '''
        SELECT Id FROM Cryptos WHERE Name = '{}'
        '''.format(i)
        cur.execute(statement)
        for t in cur:
            coin_id = t[0]

        t = data_per_day[i]
        for x in t:
            insertion = (x.date, coin_id, x.open, x.high, x.low, x.close, x.volume, x.m_cap)
            statement = 'INSERT INTO "{}"(Date, CoinId, Open, High, Low, Close, Volume, MarketCap) '.format(i)
            statement += 'VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
            cur.execute(statement, insertion)
    #Close database connection
    conn.commit()
    conn.close()

#####Functions for Data Extraction From DB (For Test Cases)

def pull_data_from_table(coin_name, limit=5, desc=True):
    conn = sqlite3.connect('crypto.sqlite')
    cur = conn.cursor()
    statement = 'SELECT * FROM {}  '.format(coin_name)
    if desc==True:
        statement += 'ORDER BY High DESC LIMIT {}'.format(limit)
    else:
        statement += 'ORDER BY High LIMIT {}'.format(limit)
    cur.execute(statement)
    return_list = []
    for i in cur:
        return_list.append(i)
    return return_list

def pull_join_data_from_tables(coin_name1, coin_name2, key_word, limit=5, desc=True):
    conn= sqlite3.connect('crypto.sqlite')
    cur= conn.cursor()
    if key_word == 'High':
        statement = '''
        SELECT {}.High, {}.High
        FROM Cryptos JOIN {}
        ON {}.ID = Cryptos.Id
        JOIN {} ON {}.ID = Cryptos.Id ORDER BY {}.High DESC LIMIT {}
        '''.format(coin_name1, coin_name2, coin_name1, coin_name1, coin_name2, coin_name2, coin_name1, limit)
        cur.execute(statement)
        return_list = []
        for i in cur:
            return_list.append(i)
        return return_list
    elif key_word == 'Low':
        statement = '''
        SELECT {}.Low, {}.Low
        FROM Cryptos JOIN {}
        ON {}.ID = Cryptos.Id
        JOIN {} ON {}.ID = Cryptos.Id ORDER BY {}.Low
        '''.format(coin_name1, coin_name2, coin_name1, coin_name1, coin_name2, coin_name2, coin_name1)
        if desc==True:
            statement+= 'DESC LIMIT {}'.format(limit)
        else:
            statement+= 'LIMIT {}'.format(limit)
        cur.execute(statement)
        return_list=[]
        for i in cur:
            return_list.append(i)
        return return_list
    elif key_word == 'Volume':
        statement = '''
        SELECT {}.Volume, {}.Volume
        FROM Cryptos JOIN {}
        ON {}.ID = Cryptos.Id
        JOIN {} ON {}.ID = Cryptos.Id ORDER BY {}.Volume
        '''.format(coin_name1, coin_name2, coin_name1, coin_name1, coin_name2, coin_name2, coin_name1)
        if desc==True:
            statement+= 'DESC LIMIT {}'.format(limit)
        else:
            statement+= 'LIMIT {}'.format(limit)
        cur.execute(statement)
        return_list=[]
        for i in cur:
            return_list.append(i)
        return return_list
    elif key_word == 'Open':
        statement = '''
        SELECT {}.Open, {}.Open
        FROM Cryptos JOIN {}
        ON {}.ID = Cryptos.Id
        JOIN {} ON {}.ID = Cryptos.Id ORDER BY {}.Open
        '''.format(coin_name1, coin_name2, coin_name1, coin_name1, coin_name2, coin_name2, coin_name1)
        if desc==True:
            statement+= 'DESC LIMIT {}'.format(limit)
        else:
            statement+= 'LIMIT {}'.format(limit)
        cur.execute(statement)
        return_list=[]
        for i in cur:
            return_list.append(i)
        return return_list
    elif key_word == 'Close':
        statement = '''
        SELECT {}.Close, {}.Close
        FROM Cryptos JOIN {}
        ON {}.ID = Cryptos.Id
        JOIN {} ON {}.ID = Cryptos.Id ORDER BY {}.Close
        '''.format(coin_name1, coin_name2, coin_name1, coin_name1, coin_name2, coin_name2, coin_name1)
        if desc==True:
            statement+= 'DESC LIMIT {}'.format(limit)
        else:
            statement+= 'LIMIT {}'.format(limit)
        cur.execute(statement)
        return_list=[]
        for i in cur:
            return_list.append(i)
        return return_list
    elif key_word == 'MarketCap':
        statement = '''
        SELECT {}.MarketCap, {}.MarketCap
        FROM Cryptos JOIN {}
        ON {}.ID = Cryptos.Id
        JOIN {} ON {}.ID = Cryptos.Id ORDER BY {}.MarketCap
        '''.format(coin_name1, coin_name2, coin_name1, coin_name1, coin_name2, coin_name2, coin_name1)
        if desc==True:
            statement+= 'DESC LIMIT {}'.format(limit)
        else:
            statement+= 'LIMIT {}'.format(limit)
        cur.execute(statement)
        return_list=[]
        for i in cur:
            return_list.append(i)
        return return_list


##### IMPLEMENTATION


URL = 'https://coinmarketcap.com/'
x = make_request_using_cache(URL)
x_soup = BeautifulSoup(x, 'html.parser')

table = x_soup.find('div', {'class': 'table-fixed-column-mobile compact-name-column'})

table_rows = table.find_all('tr')

coin_class_list = table_rows_to_objects(table_rows[1:])


data_per_day = get_data_per_coin(coin_class_list)
conn = sqlite3.connect('crypto.sqlite')
cur = conn.cursor()
crypto_name_list = [name for name in data_per_day]

###### GRAPHING

def market_cap_graph(date, crypto_name_list= crypto_name_list):
    conn = sqlite3.connect('crypto.sqlite')
    cur = conn.cursor()
    labels_for_graph = []
    values_for_graph = []

    for i in crypto_name_list:
        try:
            statement = '''
            SELECT Cryptos.Name, {}.MarketCap FROM {} JOIN Cryptos ON {}.CoinId = Cryptos.Id WHERE {}.Date LIKE '{}'
            '''.format(i, i, i, i, date)
            cur.execute(statement)
            for x,y in cur:
                labels_for_graph.append(x)
                values_for_graph.append(y)
        except:
            pass
    trace = go.Pie(labels=labels_for_graph, values=values_for_graph)
    py.plot([trace], filename='Market Share For {}'.format(date))

def graph_high_low_open_close(coin_name):
    conn = sqlite3.connect('crypto.sqlite')
    cur = conn.cursor()
    labels_for_graph = []
    high_values_for_graph= []
    low_values_for_graph = []
    open_values_for_graph = []
    close_values_for_graph = []

    statement = '''
            SELECT Date, High, Low , Open, Close FROM "{}" ORDER BY ID DESC
                '''.format(coin_name)
    cur.execute(statement)
    for i, j, k, l, m in cur:
        t = datetime.strptime(i.replace(',', ''), '%b %d %Y')
        labels_for_graph.append(t)
        high_values_for_graph.append(j)
        low_values_for_graph.append(k)
        open_values_for_graph.append(l)
        close_values_for_graph.append(m)
    trace = go.Ohlc(x=labels_for_graph,
                open=open_values_for_graph,
                high=high_values_for_graph,
                low=low_values_for_graph,
                close=close_values_for_graph)



    data = [trace]

    py.plot(data, filename='High-Low-Open-Close For {}'.format(coin_name))

def graph_box_plots(crypto_name_list):
    conn = sqlite3.connect('crypto.sqlite')
    cur = conn.cursor()
    counter = 1
    data = []
    data_dict ={}
    for name in crypto_name_list:
        try:
            statement = "SELECT High FROM {}".format(name)
            cur.execute(statement)
            values = []
            for i in cur:
                values.append(i[0])
            trace =go.Box(
                    y=values,
                    name = '{}'.format(name),
                )
            data.append(trace)
        except:
            pass
    py.plot(data)

def graph_line_plots_list(crypto_name_list):
    conn = sqlite3.connect('crypto.sqlite')
    cur = conn.cursor()
    counter = 1
    data = []
    data_dict ={}
    for name in crypto_name_list:
        try:
            statement = "SELECT Date, High FROM {} ORDER BY ID DESC".format(name)
            cur.execute(statement)
            values = []
            labels = []
            for i in cur:
                labels.append(i[0])
                values.append(i[1])
            trace =go.Scatter(
                    x = labels,
                    y=values,
                    name = '{}'.format(name),
                )
            data.append(trace)
        except:
            pass
    py.plot(data)

def two_line_graph(coin_name1, coin_name2):
    conn = sqlite3.connect('crypto.sqlite')
    cur = conn.cursor()
    labels_for_graph = []
    highs_coin_name1= []
    highs_coin_name2 = []
    statement = '''
    SELECT Date, High FROM "{}" ORDER BY Date
    '''.format(coin_name1)
    cur.execute(statement)
    for i, j in cur:
        labels_for_graph.append(i)
        highs_coin_name1.append(j)
    statement ='''
    SELECT High FROM "{}" ORDER BY Date
    '''.format(coin_name2)
    cur.execute(statement)
    for k in cur:
        highs_coin_name2.append(k)
    conn.close()

    trace0 = go.Scatter(
    x = labels_for_graph,
    y = highs_coin_name1,
    name = "High for {}".format(coin_name1),
    line = dict(
        color = ('rgb(22, 96, 167)'),
        width = 4,)
    )
    trace1 = go.Scatter(
    x = labels_for_graph,
    y = highs_coin_name2,
    name = "High for {}".format(coin_name2),
    line = dict(
        color = ('rgb(205, 12, 24)'),
        width = 4,)
    )

    data = [trace0, trace1]

    layout = dict(title = 'Highs of {} vs {}'.format(coin_name1, coin_name2),
                xaxis = dict(title='Date'),
                yaxis = dict(title='Value ($)'))
    fig = dict(data=data, layout=layout)
    py.plot(fig, filename='Highs for 2 Coins')

def volatility_graph(coin_name):
    conn = sqlite3.connect('crypto.sqlite')
    cur = conn.cursor()
    labels_for_graph=[]
    values_for_graph=[]
    statement = '''
    SELECT Date, High, Low FROM "{}" ORDER BY Date
    '''.format(coin_name)
    cur.execute(statement)
    for i, j, k in cur:
        labels_for_graph.append(i)
        value = j-k
        values_for_graph.append(value)
    conn.close()
    trace1 = go.Scatter(
    x = labels_for_graph,
    y = values_for_graph,
    name = "High for {}".format(coin_name),
    line = dict(
        color = ('rgb(205, 12, 24)'),
        width = 4,)
    )

    data = [trace1]

    layout = dict(title = 'Volatility of {}'.format(coin_name),
                xaxis = dict(title='Date'),
                yaxis = dict(title='Value ($)'))
    fig = dict(data=data, layout=layout)
    py.plot(fig, filename = 'Volatility')

def two_volatility(coin_name, coin_name2):
    conn = sqlite3.connect('crypto.sqlite')
    cur = conn.cursor()
    labels_for_graph=[]
    values_for_graph=[]
    values_for_graph2 =[]
    statement = '''
    SELECT Date, High, Low FROM "{}" ORDER BY Date
    '''.format(coin_name)
    cur.execute(statement)
    for i, j, k in cur:
        labels_for_graph.append(i)
        value = j-k
        values_for_graph.append(value)
    trace1 = go.Scatter(
    x = labels_for_graph,
    y = values_for_graph,
    name = "High-Low for {}".format(coin_name),
    line = dict(
        color = ('rgb(205, 12, 24)'),
        width = 4,)
    )

    statement = '''
    SELECT Date, High, Low FROM "{}" ORDER BY Date
    '''.format(coin_name2)
    cur.execute(statement)
    for i, j, k in cur:
        labels_for_graph.append(i)
        value = j-k
        values_for_graph2.append(value)
    conn.close()
    trace2 = go.Scatter(
    x = labels_for_graph,
    y = values_for_graph2,
    name = "High-Low for {}".format(coin_name),
    line = dict(
        color = ('rgb(22, 96, 167)'),
        width = 4,)
    )
    data = [trace1, trace2]

    layout = dict(title = 'Volatility of {}'.format(coin_name),
                xaxis = dict(title='Date'),
                yaxis = dict(title='Value ($)'))
    fig = dict(data=data, layout=layout)
    py.plot(fig, filename = 'Volatility')

def graph_volatility_list(crypto_name_list):
    conn = sqlite3.connect('crypto.sqlite')
    cur = conn.cursor()
    counter = 1
    data = []
    for name in crypto_name_list:
        try:
            statement = "SELECT Date, High, Low FROM {} ORDER BY ID DESC".format(name)
            cur.execute(statement)
            values = []
            labels = []
            for i in cur:
                labels.append(i[0])
                values.append(i[1]-i[2])
            trace =go.Scatter(
                    x = labels,
                    y=values,
                    name = '{}'.format(name),
                )
            data.append(trace)
        except:
            pass
    py.plot(data)


#DATA SUCCESSFULLY INSERTED INTO DATABASE
init_dbs(data_per_day)
insert_crypto_data(data_per_day)



#Interactivity
def interactive(input_words):
    input_list = input_words.split()
    if 'mcap' in input_words:
        try:
            date = input_words[5:]
            market_cap_graph(date)
        except:
            print('Invalid input, please try again...')

    elif len(input_list)==1:
        try:
            graph_high_low_open_close(input_list[0])
        except:
            print('Invalid input, please try again...')

    elif input_list[0]== 'box':
        try:
            crypto_list = input_list[1:]
            graph_box_plots(crypto_list)
        except:
            print('Invalid input, please try again...')

    elif input_list[0] == 'line':
        try:
            crypto_list = input_list[1:]
            graph_line_plots_list(crypto_list)
        except:
            print('Invalid input, please try again...')
    elif input_list[0]=='volatility':
        try:
            crypto_list = input_list[1:]
            graph_volatility_list(crypto_list)
        except:
            print('Invalid input, please try again...')
    else:
        print('Invalid input, please try again...')

def load_help_text():
    with open('help.txt') as f:
        return f.read()

if __name__ == "__main__":
    words= ''
    while words != 'exit':
        words = input('Type a command to get a graph (type "help" to get more information): ')
        if words == 'exit':
            print('Bye!')

        elif words == 'help':
            help_text = load_help_text()
            print(help_text)
            continue

        else:
            interactive(words)
            continue
