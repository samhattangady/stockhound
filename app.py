import json

import cherrypy
import redis

from constants import REDIS_HOST, REDIS_PORT

class StockHound:
    @cherrypy.expose
    def index(self):
        return open('index.html')

    @cherrypy.expose
    def stock_data(self, data_date=None):
        redis_db = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        all_dates = redis_db.lrange('available_days', 0, redis_db.llen('available_days'))
        if data_date is None:
            # For the latest date. Since dates are stored in YYYYMMDD, max gives us that.
            data_date = max(all_dates)
        else:
            # TODO (29 Aug 2019 sam): Ensure that the data date exists here
            pass
        stock_codes = redis_db.lrange(data_date, 0, redis_db.llen(data_date))
        response = {'data_date': data_date.decode('utf-8'), 'stocks': []}
        for code in stock_codes:
            bin_stock = redis_db.hgetall(code)
            stock = { key.decode('utf-8'): bin_stock.get(key).decode('utf-8') for key in bin_stock }
            stock['open'] = float(stock['open'])
            stock['low'] = float(stock['low'])
            stock['high'] = float(stock['high'])
            stock['close'] = float(stock['close'])
            response['stocks'].append(stock)
        return json.dumps(response)


if __name__ == '__main__':
    cherrypy.quickstart(StockHound())
