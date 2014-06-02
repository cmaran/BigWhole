import smtplib
import socket
from email.mime.text import MIMEText

class Mailer:
    """Makes sending mails easy.
    """

    def __init__(self, addr="127.0.0.1", port=25, default_sender=None, dummy=False):
        """

        :param server: IP of mail server
        :param port: Port of mail server
        :param default_sender: The sender (from field) which should be used by default
        :param dummy: If true, doesn't acutally send mails but loggs only to console if one would have been sent
        """
        self.addr = addr
        self.port = port
        self.dummy = dummy
        self.default_sender = default_sender

    def send_mail(self, to, subject, body, sender=None):
        """Sends a mail.

        :param to: Recipient
        :param subject: Subject
        :param body: Actuall text of the mail
        :param sender: From, Not needed if default_sender is set, overrides default_sender if given
        """
        if sender == None:
            if self.default_sender != None:
                sender = self.default_sender
            else:
                print("mailer: No sender specified!")
                return

        if self.dummy:
            print("mailer: Dummy Sent email:\n  To: %s\n  From: %s\n  Title: %s\n  Body: %s" % (to, sender, subject, body))
        else:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = sender
            msg["To"] = to

            try:
                server = smtplib.SMTP(self.addr)
                server.send_message(msg)
                server.quit()
                print("mailer: Sent email:\n  To: %s\n  From: %s\n  Title: %s\n  Body: %s" % (to, sender, subject, body))
            except (ConnectionRefusedError, socket.gaierror) as e:
                print("mailer: Couldn't connect to mailserver!")
