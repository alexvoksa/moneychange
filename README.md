 # moneychange
 Anti-fraud libraries for currency-exchange services.
 Made for use with Telegram API. 
 
 #### create_db.py
  - lib for creating database of currency-exchange services. Can be used to find service with best exchange rate. 
 
 #### preprocessing.py
  - lib for creating dict-based and table-based (pandas) databases (later will be upgraded for PostgreSQL).
  - Anti-fraud methods will be added to this library.  
 
 #### Verefication.py
  - lib for user-IP and phone number check. Uses MaxMind GeoIP2 library.
 
 #### telegram_bot.py
  - lib based on POST-requests. Used for handle user queries and send messages with Telegram API. 
  - **WARNING** telegram_bot.py lib use getUpdates method! This equals to short-polling and should be rewritten to webhooks or long-polling methods.
 