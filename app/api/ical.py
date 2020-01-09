from app.api import bp
from flask import jsonify, current_app
from app.models import Work, User, Service
from flask import url_for
from app import db
from app.api.errors import bad_request
from flask import request
from app.api.auth import basic_auth
from icalendar import  vCalAddress, vText, Event
from icalendar import Calendar as icale
import pytz


@bp.route('/ical/')
@basic_auth.login_required
def ical():

    work = Work.query.all()


    cal = icale()

#    cal.add('prodid', '-//My calendar product//schma.cs//')
#    cal.add('version', '2.0')

    for w in work:
        event = Event()
        event.add('summary', "%s@%s" % (w.username, w.service))
        event.add('dtstart', w.start)
        event.add('dtend', w.stop)
        event.add('dtstamp', w.stop)

        organizer = vCalAddress('MAILTO:schema@cgi.com')
        organizer.params['cn'] = vText('Schema system')
        event['organizer'] = organizer

        attendee = vCalAddress('MAILTO:%s@example.com' % w. username)
        attendee.params['cn'] = vText(w.username)
        attendee.params['ROLE'] = vText('REQ-PARTICIPANT')
        event.add('attendee', attendee, encode=0)

        cal.add_component(event)

    response = current_app.make_response(cal.to_ical())
    response.headers["Content-Disposition"] = "attachment; filename=calendar.ics"
    return response
