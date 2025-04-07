import re
from datetime import datetime, timedelta

    
def find_ignore_case(text, substring):
    return text.lower().find(substring.lower())

def add_capital_spaces(text):
    # Add a space before capital letters (except the first one)
    text = re.sub(r"(?<!^)(?=[A-Z])", " ", text)
    # Add a space between letters and numbers
    text = re.sub(r"(?<=[a-zA-Z])(?=\d)", " ", text)
    return text

def extract_float(value):
    # Use regex to find the number with optional thousands separators and a decimal part
    match = re.search(r"[-+]?\d{1,3}(?: \d{3})*(?:,\d+)?", value)
    if match:
        # Clean the matched number: remove spaces and replace ',' with '.'
        cleaned_value = match.group().replace(" ", "").replace(",", ".")
        return float(cleaned_value)
    raise ValueError("No valid float found in the string")

def extract_date(value):
    # Use regex to find a date in the format DD.MM.YYYY
    match = re.search(r"\b\d{1,2}\.\d{1,2}\.\d{2,4}\b", value)
    if match:
        # Parse the matched date string into a datetime object
        return datetime.strptime(match.group(), "%d.%m.%Y")
    raise ValueError("No valid date found in the string")

def extract_unit(value, unit):
    # Use regex to find the number followed by unit
    arg =r"(\d{1,3}(?:\s*\d{3})*(?:,\d+)?)\s*%s" % unit
    match = re.search(arg, value, re.IGNORECASE)
    if match:
        # Replace ',' with '.' to convert to a float
        cleaned_value = re.sub(r"[^\d+-.]", "", match.group().replace(",", "."))
        return float(cleaned_value)
    raise ValueError("No valid kWh value found in the string")

def extract_invoice_date_range(value):
    # Use regex to find the date range in the format DD.MM.YY-DD.MM.YY
    match = re.search(r"\b\d{1,2}\.\d{1,2}\.\d{2}\s*-\s*\d{1,2}\.\d{1,2}\.\d{2}\b", value)
    if match:
        # Split the range into start and end dates
        start_date_str, end_date_str = match.group().replace(" ", "").split('-')
        # Parse the dates into datetime objects
        start_date = datetime.strptime(start_date_str, "%d.%m.%y")
        end_date = datetime.strptime(end_date_str, "%d.%m.%y")
        return start_date, end_date
    raise ValueError("No valid invoice date range found in the string")

def first_day_of_next_month(date):
    # If the current month is December, move to January of the next year
    if date.month == 12:
        return date.replace(year=date.year + 1, month=1, day=1)
    # Otherwise, move to the first day of the next month
    return date.replace(month=date.month + 1, day=1)

def get_months_in_range(start_date, end_date):
    # Initialize the list of months
    months = []
    current_date = start_date

    # Loop through the months in the range
    while current_date < end_date:
        months.append(current_date.strftime("%B"))  # Get the full month name
        # Move to the next month
        current_date = first_day_of_next_month(current_date)
    return ", ".join(months)

class InvoiceTypes(object):
    CURRENCY = "kr"
    USAGE = "kwh"
    TOTAL_USAGE_TEXT = "spotpris"
    ADDRESS = "anleggsadresse"
    def __init__(self):
        self.name = None
        self.street = None
        self.user_usage = None
        self.user_cost = None
        self.user_percent = None
        self.total_usage = None
        self.total_cost = None
        self.invoice_deadline = None
        self.invoice_month_str = None
        self.invoice_year = None
        self.invoice_range = [] # List of datetime objects

    def parse_total_cost_and_invoice_date(self, page):
        idx = find_ignore_case(page, self.CURRENCY+" ")
        if idx == -1:
            raise ValueError("Missing extract for total cost in the first page")
        extract = page[idx-20:idx+20]
        # find the last carrage return before the currency symbol idx
        p1 = extract[:20].rfind("\n")
        # find the first carrage return after the currency symbol idx
        p2 = extract[20:].find("\n")
        # Get the number before the symbol
        if p1 == -1:
            self.total_cost = extract_float(extract[:20])
        else:
            self.total_cost = extract_float(extract[p1+1:20])
        # Get the invoice date
        if p2 == -1:
            self.invoice_deadline = extract_date(extract[20:])
        else:
            self.invoice_deadline = extract_date(extract[20:20+p2])

    def parse_total_usage(self, page):
        idx = find_ignore_case(page , self.TOTAL_USAGE_TEXT)
        if idx == -1:
            raise ValueError("Missing extract for total usage in the first page")
        extract = page[idx-5:idx+92]
        # find the last carrage return before the currency symbol idx
        p1 = extract[:5].rfind("\n")
        # find the first carrage return after the currency symbol idx
        p2 = extract[5:].find("\n")
        if p1 != -1 and p2 != -1:
            extract = extract[p1:5+p2]
        elif p1 == -1:
            extract = extract[:5+p2]
        elif p2 == -1:
            extract = extract[p1:]

        # Get the number before the symbol
        self.total_usage = extract_unit(extract, self.USAGE)

        # Get the invoice date range
        self.invoice_range = extract_invoice_date_range(extract)
        # Get the invoice month string
        self.invoice_month_str = get_months_in_range(self.invoice_range[0], self.invoice_range[1])


    def parse_user_usage(self, page):
        idx = find_ignore_case(page, self.ADDRESS)
        if idx == -1:
            raise ValueError("Missing extract for user usage in the second page")
        p1 = idx + 1 + page[idx:].find("\n")
        p2 = p1 + page[p1:].find("\n")
        self.street = add_capital_spaces(page[p1:p2])

    def parse(self, regions):

        #Extract total cost
        try:
            for region in regions:
                if "INVOICE_INFO" == region["name"]:
                    self.parse_user_usage(region["extract"])
                    
                elif "INVOICE_CONSUMPTION" == region["name"]: 
                    self.parse_total_usage(region["extract"])

                elif "INVOICE_PAYMENT" == region["name"]:
                    self.parse_total_cost_and_invoice_date(region["extract"])            


        except ValueError as e:
            print(e)
        except Exception as e:
            print(e)

    def calculate_user_data(self, usage):
        self.user_usage = usage
        self.user_percent = (usage/self.total_usage) * 100.0
        self.user_cost = (usage/self.total_usage)*self.total_cost


