import csv
import io
import os
import zipfile

from bs4 import BeautifulSoup
import redis
import requests

from constants import REDIS_HOST, REDIS_PORT

BHAVCOPY_LINK = 'https://www.bseindia.com/markets/MarketInfo/BhavCopy.aspx'
EQUITY_HTML_ID = 'ContentPlaceHolder1_btnhylZip'
CENTURY_PREFIX = '20'

def main(zipfile_url=None):
    """
    Main function to download data, extract and upload to redis

    Parameters:
    zipfile_url (str): URL to zipfile of particular data. If blank,
    we get the latest url posted to bhavcopy.
    """
    redis_db = redis.from_url(os.environ.get("REDIS_URL"))
    if zipfile_url is None:
        zipfile_url = get_latest_zipfile_url()
    data_date = get_date_from_url(zipfile_url)
    if date_exists_in_db(redis_db, data_date):
        print(f'data for {data_date} already uploaded')
        return
    equity_csv = download_zip_and_extract_csv(zipfile_url)
    stocks_data = reorganise_csv_data(equity_csv, data_date)
    upload_to_redis(redis_db, stocks_data, data_date)

def get_latest_zipfile_url():
    """
    Get url of latest data

    Downloads the html from the BHAVCOPY_LINK site, and finds the correct
    zipfile url. NOTE: We are assuming that the id will remain unchanged
    If not, then we will have to change the logic of finding the correct
    a tag.

    Returns:
    str: The url to the zipfile with the required data
    """
    html_contents = requests.get(BHAVCOPY_LINK)
    soup = BeautifulSoup(html_contents.text, 'html.parser')
    anchor_tag = soup.find(id=EQUITY_HTML_ID)
    if anchor_tag is None:
        # The id for the zipped equity url has been changed.
        # If this error is raised, then we will need to find the new id
        # or another approach to get the correct url
        raise RuntimeError(f'Could not find the equity tag with id = {EQUITY_HTML_ID}')
    return anchor_tag.get('href')

def get_date_from_url(url):
    """
    Extract date from url

    url is structured as follow .../EQDDMMYY_CSV.ZIP
    We want in YYYYMMDD format for easy sorting.
    NOTE: This might need to be updated every 100 years. =)

    Parameters:
    url (str): The url from the bhavcopy site

    Returns:
    str: The date of the data in YYYYMMDD format
    """
    raw_date = url.split('/')[-1]
    ddmmyy = raw_date[2:8]
    dd, mm, yy = raw_date[2:4], raw_date[4:6], raw_date[6:8]
    intended_date = CENTURY_PREFIX+yy+mm+dd
    return intended_date

def date_exists_in_db(redis_db, data_date):
    """
    Check if the date already exists in database

    Parameters:
    redis_db (redis.Redis connection): Connection to redis
    data_date (str): Date in YYYYMMDD format

    Returns:
    bool: True if date exists
    """
    available_days = redis_db.lrange('available_days', 0, redis_db.llen('available_days'))
    return str.encode(data_date) in available_days

def download_zip_and_extract_csv(zip_url):
    """
    Downloads the zipfile, and unzips it in memory.

    Logic is taken from
    https://techoverflow.net/2018/01/16/downloading-reading-a-zip-file-in-memory-using-python/

    Parameters:
    zip_url (str): url to zipfile with required data

    Returns:
    str: csv file contents as a string
    """
    zipfile_response = requests.get(zip_url)
    if not zipfile_response.ok:
        raise RuntimeError(f'There was an issue with getting response to url {zip_url}')
    # TODO (29 Aug 2019 sam): Improve error checks here.
    with zipfile.ZipFile(io.BytesIO(zipfile_response.content)) as zip_contents:
        with zip_contents.open(zip_contents.namelist()[0]) as csv_contents:
            return csv_contents.read()

def reorganise_csv_data(csv_string, data_date):
    """
    Reorganize csv and keep only required details

    We want the data as a dict, where each key is the in the format
    CODE_DATE. These are the keys that will be present in the redis db
    as well. The value will contain the necessary details.

    Parameters:
    csv_string (str): The data in csv format as a string
    data_date (str): Date in YYYYMMDD format

    Returns:
    dict: Each key is code as per db rules, value is requred data fields
    """
    csv_string = csv_string.decode('utf-8').split('\r\n')
    reader = csv.DictReader(csv_string)
    stocks_for_the_day = {}
    for stock in reader:
        details = get_required_stock_details(stock)
        data_code = details['code']+'_'+data_date
        stocks_for_the_day[data_code] = details
    return stocks_for_the_day

def get_required_stock_details(stock):
    """
    Get the required details from the CSV row.

    Parameters:
    stock (dict): dict provided by csv reader

    Returns:
    dict: dict containing only the desired fields
    """
    code = stock['SC_CODE']
    name = stock['SC_NAME']
    open_ = stock['OPEN']
    high = stock['HIGH']
    low = stock['LOW']
    close = stock['CLOSE']
    return {
                'code': code,
                'name': name,
                'open': open_,
                'high': high,
                'low': low,
                'close': close
            }

def upload_to_redis(redis_db, stocks_data, data_date):
    """
    Uploads data to redis

    Parameters:
    redis_db (redis.Redis connection): Connection to redis
    stocks_data (dict): Each key is code as per db rules, value is requred data fields
    data_date (str): Date in YYYYMMDD format
    """
    for code, stock in stocks_data.items():
        redis_db.hmset(code, stock)
    redis_db.rpush(data_date, *stocks_data.keys())
    redis_db.rpush('available_days', data_date)

if __name__ == '__main__':
    main()

