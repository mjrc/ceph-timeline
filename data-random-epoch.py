from datetime import datetime
import random
import json
from pprint import pprint
import calendar

FILENAME = './data.json'

data = json.load(open(FILENAME))

for element in data: 
    year = random.randint(1970, 2018)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    hour = random.randint(0, 23)
    min = random.randint(0, 59)
    sec = random.randint(0, 59)

    random_date = datetime(year, month, day, hour, min, sec).strftime('%s')
    
    element['mtime'] = random_date



with open(FILENAME, 'w') as outfile:
    json.dump(data, outfile)



