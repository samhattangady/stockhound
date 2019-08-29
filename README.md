# StockHound

A simple app to view the top stocks of the given day. The project has two components:

`bhavco.py`: A python script that gets the latest bhavcopy available, and scrapes the data to store on redis.

`app.py`: A web app that serves a VueJs frontend that allows us to view the scraped data.

## Basic Features
1. On the landing page, we can view the top 10 stocks by closing price on a given day.
2. We can also sort the stocks by largest gain, largest loss or largest volatility.
3. We can search for stocks and see the basic details of that stock for that day.
4. The script is designed to run once a day and update to the latest data.

### Future Features and Improvements
1. Change the date of data being viewed. It is being stored, but no way to access it on the front end.
2. Allow users to view longer term performance of a stock after they search for it (with graph).
3. Add links to view more data for given stock on some other site.

---

###### Redis schema

To design the redis schema, a basic usecase for the app was decided. The app will currently show
the details of the top stocks on any given day. Moving forward, the app will also get the functionality
to show the performance of a particular stock over time. Taking this into consideration, the db was
designed as follows:

available\_days: list -> This list will contain strings for all the days that have been uploaded onto it.
For example: ['20190807', ..., '20190828']

20190828: list -> This list will contain all the stocks for which data is available on a particular day
For example: ['500002\_20190828', ..., '972885\_20190828']

500002\_20190828: hash -> This hash will contain the data for that stock id for that day.

So to get the details for the latest day, we query the `days` list and get the latest day.
We use that date as a query and get all the available stocks on that day.
Then we can individually query all of those stocks for the data.

Moving forward, if we need to get the performance of a particular stock for a given period of time,
we can easily just get all the available days, and prefix the stock code, and check the database,
reducing excess database reads.

---

###### Some assumptions
1. The bhavcopy link will not change. Stored as constant `BHAVCOPY_URL`
2. The anchor tag id for the latest equity will not change. Stored as constant `ContentPlaceHolder1_btnhylZip`
3. Script will be run only for current century. Stored as constant `CENTURY_PREFIX`. =)
