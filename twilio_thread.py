from threading import Thread
from twilio.rest import Client
from twilio.http.http_client import TwilioHttpClient

class TwilioThread(Thread):
  
  def __init__(
    self,
    account_sid,
    auth_token,
    from_number,
    to_number,
    body
  ):
    Thread.__init__(self)
    
    self.response = None

    self.client = Client(
      username=account_sid,
      password=auth_token,
      http_client=TwilioHttpClient(
        max_retries=10,
        timeout=10
      )
    )

    self.from_number = from_number
    self.to_number = to_number
    self.body = body

  def run(self):
    try:
      self.response = self.client.messages.create(
        body=self.body,
        from_=self.from_number,
        to=self.to_number
      )
    except Exception as err:
      self.response = err
