import json

import cherrypy
import redis

REDIS_HOST = 'localhost'
REDIS_PORT = 6379

class StockHound:
    @cherrypy.expose
    def index(self):
        return open('index.html')

    @cherrypy.expose
    def stock_data(self, data_date=None):
        redis_db = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        if data_date is None:
            all_dates = redis_db.lrange('available_days', 0, redis_db.llen('available_days'))
            # For the latest date. Since dates are stored in YYYYMMDD, max gives us that.
            data_date = max(all_dates)
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
        # response = response.decode('utf8').replace("'", '"')
        return json.dumps(response)


if __name__ == '__main__':
    cherrypy.quickstart(StockHound())
