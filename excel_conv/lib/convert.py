from openpyxl.workbook import Workbook
from openpyxl import load_workbook
from pathlib import Path
from django.core.files import File
from datetime import datetime
from django.utils import timezone
from django.conf import settings
import os


# --------------------------------------------------
def convert_sheet(object):
    """convert_sheet function to test the conversion process"""
    
    # create the path to the temporary and converted Excel files
    out_file_path = object.excel_file.path.replace('excel_files', 'conv_files')
    out_file_path = str(out_file_path.replace('.xlsx', '_converted.xlsx'))
    temp_file_path = out_file_path.replace('.xlsx', '_temp.xlsx')

    # initialize the original workbook and worksheet
    original_workbook = Workbook()
    original_workbook = load_workbook(object.excel_file.path)
    original_worksheet = original_workbook.active
    
    # initialize the converted workbook and worksheet
    converted_workbook = Workbook()
    converted_workbook.save(temp_file_path)
    converted_workbook = load_workbook(temp_file_path)
    converted_worksheet = converted_workbook.active
    
    # write the header row to the converted spreadsheet
    header_labels = ["name", "ADDRESS_1", "City", "State", "Zip", "Creditor"]
    column_letters = "ABCDEF"
    for i, label in enumerate(header_labels):
        converted_worksheet[column_letters[i] + "1"] = label
    converted_workbook.save(temp_file_path)
    
    # we need to find the first and last debtor in the source file
    column_a = original_worksheet["A"]
    for item in column_a:
        if item.value == "No.":
            starting_row = item.row + 2
    for item in column_a:
        if item.value == "Permissible Use:":
            ending_row = item.row - 3

    # now we're going to loop through the debtor rows and convert them
    i = starting_row
    new_file_row = 2

    while i <= ending_row:
        working_row = original_worksheet[i]
        new_file_working_row = converted_worksheet[new_file_row]

        data = {
            "debtor_name": working_row[1].value,
            "debtor_address": working_row[2].value,
            "creditor": working_row[4].value,
        }

        if data["creditor"]:
            debtor_name_lines = data["debtor_name"].splitlines()
            data["debtor_name"] = debtor_name_lines[0]
            
            last_name = data["debtor_name"].split(', ')[0]
            first_name = data["debtor_name"].split(' ')[1]

            if len(data["debtor_name"].split(' ')) > 2 and data["creditor"] is not None:
                middle_name = data["debtor_name"].split(' ')[2]
                new_file_working_row[0].value = f"{first_name} {middle_name} {last_name}"
            elif data["creditor"] is not None:
                new_file_working_row[0].value = f"{first_name} {last_name}"

            data["full_name"] = f"{first_name} {middle_name} {last_name}".strip()
            
            debtor_street_address = data["debtor_address"].splitlines()[0]
            debtor_city_state_zip = data["debtor_address"].splitlines()[1]
            debtor_city = debtor_city_state_zip.split(', ')[0]
            debtor_state = debtor_city_state_zip.split(', ')[1].split(' ')[0]
            debtor_zip = debtor_city_state_zip.split(', ')[1].split(' ')[1]

            data.update(
                {
                    "debtor_street_address": debtor_street_address,
                    "debtor_city": debtor_city,
                    "debtor_state": debtor_state,
                    "debtor_zip": debtor_zip,
                    "creditor": data["creditor"],
                }
            )

            if data["creditor"] is not None:
                new_file_working_row[1].value = debtor_street_address
                new_file_working_row[2].value = debtor_city
                new_file_working_row[3].value = debtor_state
                new_file_working_row[4].value = debtor_zip
                new_file_working_row[5].value = data["creditor"]

            # for index, (key, value) in enumerate(data.items()):
            #     new_file_working_row[index].value = value

            new_file_row += 1

        converted_workbook.save(temp_file_path)
        i += 1
    
    # close the workbooks
    original_workbook.close()
    converted_workbook.close()
    
    # Create and write content to the new file
    with open(out_file_path, "wb") as file:
    # Write the content you want into the file (e.g., by copying from an existing file)
        with open(temp_file_path, "rb") as existing_file:
            file.write(existing_file.read())

    # Assign the path of the newly created file to the FileField
    # object.conv_file.name = object.excel_file.name.replace('.xlsx', '_converted.xlsx').replace('excel_files', 'conv_files') 
    object.conv_file.name = object.excel_file.name.replace('.xlsx', '_converted.xlsx')
    object.conv_file.name = object.conv_file.name.replace('excel_files', 'conv_files')
    
    # Assign a date
    object.conv_at = timezone.now()
    
    # Assign a success status
    object.success = True

    # Save the excel_file instance to persist the changes
    object.save()
    
    # delete the temp file
    os.remove(temp_file_path)
    
    # return status
    return object.success