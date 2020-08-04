# Paolo Villaflores
# 2020-08-04
#
# script for automating CND website to get trip details of all bookings
# Output will be saved to a csv file in the current dir
#

UserName = 'myCNDuserID'
Password = 'myCNDPassword'

# list of your cars in vehicle number: rego number format
cars = {
    '123456': '1AT5QO',
    '789012': 'ZTP471'
}

from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
import selenium
import time
from pprint import pprint
from datetime import datetime
from datetime import timedelta

DEBUG = False
output_csv = 'cnd_detail_bookings.csv'

now = datetime.now()

chromedriver = "chromedriver.exe"
driver = webdriver.Chrome(executable_path=chromedriver)

chrome_options = Options()
chrome_options.add_argument("user-data-dir=selenium")
driver = webdriver.Chrome(chrome_options=chrome_options)


def get_bookings(car_id, rego, days_back=1):
    the_url = "https://www.carnextdoor.com.au/manage/cars/" + car_id + "/bookings"
    driver.get(the_url)

    def element_present(a):
        l = a.find_elements_by_xpath("//*[contains(text(), 'Privacy policy')]")
        return len(l) > 0

    WebDriverWait(driver, 60).until(element_present)

    logged_in = False
    try:
        username = driver.find_element_by_id("member_session_email")
    except NoSuchElementException:
        logged_in = True

    if not logged_in:
        password = driver.find_element_by_id("member_session_password")

        username.send_keys(UserName)
        password.send_keys(Password)

        form = driver.find_element_by_id('new_member_session')
        form.submit()

    j = 1
    try:
        e = driver.find_elements_by_xpath("//a[contains(@class, 'cnd-booking-item')]")
        results = []
        for i in e:
            href1 = i.get_attribute('href')
            try:
                e1 = i.find_element_by_xpath(".//div[contains(@class, 'cnd-booking-item__title__name')]")
                # drop last 2 character's at the end which is the 's
                apostrophe = chr(8217)
                fname = e1.text.replace(" booking", '')
                if fname[-2:] == apostrophe + 's':
                    fname = fname[:-2]
                else:
                    fname = fname.strip(apostrophe)
                e2 = i.find_elements_by_xpath(".//div[contains(@class, 'cnd-booking-item__duration__text')]")
                durs = [j.text for j in e2]
                e3 = i.find_element_by_xpath(".//span[contains(@class, 'cnd-status__text')]")
                stat = e3.text
            except NoSuchElementException:
                pass  # found no element
            dt = datetime.strptime(durs[2], "%d/%m/%y %H:%M")
            dt_s = datetime.strptime(durs[0], "%d/%m/%y %H:%M")
            if (now - dt).days > days_back:
                break

            if stat.upper() != 'CANCELLED':
                ######  results set
                results.append([rego, fname, href1, stat, dt, dt_s])

    except NoSuchElementException:
        print("  reached no element")

    return results


all_bookings = []
for i in cars:
    days_back = 700
    if DEBUG:
        days_back = 20
    a = get_bookings(i, cars[i], 700)
    if len(a) > 0:
        all_bookings = all_bookings + a
    pprint(a)

b = sorted(all_bookings, key=lambda x: x[5])

def get_borrower_thumb(list1):
    for i in list1:
        if 'The borrower gave you a ' in i:
            if 'thumbs up' in i:
                return 'up'
            if 'thumbs down' in i:
                return 'down'
            return i
    return ''

def get_private_comment(list1):
    for i in list1:
        if 'Private comment' in i:
            flag = False
            for j in i.split('\n'):
                if 'Private comment' in j:
                    flag = True
                elif flag:
                    return j
    return ''

def get_public_review(list1):
    for i in list1:
        if 'Public review' in i:
            flag = False
            for j in i.split('\n'):
                if 'Public review' in j:
                    flag = True
                elif flag:
                    return j
    return ''

def get_my_thumbsup(list1):
    for i in list1:
        if 'You gave the borrower ' in i:
            flag = False
            for j in i.split('\n'):
                if 'You gave the borrower ' in j:
                    return j.replace('You gave the borrower ', '')
    return ''


def get_photos(list1):
    total_p = 0
    for i in list1:
        if ' photos uploaded ' in i:
            val = int(i.split(' ')[0])
            total_p = total_p + val
    return total_p


def get_fuel(list1):
    total_f = 0.0
    for i in list1:
        if ' fuel refund ' in i and 'Completed' in i:
            val = float((i.split(' ')[0]).strip('$'))
            total_f = total_f + val
    return total_f


def get_str(list1, val, full_str=False):
    for i in list1:
        if val in i:
            if full_str:
                return i.replace('\n', ',')
            else:
                return i.split('\n')[-1]
    return ""


all_bookings2 = []
for bookin in all_bookings:
    driver.get(bookin[2])


    def element_present(a):
        l = a.find_elements_by_xpath("//*[contains(text(), 'Privacy policy')]")
        return len(l) > 0


    WebDriverWait(driver, 60).until(element_present)

    e1 = driver.find_elements_by_xpath(".//div[contains(@class, 'cnd-justify-between')]")
    e2 = [i.text for i in e1]
    bill_info1 = [
        get_str(e2, 'Billing status'),
        get_str(e2, 'Pickup'),
        get_str(e2, 'Return'),
        get_str(e2, 'Time charges'),
        get_str(e2, 'Your share'),
        get_str(e2, ' km x ', True)
    ]

    e3 = driver.find_elements_by_xpath(".//div[contains(@class, 'cnd-items-center')]")
    e4 = [i.text for i in e3]
    bill_info1 = bill_info1 + [e4[-2], e4[-1]]
    e5 = driver.find_elements_by_xpath(".//div[contains(@class, 'text')]")
    e6 = [i.text for i in e5]
    e7 = driver.find_elements_by_xpath(".//div[contains(@class, 'cnd-panel')]")
    e8 = [i.text for i in e7]
    bill_info1 = bill_info1 + [get_borrower_thumb(e8),
                               get_private_comment(e8),
                               get_public_review(e8),
                               get_my_thumbsup(e8),
                               get_photos(e8),
                               get_fuel(e8)]
    all_bookings2.append(bookin + bill_info1)

pprint(all_bookings2)
driver.quit()

import csv

with open(output_csv, 'w', newline='', encoding='utf-8') as file:
    fieldnames = ['rego', 'borrower_name', 'booking_url', 'status', 'end_dt', 'start_dt',
                  'billing_status', 'pickup', 'return', 'time_charges', 'your_share', 'km', 'email', 'phone',
                  'borrower_thumbs', 'private_comment', 'public_review', 'my_thumbsup', 'photos', 'fuel']
    writer = csv.DictWriter(file, fieldnames=fieldnames)

    writer.writeheader()
    for j in all_bookings2:
        d1 = {}
        for c, k in enumerate(fieldnames):
            if k == 'phone':
                d1[k] = "'" + j[c]
            else:
                d1[k] = j[c]

        writer.writerow(d1)

