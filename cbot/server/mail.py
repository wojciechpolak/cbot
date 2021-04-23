"""
# mail.py
#
# CBot Copyright (C) 2022 Wojciech Polak
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import smtplib

from cbot.server import config
from cbot.server.logger import logger


def send_mail(body: str = ''):
    mail_conf = config.conf.sections['mail']

    mail_server = mail_conf.get('server')
    if not mail_server:
        logger.error('Missing mail config')
        return

    mail_port = mail_conf.get('port')
    mail_user = mail_conf.get('user')
    mail_pass = mail_conf.get('pass')
    mail_sender = mail_conf.get('sender')
    recipient = mail_conf.get('recipient')
    subject_desc = mail_conf.get('subject_desc')

    to_addrs = [recipient]
    subject = 'CBot Notification'

    if subject_desc:
        subject += f' [{subject_desc}]'

    email_text = f'From: {mail_sender}\n'
    email_text += f'To: {", ".join(to_addrs)}\n'
    email_text += f'Subject: {subject}\n'
    email_text += '\n'
    email_text += body

    logger.debug('mail: %s', email_text)

    try:
        server = smtplib.SMTP_SSL(mail_server, mail_port)
        server.ehlo()
        server.login(mail_user, mail_pass)
        server.sendmail(mail_sender, to_addrs, email_text)
        server.close()
        logger.info('Notification email sent')
    except Exception:
        logger.exception('mail: Something went wrong...')
