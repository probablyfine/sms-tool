import csv
import phonenumbers

def load_csv(path):
  with open(path, 'r', newline='') as csvfile:
    
    csv_reader = csv.reader(csvfile)
    
    if len(next(csv_reader)) < 3:
      return None

    existing_numbers = set()

    rows = []

    for row in csv_reader:
      formatted_number = format_phone_number(row[2])
      
      if not formatted_number:
        continue

      if formatted_number not in existing_numbers:
        rows.append([
          row[0],
          row[1],
          formatted_number
        ])

        existing_numbers.add(formatted_number)

    return rows

def format_phone_number(phone_string):
  if not isinstance(phone_string, str):
    return None

  try:
    parsed_number = phonenumbers.parse(phone_string, 'US')

    if phonenumbers.is_valid_number(parsed_number):
      return phonenumbers.format_number(
        parsed_number,
        phonenumbers.PhoneNumberFormat.E164
      )
    else:
      return None

  except:
    return None
