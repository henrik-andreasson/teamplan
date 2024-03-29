from flask import current_app
import click
from pprint import pprint
from rocketchat_API.rocketchat import RocketChat
from app.models import Work, User, Oncall
# from datetime import datetime
from sqlalchemy import func
import time
from app import db
from datetime import datetime


def register(app):
    @app.cli.group()
    def chat():
        """chat commands."""
        pass

    @chat.command()
    @click.argument('start')
    @click.argument('stop')
    def send(start, stop):
        """send who works today."""
        print("start: %s stop: %s" % (start, stop))
#        today = datetime.utcnow()

        # display_month = '{:02d}'.format(today.month)
        # display_year = '{:02d}'.format(today.year)
        # display_day = '{:02d}'.format(today.day)

        # date_min = "%s-%s-%s 00:00" % (display_year, display_month,
        #                                   display_day)
        # date_max = "%s-%s-%s 12:31" % (display_year, display_month,
        #                                   display_day)
        dt_start = datetime.strptime(start, "%Y-%m-%d %H:%M")
        dt_stop = datetime.strptime(stop, "%Y-%m-%d %H:%M")

        work = Work.query.filter((Work.start > dt_start)
                                 & (Work.stop < dt_stop)
                                 ).all()

        rocket = RocketChat(current_app.config['ROCKET_USER'],
                            current_app.config['ROCKET_PASS'],
                            server_url=current_app.config['ROCKET_URL'])

        for w in work:
            msg = 'Upcoming work: %s\t%s\t%s\t@%s ' % (w.start, w.stop,
                                                       w.service, w.user.username)
            pprint(rocket.chat_post_message(msg, channel=current_app.
                                            config['ROCKET_CHANNEL']).json())
            time.sleep(1)

    @chat.command()
    @click.argument('start')
    @click.argument('stop')
    def oncall(start, stop):
        """send who works today."""
        print("start: %s stop: %s" % (start, stop))

        dt_start = datetime.strptime(start, "%Y-%m-%d %H:%M")
        dt_stop = datetime.strptime(stop, "%Y-%m-%d %H:%M")

        oncall = Oncall.query.filter((Oncall.start > dt_start)
                                     & (Work.stop < dt_stop)
                                     ).all()

        rocket = RocketChat(current_app.config['ROCKET_USER'],
                            current_app.config['ROCKET_PASS'],
                            server_url=current_app.config['ROCKET_URL'])

        for o in oncall:
            msg = 'oncall: %s\t%s\t%s\t@%s ' % (o.start, o.stop,
                                                o.service, o.user.username)
            pprint(rocket.chat_post_message(msg, channel=current_app.
                                            config['ROCKET_CHANNEL']).json())
            pprint(rocket.chat_post_message(msg, channel=o.user.username).json())

            time.sleep(1)

    @chat.command()
    def helpneeded():
        """send who works today."""

        dt_today = datetime.utcnow()
        print("looking for help needed after: {}".format(dt_today))
        work = Work.query.filter((Work.status != "assigned")
                                 & (Work.start > dt_today)
                                 ).order_by(Work.start)

        rocket = RocketChat(current_app.config['ROCKET_USER'],
                            current_app.config['ROCKET_PASS'],
                            server_url=current_app.config['ROCKET_URL'])

        for w in work:
            if w.status == "unassigned":
                msg = 'Hey manager: @{} assign these shifts/work : {}\t{}\t{}\t{}'.format(
                        w.service.manager.username,
                        w.start,
                                  w.stop,
                                  w.status,
                                  w.service.name)

            elif w.status == "needs-out":
                msg = 'Hey manager: @{}, help @{} who needs-out from this shift\nservice:{} start:{} stop: {} status: *{}*'.format(
                                    w.service.manager.username,
                                    w.user.username,
                                    w.service.name,
                                    w.start,
                                    w.stop,
                                    w.status)

            elif w.status == "wants-out":
                msg = 'Hey team @all please find it in your heart to help @{} with this shift\n{}\t{}\t*{}*\t{}'.format(w.user.username,
                                w.start,
                                w.stop,
                                  w.status,
                                  w.service.name)

            else:
                msg = 'weird work update: %s\t%s\t%s\t@%s \t%s' % (w.start, w.stop,
                                                       w.service, w.user.username,
                                                       w.status)

            print(msg)
            pprint(rocket.chat_post_message(msg, channel=current_app.
                                            config['ROCKET_CHANNEL']).json())
            time.sleep(3)

    @app.cli.group()
    def user():
        """chat commands."""
        pass

    @user.command()
    @click.argument('username')
    @click.argument('password')
    @click.argument('email')
    def new(username, password, email):
        """create new user."""
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

    @user.command()
    @click.argument('username')
    @click.argument('password')
    def passwd(username, password):
        """set password user."""
        user = User.query.filter_by(username=username).first()
        if user is None:
            print("User not found")
        else:
            user.set_password(password)
            db.session.commit()

    @user.command()
    @click.argument('username')
    def admin(username):
        """set role for user."""
        user = User.query.filter_by(username=username).first()
        if user is None:
            print("User not found")
        else:
            user.set_admin()
            db.session.commit()
