from flask import current_app
import os
import click
from pprint import pprint
from rocketchat_API.rocketchat import RocketChat
from app.models import User, Work, Service
from calendar import Calendar
from datetime import datetime
from sqlalchemy import func
import time


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
        print("start: %s stop: %s" % (start,stop))
        today = datetime.utcnow()

        display_month = '{:02d}'.format(today.month)
        display_year = '{:02d}'.format(today.year)
        display_day = '{:02d}'.format(today.day)

        # date_min = "%s-%s-%s 00:00" % (display_year, display_month,
        #                                   display_day)
        # date_max = "%s-%s-%s 12:31" % (display_year, display_month,
        #                                   display_day)

        work = Work.query.filter(func.datetime(Work.start) > start,
                                 func.datetime(Work.stop) < stop).all()

        rocket = RocketChat(current_app.config['ROCKET_USER'], current_app.config['ROCKET_PASS'], server_url=current_app.config['ROCKET_URL'])

        for w in work:
            pprint(rocket.chat_post_message('today: %s\t%s\t%s\t@%s ' % (w.start,w.stop,w.service,w.username), channel=current_app.config['ROCKET_CHANNEL']).json())
            time.sleep(1)
