from util import load_csv
from widgets import FieldLabel, DataCell, DataHeader, DataGrid

from pathlib import Path

from requests.exceptions import ConnectionError

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout

from kivy.lang import Builder
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.config import Config

from twilio.base.exceptions import TwilioRestException
from twilio.base.instance_resource import InstanceResource

from twilio_thread import TwilioThread

clr_green  = (125/255, 184/255, 116/255, 1)
clr_red    = (217/255, 33/255,  32/255,  1)
clr_yellow = (217/255, 173/255, 60/255,  1)

Builder.load_file('sms_tool.kv')

class SMSTool(BoxLayout):
  
  def __init__(self, **kwargs):
    super(SMSTool, self).__init__(**kwargs)

    Window.bind(on_drop_file=self.handle_file_drop)

    self.text_inputs = [
      self.ids.text_input_account_sid,
      self.ids.text_input_auth_token,
      self.ids.text_input_from_number,
      self.ids.text_input_message,
      self.ids.text_input_rate_limit
    ]

    for text_input in self.text_inputs:
      text_input.bind(
        text=self.check_ok_to_send
      )

    (
      self
      .ids
      .button_send
      .bind(
        on_release=self.start_sending
      )
    )
    (
      self
      .ids
      .button_pause
      .bind(
        on_release=self.pause_sending
      )
    )

    self.init_state()

  def init_state(self):
    self.csv_path = None
    self.csv_data = None
    self.request_thread = None
    self.current_message = None
    self.sending = False
    self.sent = False
    self.paused = False

    data_grid = (
      self
      .ids
      .data_grid
    )

    data_grid.clear_rows()

    # Populate some blank rows, just so there isn't a weird empty
    # gap when no CSV is loaded
    for _ in range(5):
      data_grid.add_row('', '', '', '')

    btn = (
      self
      .ids
      .button_send
    )
    btn.text = 'Send 0 Messages'

  def handle_file_drop(
    self,
    window,
    filename,
    x,
    y,
    *args
  ):
    # Don't allow loading a new file while sending
    if self.sending:
      return

    path = Path(
      filename.decode('utf-8')
    )

    if path.suffix.lower() == '.csv':

      self.init_state()

      text_input_contacts = (
        self
        .ids
        .text_input_contacts
      )

      try:
        self.csv_data = load_csv(path)
      except:
        self.csv_data = None

      if self.csv_data:
        text_input_contacts.text = str(path)
        
        self.csv_path = path
        
        self.handle_csv_load()

      else:
        text_input_contacts.text = ''

  def handle_csv_load(self):
    data_grid = (
      self
      .ids
      .data_grid
    )
    
    data_grid.clear_rows()

    for i, row in enumerate(self.csv_data):
      print(i)
      data_grid.add_row(*row, 'Not Sent')

    (
      self
      .ids
      .button_send
      .text
    ) = f'Send {len(self.csv_data)} Messages'

    self.check_ok_to_send()

    self.current_message = 1

  def check_ok_to_send(self, *args):

    inputs_are_blank = any([
      text_input.text.strip() == '' 
        for text_input in self.text_inputs
    ])

    rate_limit = (
      self
      .ids
      .text_input_rate_limit
      .text
    )
    
    btn = (
      self
      .ids
      .button_send
    )

    if (
      not inputs_are_blank and
      rate_limit != '-' and
      int(rate_limit) > 0 and
      not (self.sending or self.sent) and
      self.csv_data
    ):
      btn.disabled = False

    else:
      btn.disabled = True

  def start_sending(self, *args):
    self.paused = False
    self.sent = False
    self.sending = True

    (
      self
      .ids
      .button_pause
      .disabled
    ) = False
    
    self.send_next_message()

  def pause_sending(self, *args):
    if self.sent:
      return

    self.paused = True
    self.sending = False

    btn = self.ids.button_send
    btn.text = btn.text.replace('ing', '')

    for text_input in self.text_inputs:
      text_input.disabled = False

    self.check_ok_to_send()

  def send_next_message(self, *args):
    # If we're paused, don't do anything
    if self.paused:
      return

    # If we have an active Twilio request, but no response yet, schedule another
    # check and don't do anything else
    if self.request_thread and not self.request_thread.response:
      Clock.schedule_once(self.send_next_message, 0.01)
      return

    # If we have an active Twilio request AND a response, handle the response
    elif self.request_thread and self.request_thread.response:
      self.handle_request_response()
      return

    # If there's no data loaded, return
    if not self.csv_data:
      return

    # If we don't have an indicator of which message we're on, return
    if not self.current_message:
      return

    (
      self
      .ids
      .button_send
      .disabled
     ) = True

    for text_input in self.text_inputs:
      text_input.disabled = True

    account_sid = (
      self
      .ids
      .text_input_account_sid
      .text
    )
    auth_token = (
      self
      .ids
      .text_input_auth_token
      .text
    )
    from_number = (
      self
      .ids
      .text_input_from_number
      .text
    )
    body = (
      self
      .ids
      .text_input_message
      .text
    )

    data_grid = (
      self
      .ids
      .data_grid
    )

    current_data_row = data_grid.data_rows[self.current_message]

    to_number = current_data_row[3].text

    self.request_thread = TwilioThread(
      account_sid,
      auth_token,
      from_number,
      to_number,
      body
    )
    self.request_thread.start()

    current_data_row[4].text = 'Sending...'

    # Change current data row color to yellow
    data_grid.recolor_entry(
      self.current_message,
      clr_yellow
    )

    self.current_message += 1

    Clock.schedule_once(self.send_next_message, 0.01)

  def handle_request_response(self):

    def make_error_text(err_code):
      return (
        f'[ref=https://www.twilio.com/docs/api/errors/{err_code}]' +
        f'Error {err_code}' +
        '[/ref]'
      )

    response = (
      self
      .request_thread
      .response
    )

    # This happens when we get an actual response from Twilio
    if isinstance(
      response,
      InstanceResource
    ):
      error_code = response.error_code

      # The response might've contained an error
      if error_code:
        status_text = make_error_text(error_code)

      # If it didn't contain an error, assume the message was sent
      else:
        status_text = 'Sent'

    # This happens if we get a 400 or 500 status code from the Twilio API
    elif isinstance(
      response,
      TwilioRestException
    ):
      error_code = response.code

      status_text = make_error_text(error_code)

    # This happens if network connectivity is lost
    elif isinstance(
      response,
      ConnectionError
    ):
      status_text = 'Network Error'
    else:
      status_text = 'Error'

    if status_text == 'Sent':
      color = clr_green
    else:
      color = clr_red

    data_grid = (
      self
      .ids
      .data_grid
    )

    # Set the color of the row green if successful, red if error
    data_grid.recolor_entry(
      self.current_message - 1,
      color
    )
      
    current_cell = data_grid.data_rows[self.current_message - 1][-1]
    current_cell.text = status_text
    
    remaining_messages = len(self.csv_data) - self.current_message + 1

    # Update the Send button's label to show progress
    btn = self.ids.button_send
    btn.text = f'Sending {remaining_messages} Messages...'

    self.request_thread = None
    
    # Happens when we've sent all the messages
    if self.current_message >= len(self.csv_data) + 1:
      self.current_message = None

      self.ids.button_send.text = 'Finished Sending'
      self.ids.button_send.disabled = True

      for text_input in self.text_inputs:
        text_input.disabled = False

      self.sending = False
      self.sent = True
      return
    
    else:
      message_rate = float(
        self
        .ids
        .text_input_rate_limit
        .text
      )
      
      message_delay = 1 / message_rate

      Clock.schedule_once(self.send_next_message, message_delay)

class SMSToolApp(App):
  def build(self):
    return SMSTool()

if __name__ == '__main__':
  Config.set( 'input', 'mouse', 'mouse,disable_multitouch') # section, option, value
  Config.set( 'kivy', 'exit_on_escape', 0)
  Config.set( 'graphics', 'position', 'custom')
  
  Window.size = (dp(330), dp(380))

  SMSToolApp().run()
