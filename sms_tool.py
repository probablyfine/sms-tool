import os, sys

# Needed if packaged using PyInstaller
if hasattr(sys, '_MEIPASS'):
  os.environ['KIVY_NO_CONSOLELOG'] = '1'
  
import platform
from pathlib import Path
from requests.exceptions import ConnectionError

from util import load_csv
from widgets import FieldLabel, DataCell, DataHeader, DataRow, RV
from twilio_thread import TwilioThread
  
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.config import Config
from kivy.resources import resource_add_path, resource_find

from twilio.base.exceptions import TwilioRestException
from twilio.base.instance_resource import InstanceResource
from sms_counter import SMSCounter

clr_green  = (125/255, 184/255, 116/255, 1)
clr_red    = (217/255, 33/255,  32/255,  1)
clr_yellow = (217/255, 173/255, 60/255,  1)

# Needed if packaged using PyInstaller
if hasattr(sys, '_MEIPASS'):
  resource_add_path(
    os.path.join(
      sys._MEIPASS
    )
  )
  
Builder.load_file('sms_tool.kv')

class SMSTool(BoxLayout):
  
  def __init__(self, **kwargs):
    super(SMSTool, self).__init__(**kwargs)

    Window.bind(on_drop_file=self.handle_file_drop)

    Clock.schedule_interval(
      self
      .ids
      .recycle_view
      .refresh_visible_rows,
      1
    )

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
      .text_input_message
    ).bind(
      text=self.count_segments
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

    recycle_view = (
      self
      .ids
      .recycle_view
    )

    recycle_view.clear_rows()

    # Populate some blank rows, just so there isn't a weird empty
    # gap when no CSV is loaded
    for _ in range(6):
      recycle_view.add_row('', '', '', '')

    btn = (
      self
      .ids
      .button_send
    )
    btn.text = 'Send 0 Messages'

  def count_segments(self, *args):
    message = (
      self
      .ids
      .text_input_message
      .text
    )

    segments = SMSCounter.count(message)['messages']

    (
      self
      .ids
      .field_label_segments
      .text
    ) = f'Message ({segments} segments used):'

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

      try:
        self.csv_data = load_csv(path)
      except:
        self.csv_data = None

      text_input_contacts = (
        self
        .ids
        .text_input_contacts
      )

      if self.csv_data:
        text_input_contacts.text = str(path)
        
        self.csv_path = path
        
        self.handle_csv_load()

      else:
        text_input_contacts.text = ''

      self.check_ok_to_send()

  def handle_csv_load(self):
    recycle_view = (
      self
      .ids
      .recycle_view
    )
    
    recycle_view.clear_rows()

    for row in self.csv_data:
      recycle_view.add_row(*row, 'Not Sent')

    (
      self
      .ids
      .button_send
      .text
    ) = f'Send {len(self.csv_data)} Messages'

    self.current_message = 0 # zero-indexed

    self.check_ok_to_send()

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

    (
      self
      .ids
      .button_send
      .disabled
     ) = True

    for text_input in self.text_inputs:
      text_input.disabled = True
    
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
      Clock.schedule_once(
        self.send_next_message,
        0.01
      )
      return

    # If we have an active Twilio request AND a response, handle the response
    elif self.request_thread and self.request_thread.response:
      self.handle_request_response()
      return

    # If there's no data loaded, return
    if not self.csv_data:
      return

    # If we don't have an indicator of which message we're on, return
    if self.current_message is None:
      return

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

    recycle_view = (
      self
      .ids
      .recycle_view
    )

    current_data_row = recycle_view.data[self.current_message]

    to_number = current_data_row['phone_number']

    self.request_thread = TwilioThread(
      account_sid,
      auth_token,
      from_number,
      to_number,
      body
    )
    self.request_thread.start()

    recycle_view.update_row(
      self.current_message,
      {
        'status': 'Sending...',
        'color': clr_yellow
      }
    )

    Clock.schedule_once(
      self.send_next_message,
      0.01
    )

  def handle_request_response(self):

    def make_error_text(err_code):
      return (
        f'[ref=https://www.twilio.com/docs/api/errors/{err_code}]' +
        f'[u]Error {err_code}[/u]' +
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

      # The response might've contained an error
      if response.error_code:
        status_text = make_error_text(response.error_code)

      # If it didn't contain an error, assume the message was sent
      else:
        status_text = 'Sent'

    # This happens if we get a 400 or 500 status code from the Twilio API
    elif isinstance(
      response,
      TwilioRestException
    ):
      status_text = make_error_text(response.code)

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

    recycle_view = (
      self
      .ids
      .recycle_view
    )

    recycle_view.update_row(
      self.current_message,
      {
        'status': status_text,
        'color': color
      }
    )
    
    remaining_messages = len(self.csv_data) - self.current_message - 1

    # Update the Send button's label to show progress
    btn = self.ids.button_send
    btn.text = f'Sending {remaining_messages} Messages...'

    # Toss out the thread, we'll need to create a new one
    # for the next message we send.
    self.request_thread = None
    
    # Happens when we've sent all the messages
    if self.current_message >= len(self.csv_data) - 1:
      self.current_message = None

      btn.text = 'Finished Sending'
      btn.disabled = True

      for text_input in self.text_inputs:
        text_input.disabled = False

      self.sending = False
      self.sent = True
      return
    
    else:

      self.current_message += 1

      message_rate = float(
        self
        .ids
        .text_input_rate_limit
        .text
      )
      
      message_delay = 1 / message_rate

      Clock.schedule_once(
        self.send_next_message,
        message_delay
      )

class SMSToolApp(App):
  def build(self):
    return SMSTool()

if __name__ == '__main__':
  Config.set('input', 'mouse', 'mouse,disable_multitouch') # section, option, value
  Config.set('kivy', 'exit_on_escape', 0)

  window_width = dp(660)
  window_height = dp(776)

  # Handle weird window sizing on macOS
  if platform.system() == 'Darwin':
    window_width /= 2
    window_height /= 2

  Window.size = (window_width, window_height)
        
  SMSToolApp().run()
