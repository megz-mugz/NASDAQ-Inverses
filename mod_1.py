import datetime as dt
import pandas_datareader.data as web
import matplotlib.pyplot as plt


start = dt.datetime(2010, 2, 12)
now = dt.datetime.now()

# gets data for tq and sq
df = web.DataReader('tqqq', 'yahoo', start, now)
sq = web.DataReader('sqqq', 'yahoo', start, now)

# all the lists that are used throught algo
tq_pos = 0
sq_pos = 0
buying_ema = 0
macd_sema = 0
Close = []
tq_buys = []
tq_sells = []
sq_buys = []
sq_sells = []
ATC_list = []
tq_marker_buys = []
tq_marker_sells = []
sq_marker_buys = []
sq_marker_sells = []
extremes = []
stop_loss = []

# macd strategy
short_ema = df.Close.ewm(span=12, adjust=False).mean()
long_ema = df.Close.ewm(span=26, adjust=False).mean()

MACD = short_ema - long_ema
signal = MACD.ewm(span=9, adjust=False).mean()

df['macd'] = MACD
df['signal'] = signal

for i in range(0, len(df.index)):
    # collection of ema lines:
    one_ema = df.Close.ewm(span=1, adjust=False).mean()[i]
    two_ema = df.Close.ewm(span=2, adjust=False).mean()[i]
    three_ema = df.Close.ewm(span=2.5, adjust=False).mean()[i]
    five_ema = df.Close.ewm(span=5, adjust=False).mean()[i]
    eight_ema = df.Close.ewm(span=8, adjust=False).mean()[i]
    thirteen_ema = df.Close.ewm(span=13, adjust=False).mean()[i]
    twenty_one_ema = df.Close.ewm(span=21, adjust=False).mean()[i]
    thirty_four_ema = df.Close.ewm(span=34, adjust=False).mean()[i]

    # 6 ema strategy
    quick_emas = min(three_ema, five_ema, eight_ema)
    slow_emas = max(thirteen_ema, twenty_one_ema, thirty_four_ema)

    # sma lines

    df['30ma'] = df['Adj Close'].rolling(window=30).mean()[i]
    df['20ma'] = df['Adj Close'].rolling(window=20).mean()[i]

    # bollinger band
    df['20std'] = df['Adj Close'].rolling(window=20).std()[i]

    df['Upper Band'] = df['20ma'][i] + (df['20std'][i] * 1.75)
    df['Lower Band'] = df['20ma'][i] - (df['20std'][i] * 2)

    # generate candlesticks:
    entire_candlestick = df["High"][i] - df['Low'][i]
    green_or_red = df['Adj Close'][i] - df['Open'][i]
    # green candle
    if green_or_red > 0:
        body = df['Adj Close'][i] - df['Open'][i]
        upper_wick = df['High'][i] - df['Close'][i]
        lower_wick = df['Open'][i] - df['Low'][i]
    # red candle
    else:
        body = df['Open'][i] - df['Adj Close'][i]
        upper_wick = df['High'][i] - df['Open'][i]
        lower_wick = df['Close'][i] - df['Low'][i]

    # intra algo references:
    tq_close = df['Adj Close'][i]
    ATC_list.append(tq_close)
    sq_close = sq['Adj Close'][i]
    df['buying_ema'] = three_ema

    def opening_long():
        tq_buying_price = tq_close
        tq_buys.append(tq_buying_price)
        tq_marker_buys.append(i)
        print('{} **Entry TQQQ: ', tq_buying_price.round(2))

    def close_long():
        tq_selling_price = tq_close
        tq_marker_sells.append(i)
        tq_sells.append(tq_selling_price)
        print('**Closing TQQQ: ', tq_selling_price.round(2))
    def opening_short():
        sq_buying_price = sq_close
        sq_marker_buys.append(i)
        sq_buys.append(sq_buying_price)
        print('--Opening SQQQ: ', sq_buying_price.round(2))
    def closing_short():
        sq_selling_price = sq_close
        sq_marker_sells.append(i)
        sq_sells.append(sq_selling_price)
        print('--Closing SQQQ: ', sq_selling_price.round(2))
    def opening_long():
        tq_buying_price = tq_close
        tq_buys.append(tq_buying_price)
        tq_marker_buys.append(i)
        print("**Opening TQQQ: ", tq_buying_price.round(2))

# opening long position rules
    if df['macd'][i] > df['signal'][i] and df['High'][i] > three_ema and tq_pos == 0 and sq_pos == 0:
        tq_pos = 1
        macd_sema = 1
        opening_long()

    elif quick_emas > slow_emas and tq_pos == 0 and sq_pos == 0 and tq_close > eight_ema:
        tq_pos = 1
        opening_long()

    elif df['High'][i] >= df['buying_ema'][i] and tq_pos == 0 and sq_pos == 0:
        tq_pos = 1
        buying_ema = 1
        opening_long()

# closing long & opening short
    elif tq_close < df['30ma'][i] and tq_pos == 1 and sq_pos == 0 and macd_sema == 0:
        tq_pos = 0
        close_long()
        sq_pos = 1
        opening_short()

    elif tq_close <= df['Adj Close'][i - 1] - (df['Adj Close'][i - 1] * 0.105) and df['Volume'][i] > df['Volume'][i - 1] and tq_pos == 1 and sq_pos == 0:
        tq_pos = 0
        close_long()
        sq_pos = 1
        opening_short()

    elif tq_close < df['20ma'][i] and tq_pos == 1 and sq_pos == 0 and buying_ema == 0:
        tq_pos = 0
        close_long()
        sq_pos = 1
        opening_short()

# closing long (lock in profit)
    elif tq_pos == 1 and sq_pos == 0 and tq_close >= (tq_buys[-1] + (tq_buys[-1] * 0.125)) and tq_close <= eight_ema:
        tq_pos = 0
        close_long()

# closing short and opening long
    elif quick_emas > slow_emas and tq_pos == 0 and sq_pos == 1:
        sq_pos = 0
        closing_short()
        tq_pos = 1
        opening_long()

# lock in profit (short)
    elif df['macd'][i] > df['signal'][i] and tq_close > df['20ma'][i] and tq_pos == 0 and sq_pos == 1:
        sq_pos = 0
        closing_short()

    # weak candlestick
    elif lower_wick > body and tq_close < df['30ma'][i] and df['Volume'][i] < df['Volume'][i - 1] and tq_pos == 0 and sq_pos == 1:
        sq_pos = 0
        closing_short()
# find extreme values
    elif tq_close >= df['Upper Band'][i] or tq_close <= df['Lower Band'][i]:
        extremes.append(i)

# print prices
    elif tq_pos == 1 and sq_pos == 0:
        print("TQQQ Position Open: ", tq_close.round(2))
        continue

    elif sq_pos == 1 and tq_pos == 0:
        print("SQQQ Position Open: ", sq_close.round(2))
        continue

    elif tq_pos == 0 and sq_pos == 0:
        print("NO Position Open: ", 'tq:', tq_close.round(2), 'sq:', sq_close.round(2))
        continue

percent_change = []
tq_wins = []
tq_losses = []
sq_wins = []
sq_losses = []
size_sq_win = []
size_tq_win = []

total_pc_change = []
np_list = []
def tq_win_loss_amt():
    # calculates TQQQ wins & losses
    if tq_buys != tq_sells:
        del tq_buys[-1]

    for trades in range(len(tq_buys)):
        tq_deci_pc = ((tq_sells[trades] - tq_buys[trades]) / tq_buys[trades])
        percent_change.append(tq_deci_pc)

        pc = ((tq_sells[trades] - tq_buys[trades]) / tq_buys[trades]) * 100

        if pc < 0:
            tq_losses.append(pc)
        else:
            tq_wins.append(pc)
            size_tq_win.append(tq_deci_pc)
def sq_win_loss_amt():

    if sq_buys != sq_sells:
        del sq_buys[-1]

    for trades in range(len(sq_buys)):
        sq_deci_pc = ((sq_sells[trades] - sq_buys[trades]) / sq_buys[trades])
        percent_change.append(sq_deci_pc)
        pc = ((sq_sells[trades] - sq_buys[trades]) / sq_buys[trades]) * 100

        if pc < 0:
            sq_losses.append(pc)
        else:
            sq_wins.append(pc)
            size_sq_win.append(sq_deci_pc)
def algo_money_calc():
    principle = 1000
    og_principle = principle
    for y in range(0, len(percent_change)):
        np = principle + (principle * percent_change[y])
        principle = np
        total_pc_change.append(np)
    print('-----Summary-----')
    print('Algo trading turned {} into {}, (realized profit)'.format(og_principle, principle.round(2)))
def printers():
    print('Total Trades:', len(tq_sells) + len(sq_sells))
    print('TQQQ Win %:', (len(tq_wins) / (len(tq_wins) + len(tq_losses))) * 100)
    print('--Average TQQQ Win in %: ', ((sum(size_tq_win) / len(tq_wins)) * 100).round(2))
    print('SQQQ Win %:', (len(sq_wins) / (len(sq_wins) + len(sq_losses))) * 100)
    print('--Average SQQQ Win in %: ', ((sum(size_sq_win) / len(sq_wins)) * 100).round(2))
def visualization():
    plt.style.use('dark_background')

    fig, ax = plt.subplots(nrows=2, ncols=1, sharex=True)
    plt.suptitle('Inverse ETF Chart')
    # define the two graphs
    tq_graph = ax[0]

    sq_graph = ax[1]

    # bollinger band
    df['20ma'] = df['Adj Close'].rolling(window=20).mean()
    df['30ma'] = df['Adj Close'].rolling(window=30).mean()
    df['20std'] = df['Adj Close'].rolling(window=20).std()
    df['8ema'] = df.Close.ewm(span=8, adjust=False).mean()

    df['Upper Band'] = df['20ma'] + (df['20std'] * 1.75)
    df['Lower Band'] = df['20ma'] - (df['20std'] * 2)

    # tq graph (top graph)
    # lines
    tq_graph.plot(df.index, df['Adj Close'], color='white', lw=1)
    tq_graph.plot(df.index, df['Upper Band'], color='purple', ls='dashed', label='Upper Band')
    tq_graph.plot(df.index, df['Lower Band'], color='purple', ls='dashed', label='Lower Band')
    tq_graph.plot(df.index, df['20ma'], color='purple', ls='solid', label='20 SMA')
    tq_graph.plot(df.index, df['30ma'], color='blue', ls='solid', label='30 SMA')
    tq_graph.plot(df.index, df['8ema'], color='red', ls='solid', label='8 EMA')
    tq_graph.plot(df.index, df['Adj Close'], color='white', lw=1, markevery=tq_marker_buys, marker='^',
                  markerfacecolor='green', markersize=15, alpha=0.5, markeredgecolor='green')
    tq_graph.plot(df.index, df['Adj Close'], color='white', lw=1, markevery=tq_marker_sells, marker='v',
                  markerfacecolor='red', markersize=15, alpha=0.5, markeredgecolor='red')
    tq_graph.plot(df.index, df['Adj Close'], color='white', lw=1, markevery=extremes, marker='o',
                  markerfacecolor='purple', markersize=5, alpha=0.5, markeredgecolor='purple')


    # axis titles
    tq_graph.set_title('TQQQ Graph', fontsize=15, color='white')
    tq_graph.set_ylabel('Price', fontsize=15)

    # cod
    tq_graph.legend(loc='best')

    # sq graph (bottom graph)
    sq_graph.plot(sq.index, sq['Adj Close'], color='white', lw=2)
    sq_graph.set_title('SQQQ Graph', fontsize=15, color='white')
    sq_graph.set_ylabel('Price', fontsize=15)
    sq_graph.plot(sq.index, sq['Adj Close'], color='white', lw=2, markevery=sq_marker_buys, marker='^',
                  markerfacecolor='green',markersize=15, alpha=0.5, markeredgecolor='green')
    sq_graph.plot(sq.index, sq['Adj Close'], color='white', lw=2, markevery=sq_marker_sells, marker='v',
                  markerfacecolor='red',markersize=15, alpha=0.5, markeredgecolor='red')
    sq_graph.set_ylim([0, 50])

    plt.show()


tq_win_loss_amt()
sq_win_loss_amt()
algo_money_calc()
printers()
visualization()
