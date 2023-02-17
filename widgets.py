from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior

import webbrowser

# Label to the left of each input field
class FieldLabel(Label):
  def __init__(self, *args, **kwargs):
    super(FieldLabel, self).__init__(*args, **kwargs)

# Label used for showing CSV data
class DataCell(Label):
  def __init__(self, *args, **kwargs):
    super(DataCell, self).__init__(*args, **kwargs)

  # Opens web links if 'ref' Markup is used
  def on_ref_press(self, ref):
    webbrowser.open(ref)
    return super().on_ref_press(ref)

# Labels for each CSV field (First, Last, Phone)
class DataHeader(Label):
  def __init__(self, *args, **kwargs):
    super(DataHeader, self).__init__(*args, **kwargs)

# Holds all the CSV data Labels
class DataRow(
  RecycleDataViewBehavior,
  GridLayout
):
  index = None

  def __init__(self, *args, **kwargs):
    super(DataRow, self).__init__(*args, **kwargs)

    self.cell_labels = [
      self.ids.cell_index,
      self.ids.cell_first_name,
      self.ids.cell_last_name,
      self.ids.cell_phone,
      self.ids.cell_status,
    ]
      
  def refresh_view_attrs(
    self,
    rv,
    index,
    data
  ):
    self.index = index
    self.index_text = str(index+1)
    self.first_name_text = data['first_name']
    self.last_name_text = data['last_name']
    self.phone_text = data['phone_number']
    self.status_text = data['status']

    for lbl in self.cell_labels:
      lbl.background_color = data['color']
    
    return super(DataRow, self).refresh_view_attrs(
      rv,
      index,
      data
    )

class RV(RecycleView):
  def __init__(self, **kwargs):
    super(RV, self).__init__(**kwargs)
    self.clear_rows()

  def clear_rows(self):
    self.data = []

  def add_row(
    self,
    first_name,
    last_name,
    phone_number,
    status,
    color=(0.7, 0.7, 0.7, 1)
  ):
    self.data.append(
      {
        'first_name': first_name,
        'last_name': last_name,
        'phone_number': phone_number,
        'status': status,
        'color': color
      }
    )

  def update_row(
    self,
    index,
    data
  ):
    for field in [
      'first_name',
      'last_name',
      'phone_number',
      'status',
      'color'
    ]:
      if field in data:
        self.data[index][field] = data[field]

    self.refresh_visible_rows()

  def refresh_visible_rows(self):
    for w in (
      self
      .children[0] # this is a RecycleBoxLayout
      .children    # list of all currently-visible widgets
    ):
      w.refresh_view_attrs(
        self,
        w.index,
        self.data[w.index]
      )
