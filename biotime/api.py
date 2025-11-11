import frappe
import json
import requests
from frappe import _
from frappe import publish_progress
from frappe.utils import get_first_day, get_last_day, today, add_to_date
from frappe.utils import add_to_date

from datetime import datetime

# Biometric Integration


def get_tokan():
    doc = frappe.get_single("BioTime Setting")
    url = doc.url + "/jwt-api-token-auth/"
    headers = {
        "Content-Type": "application/json",
    }
    doc = frappe.get_single("BioTime Setting")
    data = {
        "username": doc.user_name ,
        "password": doc.get_password('password')
    }
    try:
        response = requests.post(url, data=json.dumps(data), headers=headers)
        return response.text[10: len(response.text) - 2]
    # print(response.text) 
    # tokan = doc.get_password('tokan') if doc.tokan else ""
    # return tokan
    except Exception as e:
        frappe.log_error(
            message=e, title="Failed while Connect to biotime serever")
        frappe.throw(
            title='Error',
            msg='Failed while Connect to biotime serever',
        )
    


def get_url():
    doc = frappe.get_single("BioTime Setting")
    url = doc.url
    return url

@frappe.whitelist()
def fetch_transactions():
    tokan = get_tokan()
    main_url = get_url()
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'JWT ' + tokan
    }

    transactions_list = []

    start_date = get_first_day(today()).strftime("%Y-%m-%d %H:%M:%S")
    end_date = get_last_day(today()).strftime("%Y-%m-%d %H:%M:%S")
    end_date = add_to_date(end_date, days=1)
    is_next_page = True
    url = f"{main_url}/iclock/api/transactions/?start_time={start_date}&end_time={end_date}"

    progress_count = 0
    count = 0
    while is_next_page:
        try:
            response = requests.request("GET", url, headers=headers)
            if response.ok:
                res = json.loads(response.text)
                transactions = res.get("data")
                # print(res)
                count = res.get("count")
                if not res.get("next"):
                    is_next_page = False
                else:
                    for transaction in transactions:
                        transactions_list.append(transaction)
                url = res.get("next")
            else:
                is_next_page = False
                frappe.log_error(message=res.get("detail", ""),
                                 title=f"Failed to Get Transactions")

        except Exception as e:
            is_next_page = False
            frappe.log_error(
                message=e, title="Failed while fetching transactions")
            frappe.publish_realtime("msgprint", "Can't Fetch Transactions please check your tokan or url <hr> For more details review error log")
    
    is_next_page = True
    while is_next_page:

        try:
            response = requests.request("GET", url, headers=headers)
            if response.ok:
                res = json.loads(response.text)
                transactions = res.get("data")
                # print(res)
                count = res.get("count")
                if res.get("next"):
                    is_next_page = False
                else:
                    for transaction in transactions:
                        transactions_list.append(transaction)
                url = res.get("next")
            else:
                is_next_page = False
                frappe.log_error(message=res.get("detail", ""),
                                 title=f"Failed to Get Transactions")

        except Exception as e:
            is_next_page = False
            frappe.log_error(
                message=e, title="Failed while fetching transactions")
            frappe.publish_realtime("msgprint", "Can't Fetch Transactions please check your tokan or url <hr> For more details review error log")

        progress_count += 10
        publish_progress(progress_count*100/int(count + 1),
                         title="Fetching Transactions...")

    if len(transactions_list):

        handel_transactions(transactions_list)

def handel_transactions(transactions):
    exists_trans = 0
    progress_count = 0
    created = 0
    errors = 0
    for transaction in transactions:
        
        # Check if Transaction is Exists
        is_exists = frappe.db.exists(
            {"doctype": "Employee Checkin", "transaction_id": transaction.get("id")})
        if is_exists:
            exists_trans += 1
        else:
            # Check if employee exists
            is_emp_exists = frappe.db.exists(
                {"doctype": "Employee", "attendance_device_id": transaction.get("emp_code")})
            if is_emp_exists:
                # Create Transaction
                new_trans = create_employee_checkin(transaction)
                if new_trans:
                    created += 1
                else:
                    errors += 1
            else:
                trans_no = transaction.get("id")
                emp_code = transaction.get("emp_code")         
                errors += 1
                frappe.msgprint(
                    msg=_(f"Can't Create Transaction No. { str(trans_no) } because Employee with code { emp_code } Not in System, Please make sure to Fetching Employees"),
                    title=_("Transaction Creation Faild"),
                )
        progress_count += 1

        publish_progress(int(progress_count * 100/len(transactions)),
                         title="Creating Employee Checkin...")

    msg = "Try to Create {} Employee Checkin: <br> {} already Exists In System  <br> {} Successfully Created ,<br> {} Failed <hr> for more details about Failed Employee Checkin Docs review errors log".format(
        len(transactions), exists_trans, created, errors)
    if created >0:
        shift_list =  frappe.get_list("Shift Type" , filters = {"enable_auto_attendance" : 1})
        for shift in shift_list:
            shift_doc = frappe.get_doc("Shift Type" , shift)
            shift_doc.last_sync_of_checkin = datetime.now()
            shift_doc.save()
            frappe.db.commit()
    frappe.publish_realtime('msgprint', msg)
    
def create_employee_checkin(transaction):
    res = False
    if transaction:
        try:
            log_type = ""
            if transaction.get("punch_state") == "1":
                log_type = "OUT"
            elif transaction.get("punch_state") == "0":
                log_type = "IN"
            else:
                log_type = ""

            employee = frappe.db.get_list(
                "Employee", filters={"attendance_device_id": transaction.get("emp_code")})
            doc = frappe.new_doc('Employee Checkin')
            doc.employee = employee[0].name
            doc.time = transaction.get("punch_time")
            doc.log_type = log_type
            doc.transaction_id = transaction.get("id")
            doc.save()
            res = True
            frappe.db.commit()
        except Exception as e:
            trans_no = transaction.get("id")
            frappe.log_error(
                message=e, title=f"Failed to Create Employee With id <b> {trans_no} <b>")
            res = False
    return res

# هذا الكود كتب على وجه الاستعجال لحل مشكلة بشكل شريع ,,,,  سيحتاج الكود الى تعديل و تحسين ف المستقبل ليكون اقل في عدد الاسطر و اكثر فاعليى
# كتب بتاريخ 11 / 02 /2024
# من قبل م هديل
# لحل مشكلة في عبور ,,, الشمكلة حدثت قبل تسيلم تعديل الكود الاخير الذي سيكون بدوره مانع لوقوع المشكلة 

@frappe.whitelist()
def fetch():
    tokan = get_tokan()
    main_url = get_url()

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'JWT ' + tokan
    }

    transactions_list = []
    date = frappe.get_single("BioTime Setting").date
    print("DDDDDDDDDDDDDDDDDDDD" , date)
    start_date = get_first_day(date).strftime("%Y-%m-%d %H:%M:%S")
    end_date = get_last_day(date).strftime("%Y-%m-%d %H:%M:%S")
    end_date = add_to_date(end_date, days=1)
    print("DDDDDDDDDDDDDDDDDDDD" , start_date, end_date)

    is_next_page = True
    url = f"{main_url}/iclock/api/transactions/?start_time={start_date}&end_time={end_date}"

    progress_count = 0
    count = 0
    is_next_page = True
    while is_next_page:

        try:
            response = requests.request("GET", url, headers=headers)
            if response.ok:
                res = json.loads(response.text)
                transactions = res.get("data")
                # print(res)
                count = res.get("count")
                if not res.get("next"):
                    is_next_page = False
                else:
                    for transaction in transactions:
                        transactions_list.append(transaction)
                url = res.get("next")
            else:
                is_next_page = False
                frappe.log_error(message=res.get("detail", ""),
                                 title=f"Failed to Get Transactions")

        except Exception as e:
            is_next_page = False
            frappe.log_error(
                message=e, title="Failed while fetching transactions")
            frappe.publish_realtime("msgprint", "Can't Fetch Transactions please check your tokan or url <hr> For more details review error log")
    is_next_page = True
    while is_next_page:

        try:
            response = requests.request("GET", url, headers=headers)
            if response.ok:
                res = json.loads(response.text)
                transactions = res.get("data")
                # print(res)
                count = res.get("count")
                if res.get("next"):
                    is_next_page = False
                else:
                    for transaction in transactions:
                        transactions_list.append(transaction)
                url = res.get("next")
            else:
                is_next_page = False
                frappe.log_error(message=res.get("detail", ""),
                                 title=f"Failed to Get Transactions")

        except Exception as e:
            is_next_page = False
            frappe.log_error(
                message=e, title="Failed while fetching transactions")
            frappe.publish_realtime("msgprint", "Can't Fetch Transactions please check your tokan or url <hr> For more details review error log")

        progress_count += 10
        publish_progress(progress_count*100/int(count + 1),
                         title="Fetching Transactions...")
        progress_count += 10
        publish_progress(progress_count*100/int(count + 1),
                         title="Fetching Transactions...")
    print(len(transactions_list))
    if len(transactions_list):
        handel_transactions(transactions_list)
