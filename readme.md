Final Project SI 507-- Romil Shah (README)

For my final project I have decided to extract data about cryptocurrencies in order to process the data and provide graphing capabilities.  For my data I have decided to scrape the Coin Market Cap website (https://coinmarketcap.com/).  For my extraction I did not need any special API access or any secret tokens since I directly scraped the HTML available on the site.  Therefore I used the requests module directly with just the URL I wanted to access.  From the homepage, I accessed the href tag for each coin, and then accessed the price history page per coin from each coin page.  I have accessed about 100 different coins and 30 records per coin (about 3000 records with 7 columns each). To access the data in a similar way that I have, simply pip install the requests and bs4 module, and utilize the BeautifulSoup module within bs4.

I have utilized the json module in order to store data into the cache as well as utilized the sqlite3 module in order to store all of the information scraped into a database.  I have created an individual table for each cryptocurrency as well as a 'multiple joins' table containing names and coin_ids for each cryptocurrency in order to be able to join any data in all of my tables.  

The main presentation option utilized for this project was to display data graphically through plotly (plotly documentation can be found here: https://plot.ly/python/getting-started/). My program allows for visualizations of market caps, OHLC, box plots, line graphs, and volatility graphs (more information as to how to call this can be found in help.txt).

Some of the major functions used in order to pull the data were table_rows_to_objects() and get_data_per_coin() which were used to scrape the site, turn that data into objects, and then utilize those objects to scrape additional pages as well as to return information in the form of a dictionary so that it could be inputted into a database.  Functions were also utilized to initialize and input data from that dictionary into the database.  The class Coin() was used to turn each cryptocurrency information into an object and the class Coin_Per_Day() was used to turn each day of information per coin (each row) into an object. Finally, an interactivity function was used so that users could interactively call the graphing functions as well as to handle any errors gracefully.

To utilize the program simply start like any other python file. Users will be prompted to type in a command.  Here a user can type help in to get deeper understanding of what arguments to input to get specific results or exit to exit the program.  Once familiar with the documentation, users can type in a single cryptocurrency name to get a OHLC plot, type line followed by a series of cryptocurrency names to get line charts of the highs over the previous month of those currencies, box followed by a series of cryptocurrency names to receive box plots, mcap followed by a date to receive the the market caps for all cryptocurrencies on that specific day, and volatility followed by a series of cryptocurrency names to get line charts of the volatility over the past month of said cryptocurrencies. 
