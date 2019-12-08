import calendar

# Create a plain text calendar
c = calendar.TextCalendar(calendar.THURSDAY)
str = c.formatmonth(2025, 1, 0, 0)
print(str)

# Create an HTML formatted calendar
hc = calendar.HTMLCalendar(calendar.THURSDAY)
str = hc.formatmonth(2025, 1)
print(str)
# loop over the days of a month
# zeroes indicate that the day of the week is in a next month or overlapping month
for i in hc.itermonthdays(2025, 4):
    print(i)

    # The calendar can give info based on local such a names of days and months (full and abbreviated forms)
    for name in calendar.month_name:
        print(name)
    for day in calendar.day_name:
        print(day)
    # calculate days based on a rule: For instance an audit day on the second Monday of every month
    # Figure out what days that would be for each month, we can use the script as shown here
    for month in range(1, 13):
		# It retrieves a list of weeks that represent the month
        mycal = calendar.monthcalendar(2025, month)
		# The first MONDAY has to be within the first two weeks
        week1 = mycal[1]
        week2 = mycal[2]
        if week1[calendar.MONDAY] != 0:
            auditday = week1[calendar.MONDAY]
        else:
        # if the first MONDAY isn't in the first week, it must be in the second week
            auditday = week2[calendar.MONDAY]

        print("%10s %2d" % (calendar.month_name[month], auditday))
