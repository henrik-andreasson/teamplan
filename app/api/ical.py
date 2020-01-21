from app.api import bp
from flask import jsonify, current_app, g
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
from flask_login import login_manager
from app.api.errors import error_response


@bp.route('/ical/')
def ical():

    api_user = request.args.get('api_user')
    api_key = request.args.get('api_key')

#    fixed_api_key = "123456"
    if api_user is None:
        return error_response(401)

    user = User.query.filter_by(username=api_user).first()
    if user is None:
        return error_response(401)

    if api_key is None:
        return error_response(401)

    if User.check_api_key(user,api_key) is False:
        return error_response(401)

    # all ok
    g.current_user = user

    username = request.args.get('username')
    service = request.args.get('service')

    today = datetime.utcnow()
    prev_month = today + relativedelta.relativedelta(months=-1)
    next_month = today + relativedelta.relativedelta(months=1)

    date_min = prev_month.strftime("%Y-%m-%d 00:00:00")
    date_max = next_month.strftime("%Y-%m-%d 23:59:00")

    print("search range: %s->%s" %(date_min,date_max))

    if service is not None:
        s = Service.query.filter_by(name=service).first()
        work = Work.query.filter(Work.service_id == s.name,
                                func.datetime(Work.start) > date_min,
                                func.datetime(Work.start) < date_max
                                ).order_by(Work.service_id)

        oncall = Oncall.query.filter( (Oncall.service == service) &
                                      (func.datetime(Oncall.start) > date_min) &
                                      (func.datetime(Oncall.start) < date_max)
                                    ).order_by(Oncall.service)

    elif username is not None:
        work = Work.query.filter(Work.username == username,
                                func.datetime(Work.start) > date_min,
                                func.datetime(Work.start) < date_max
                                ).order_by(Work.service_id)

        oncall = Oncall.query.filter( (Oncall.username == username) &
                                      (func.datetime(Oncall.start) > date_min ) &
                                      (func.datetime(Oncall.start) < date_max )
                                    ).order_by(Oncall.service)

    else:
        work = Work.query.filter(func.datetime(Work.start) > date_min,
                        func.datetime(Work.start) < date_max
                        ).order_by(Work.service_id)

        oncall = Oncall.query.filter( (func.datetime(Oncall.start) > date_min ) &
                                  (func.datetime(Oncall.start) < date_max )
                                ).order_by(Oncall.service)


    reminderHours = 1
    cal = icale()

#    cal.add('prodid', '-//My calendar product//schma.cs//')
#    cal.add('version', '2.0')

    for w in work:
        user = User.query.filter_by(username = w.username).first()
        event = Event()
        event.add('summary', "%s@%s" % (w.username, w.service.name))
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
