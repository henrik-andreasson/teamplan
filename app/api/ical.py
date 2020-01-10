from app.api import bp
from flask import jsonify, current_app
from app.models import User, Work, Service, Absence, Oncall, NonWorkingDays
from flask import url_for
from app import db
from app.api.errors import bad_request
from flask import request
from app.api.auth import basic_auth
from icalendar import  vCalAddress, vText, Event, Alarm
from icalendar import Calendar as icale
import pytz
from datetime import datetime, date, timedelta
from sqlalchemy import func, or_, and_
from dateutil import relativedelta


@bp.route('/ical/')
@basic_auth.login_required
def ical():

    username = request.args.get('username')
    service = request.args.get('service')

#    work = Work.query.all()

    today = datetime.utcnow()
    next_month = today + relativedelta.relativedelta(months=1)

    date_min = today.strftime("%Y-%m-%d 00:00:00")
    date_max = next_month.strftime("%Y-%m-%d 23:59:00")

    print("search range: %s->%s" %(date_min,date_max))

    if service is not None:
        work = Work.query.filter(Work.service == service,
                                func.datetime(Work.start) > date_min,
                                func.datetime(Work.start) < date_max
                                ).order_by(Work.service)

        oncall = Oncall.query.filter( (Oncall.service == service) &
                                      (func.datetime(Oncall.start) > date_min) &
                                      (func.datetime(Oncall.start) < date_max)
                                    ).order_by(Oncall.service)

    elif username is not None:
        work = Work.query.filter(Work.username == username,
                                func.datetime(Work.start) > date_min,
                                func.datetime(Work.start) < date_max
                                ).order_by(Work.service)

        oncall = Oncall.query.filter( (Oncall.username == username) &
                                      (func.datetime(Oncall.start) > date_min ) &
                                      (func.datetime(Oncall.start) < date_max )
                                    ).order_by(Oncall.service)

    else:
        work = Work.query.filter(func.datetime(Work.start) > date_min,
                        func.datetime(Work.start) < date_max
                        ).order_by(Work.service)

        oncall = Oncall.query.filter( (func.datetime(Oncall.start) > date_min ) &
                                  (func.datetime(Oncall.start) < date_max )
                                ).order_by(Oncall.service)


    reminderHours = 1
    cal = icale()

#    cal.add('prodid', '-//My calendar product//schma.cs//')
#    cal.add('version', '2.0')

    for w in work:
        user = User.query.filter(User.username == w.username).first()
        event = Event()
        event.add('summary', "%s@%s" % (w.username, w.service))
        event.add('dtstart', w.start)
        event.add('dtend', w.stop)
        event.add('dtstamp', w.stop)

        organizer = vCalAddress('MAILTO:schema@cgi.com')
        organizer.params['cn'] = vText('Schema system')
        event['organizer'] = organizer

        attendee = vCalAddress('MAILTO:%s' % user.email)
        attendee.params['cn'] = vText(w.username)
        attendee.params['ROLE'] = vText('REQ-PARTICIPANT')
        event.add('attendee', attendee, encode=0)

        cal.add_component(event)

        alarm = Alarm()
        alarm.add("action", "DISPLAY")
        alarm.add('description', "Reminder")
        alarm.add("TRIGGER;RELATED=START", "-PT{0}H".format(reminderHours))
        event.add_component(alarm)
        cal.add_component(event)


    for oc in oncall:
        event = Event()
        user = User.query.filter(User.username == oc.username).first()

        event.add('summary', "%s@%s" % (oc.username, oc.service))
        event.add('dtstart', oc.start)
        event.add('dtend', oc.stop)
        event.add('dtstamp', oc.stop)

        organizer = vCalAddress('MAILTO:schema@cgi.com')
        organizer.params['cn'] = vText('Schema system')
        event['organizer'] = organizer

        attendee = vCalAddress('MAILTO:%s' % user.email)
        attendee.params['cn'] = vText(oc.username)
        attendee.params['ROLE'] = vText('REQ-PARTICIPANT')
        event.add('attendee', attendee, encode=0)

        alarm = Alarm()
        alarm.add("action", "DISPLAY")
        alarm.add('description', "Reminder")
        alarm.add("TRIGGER;RELATED=START", "-PT{0}H".format(reminderHours))
        event.add_component(alarm)
        cal.add_component(event)


    response = current_app.make_response(cal.to_ical())
    response.headers["Content-Disposition"] = "attachment; filename=calendar.ics"
    return response
