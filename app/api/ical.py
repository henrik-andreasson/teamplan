from app.api import bp
from flask import jsonify, current_app, g
from app.models import User, Work, Service, Absence, Oncall, NonWorkingDays
from flask import url_for
from app import db
from app.api.errors import bad_request
from flask import request
from app.api.auth import basic_auth
from icalendar import vCalAddress, vText, Event, Alarm
from icalendar import Calendar as icale
import pytz
from pytz import timezone
from datetime import datetime, date, timedelta
from sqlalchemy import func, or_, and_
from dateutil import relativedelta
from flask_login import login_manager
from app.api.errors import error_response
import uuid


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

    if User.check_api_key(user, api_key) is False:
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

    print("search range: %s->%s" % (date_min, date_max))

    u = None
    if username is not None:
        u = User.query.filter_by(username=username).first()

    s = None
    if service is not None:
        s = Service.query.filter_by(name=service).first()

    if s is not None:
        work = Work.query.filter(Work.service_id == s.name,
                                 func.datetime(Work.start) > date_min,
                                 func.datetime(Work.start) < date_max
                                 ).order_by(Work.service_id)

        oncall = Oncall.query.filter(
         (Oncall.service_id == s.id)
         & (func.datetime(Oncall.start) > date_min)
         & (func.datetime(Oncall.start) < date_max)
         ).order_by(Oncall.service_id)

        absence = Absence.query.filter(func.datetime(Absence.start) > date_min,
                                       func.datetime(Absence.stop) < date_max
                                       ).all()

    elif u is not None:
        work = Work.query.filter((Work.user_id == u.id)
                                 & (func.datetime(Work.start) > date_min)
                                 & (func.datetime(Work.start) < date_max)
                                 ).order_by(Work.service_id)

        oncall = Oncall.query.filter((Oncall.user_id == u.id) &
                                     (func.datetime(Oncall.start) > date_min ) &
                                     (func.datetime(Oncall.start) < date_max )
                                     ).order_by(Oncall.service_id)

        absence = Absence.query.filter((Absence.user_id == u.id) &
                                       (func.datetime(Absence.start) > date_min) &
                                       (func.datetime(Absence.stop) < date_max)
                                       ).all()

    else:
        work = Work.query.filter(func.datetime(Work.start) > date_min,
                                 func.datetime(Work.start) < date_max
                                 ).order_by(Work.service_id)

        oncall = Oncall.query.filter((func.datetime(Oncall.start) > date_min) &
                                     (func.datetime(Oncall.start) < date_max)
                                     ).order_by(Oncall.service_id)

        absence = Absence.query.filter(func.datetime(Absence.start) > date_min,
                                       func.datetime(Absence.stop) < date_max
                                       ).all()

    reminderHours = current_app.config['ICAL_REMINDER_MINS']
    cal = icale()

#    cal.add('prodid', '-//My calendar product//schma.cs//')
#    cal.add('version', '2.0')

    local_tz = timezone(current_app.config['TEAMPLAN_TZ'])
    utc = pytz.utc

    for w in work:
        user = User.query.get(w.user.id)
        event = Event()
        event.add('summary', "%s@%s" % (w.user.username, w.service.name))

        event.add('dtstart', local_tz.localize(w.start).astimezone(utc))
        event.add('dtend', local_tz.localize(w.stop).astimezone(utc))
        event.add('uid', str(uuid.uuid4()) + current_app.config['ICAL_UID_DOMAIN'])
        organizer = vCalAddress('MAILTO:' + current_app.config['ICAL_INVITE_FROM'])
        organizer.params['cn'] = vText('Schema system')
        event['organizer'] = organizer

        attendee = vCalAddress('MAILTO:%s' % user.email)
        attendee.params['cn'] = vText(w.user.username)
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
        user = User.query.filter(User.username == oc.user.username).first()

        event.add('summary', "oncall: %s@%s" % (oc.user.username, oc.service.name))
        event.add('dtstart', local_tz.localize(oc.start).astimezone(utc))
        event.add('dtend', local_tz.localize(oc.stop).astimezone(utc))

        event.add('uid', str(uuid.uuid4()) + current_app.config['ICAL_UID_DOMAIN'])
        organizer = vCalAddress('MAILTO:' + current_app.config['ICAL_INVITE_FROM'])

        organizer.params['cn'] = vText('Schema system')
        event['organizer'] = organizer

        attendee = vCalAddress('MAILTO:%s' % user.email)
        attendee.params['cn'] = vText(oc.user.username)
        attendee.params['ROLE'] = vText('REQ-PARTICIPANT')
        event.add('attendee', attendee, encode=0)

        alarm = Alarm()
        alarm.add("action", "DISPLAY")
        alarm.add('description', "Reminder")
        alarm.add("TRIGGER;RELATED=START", "-PT{0}H".format(reminderHours))
        event.add_component(alarm)
        cal.add_component(event)

    for ab in absence:
        event = Event()
        user = User.query.filter(User.username == ab.user.username).first()

        event.add('summary', "absence: %s" % (ab.user.username))
        event.add('dtstart', local_tz.localize(ab.start).astimezone(utc))
        event.add('dtend', local_tz.localize(ab.stop).astimezone(utc))
        event.add('uid', str(uuid.uuid4()) + current_app.config['ICAL_UID_DOMAIN'])
        organizer = vCalAddress('MAILTO:' + current_app.config['ICAL_INVITE_FROM'])
        organizer.params['cn'] = vText('Schema system')
        event['organizer'] = organizer

        attendee = vCalAddress('MAILTO:%s' % user.email)
        attendee.params['cn'] = vText(ab.user.username)
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
