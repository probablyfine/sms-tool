from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label

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
class DataGrid(GridLayout):

  def __init__(self, *args, **kwargs):
    super(DataGrid, self).__init__(*args, **kwargs)
    
    # Used for numbering each data row sequentially
    self.next_num = 0
    
    # Stores the widgets for each data row
    self.data_rows = dict()
      
  def add_row(
    self,
    first_name,
    last_name,
    phone_number,
    status
  ):
      
    self.next_num += 1
    
    c1 = DataCell(
      text=f'[b]{self.next_num}[/b]',
      size_hint_x=None,
      width='30dp'
    )
    c2 = DataCell(text=first_name)
    c3 = DataCell(text=last_name)
    c4 = DataCell(text=phone_number)
    c5 = DataCell(
      text=status,
      size_hint_x=None,
      width='110dp'
    )
    
    self.data_rows[self.next_num] = (c1,c2,c3,c4,c5)
    
    self.add_widget(c1)
    self.add_widget(c2)
    self.add_widget(c3)
    self.add_widget(c4)
    self.add_widget(c5)

    return self.next_num
      
  def clear_rows(self):
    if self.data_rows:
      for i in range(1, self.next_num+1):
        self.remove_row(i)

  def remove_row(self, row_num):
    for c in self.data_rows[row_num]:
      self.remove_widget(c)
    self.next_num -= 1
    self.data_rows.pop(row_num)
      
  def recolor_entry(
    self,
    row_num,
    color
  ):
    for lbl in self.data_rows[row_num]:
      lbl.background_color = color
