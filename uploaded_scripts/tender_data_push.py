import requests
import json
import csv

base_url = "https://api.bidsinfoglobal.com"
status_string = "************************************************** {} **************************************************"

def login(email, password):
    url = "{}/auth/user-login".format(base_url)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer your_token'
    }
    body_data = {
        "email": email,
        "password": password
    }
    json_data = json.dumps(body_data)
    re = requests.post(url, headers=headers, data=json_data)
    if re.status_code == 201:
        print(status_string.format("login successful!"))
        token = json.loads(re.text)["result"]["tokens"]
        return {'success': True, "token": token}
    else:
        print(status_string.format("login failed!"))
        return {'success': False, "token": ""}

def filter_data(db_column_name,file_column_name,header_list,row_data):
    data=row_data[header_list.index(file_column_name)]
    if data =="" or data=="null":
        return "-"
    return data

def preparer_data():
    header = []
    output_list = []
    with open('test_data - Sheet1.csv', 'r', encoding='utf-8-sig') as file:
        print(status_string.format("file load successful!"))
        type(file)
        csv_reader = csv.reader(file)
        header = next(csv_reader)
        # print(header)
        for row in csv_reader:
            data = {
                    "org_name": filter_data(db_column_name="org_name", file_column_name="org_name", header_list=header, row_data=row),
                    "title": filter_data(db_column_name="title", file_column_name="title", header_list=header, row_data=row),
                    "org_address": filter_data(db_column_name="org_address", file_column_name="org_address", header_list=header, row_data=row),
                    "telephone_no": filter_data(db_column_name="telephone_no", file_column_name="telephone_no", header_list=header, row_data=row),
                    "fax_number": filter_data(db_column_name="fax_number", file_column_name="fax_number", header_list=header, row_data=row),
                    "email": filter_data(db_column_name="email", file_column_name="email", header_list=header, row_data=row),
                    "contact_person": filter_data(db_column_name="contact_person", file_column_name="contact_person", header_list=header, row_data=row),
                    "document_no": filter_data(db_column_name="document_no", file_column_name="document_no", header_list=header, row_data=row),
                    "bidding_type": filter_data(db_column_name="bidding_type", file_column_name="bidding_type", header_list=header, row_data=row),
                    "project_location": filter_data(db_column_name="project_location", file_column_name="project_location", header_list=header, row_data=row),
                    "contractor_details": filter_data(db_column_name="contractor_details", file_column_name="contractor_details", header_list=header, row_data=row),
                    "tender_notice_no": filter_data(db_column_name="tender_notice_no", file_column_name="tender_notice_no", header_list=header, row_data=row),
                    "description": filter_data(db_column_name="description", file_column_name="description", header_list=header, row_data=row),
                    "cpv_codes": filter_data(db_column_name="cpv_codes", file_column_name="cpv_codes", header_list=header, row_data=row),
                    "sectors": filter_data(db_column_name="sectors", file_column_name="sectors", header_list=header, row_data=row),
                    "regions": filter_data(db_column_name="regions", file_column_name="regions", header_list=header, row_data=row),
                    "funding_agency": filter_data(db_column_name="funding_agency", file_column_name="funding_agency", header_list=header, row_data=row),
                    "awards_publish_date": filter_data(db_column_name="awards_publish_date", file_column_name="awards_publish_date", header_list=header, row_data=row),
                    "is_active": filter_data(db_column_name="is_active", file_column_name="is_active", header_list=header, row_data=row),
                }


            # Each row is a list representing the fields in that row
            # You can access individual fields by their index
            output_list.append(data)

        print(status_string.format("preparer data successful!"))

        return output_list

def push_tenders(token):
    print(token)
    data = preparer_data()
    url = "{}/contract-award/multiple".format(base_url)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(token)
    }
    body_data = {
        "tenders": data,
    }
    json_data = json.dumps(body_data)
    re = requests.post(url, headers=headers, data=json_data)
    if re.status_code == 201:
        print(status_string.format("data upload successful!"))
    else:
        print(status_string.format("data upload failed!"))
        print(re.text)


re=login("admin@gmail.com", "Admin@123")
if re["success"]:
    push_tenders(re["token"])