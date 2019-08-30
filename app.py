import json
import os

import cherrypy
import redis

from constants import REDIS_HOST, REDIS_PORT

class StockHound:
    @cherrypy.expose
    def index(self):
        return open('index.html')

    @cherrypy.expose
    def stock_data(self, data_date=None):
        redis_db = redis.from_url(os.environ.get("REDIS_URL"))
        all_dates = redis_db.lrange('available_days', 0, redis_db.llen('available_days'))
        all_dates = [d.decode('utf-8') for d in all_dates]
        if data_date is None:
            # For the latest date. Since dates are stored in YYYYMMDD, max gives us that.
            data_date = max(all_dates)
        else:
            if data_date not in all_dates:
                raise cherrypy.HTTPError(404)
        stock_codes = redis_db.lrange(data_date, 0, redis_db.llen(data_date))
        response = {'all_dates': all_dates, 'data_date': data_date, 'stocks': []}
        for code in stock_codes:
            stock = clean_up_stock(redis_db.hgetall(code))
            response['stocks'].append(stock)
        return json.dumps(response)

def clean_up_stock(stock):
    """
    Convert fields from bytes to str and float
    """
    stock = { key.decode('utf-8'): stock.get(key).decode('utf-8') for key in stock }
    stock['open'] = float(stock['open'])
    stock['low'] = float(stock['low'])
    stock['high'] = float(stock['high'])
    stock['close'] = float(stock['close'])
    return stock


if __name__ == '__main__':
    cherrypy.config.update({'server.socket_host': '0.0.0.0',})
    cherrypy.config.update({'server.socket_port': int(os.environ.get('PORT', '5000')),})
    cherrypy.quickstart(StockHound())

