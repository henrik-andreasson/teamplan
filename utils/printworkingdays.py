# print out all the workdays (Mon - Fri) of a month
# tested with Python24    vegaseat     01feb2007
import calendar
# change these values to your needs ...
year = 2020
month = 1     # jan=1
# makes Monday first day of week (this is the default)
calendar.setfirstweekday(calendar.MONDAY)
months = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
          'August', 'September', 'October', 'November', 'December']
days2 = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']

for day in range(1, 32):
    try:
        weekday = calendar.weekday(year, month, day)
    except ValueError:
        continue
    if weekday < calendar.SATURDAY:
        # format the result
        print("%d-%02d-%02d" % (year, month, day))
