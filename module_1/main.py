from datetime import datetime, timedelta, date
import re
import pickle

class Field:
    def __init__(self, value):
        self.value = value

class Name(Field):
    def __init__(self, value):
        super().__init__(value)

class Phone(Field):
    def __init__(self, value):
        if not re.fullmatch(r'\d{10}', value):
            raise ValueError("Invalid phone number format. Use 10 digits.")
        super().__init__(value)

class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        super().__init__(value)

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def change_phone(self, old_phone, new_phone):
        if not re.fullmatch(r'\d{10}', new_phone):
            raise ValueError("Invalid phone number format. Use 10 digits.")
        
        for phone in self.phones:
            if phone.value == old_phone:
                phone.value = new_phone
                return
        raise ValueError("Old phone number not found.")

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def show_birthday(self):
        return self.birthday.value.strftime("%d.%m.%Y") if self.birthday else None

    def show_phones(self):
        return [phone.value for phone in self.phones]

class AddressBook:
    def __init__(self):
        self.records = {}

    def add_record(self, record):
        self.records[record.name.value] = record

    def find(self, name):
        return self.records.get(name, None)

    def get_upcoming_birthdays(self):
        today = date.today()
        upcoming_birthdays = []
        for record in self.records.values():
            if record.birthday:
                birthday_this_year = record.birthday.value.replace(year=today.year).date()
                if birthday_this_year < today:
                    birthday_this_year = birthday_this_year.replace(year=today.year + 1)
                if 0 <= (birthday_this_year - today).days <= 7:
                    congratulation_date = adjust_for_weekend(birthday_this_year)
                    upcoming_birthdays.append({"name": record.name.value, "congratulation_date": congratulation_date})
        return upcoming_birthdays
    
    def serialize(self, filename):
        with open(filename, 'wb') as file:
            pickle.dump(self.records, file)
    
    @classmethod
    def deserialize(cls, filename):
        address_book = cls()
        with open(filename, 'rb') as file:
            address_book.records = pickle.load(file)
        return address_book

def adjust_for_weekend(birthday):
    if birthday.weekday() >= 5:  # If it's Saturday (5) or Sunday (6)
        return find_next_weekday(birthday, 0)  # Move to next Monday
    return birthday

def find_next_weekday(start_date, weekday):
    days_ahead = weekday - start_date.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return start_date + timedelta(days=days_ahead)

def input_error(handler):
    def wrapper(*args, **kwargs):
        try:
            return handler(*args, **kwargs)
        except (IndexError, KeyError, ValueError) as e:
            return str(e)
    return wrapper

@input_error
def add_contact(args, book: AddressBook):
    if len(args) < 2:
        raise IndexError("Not enough arguments for add command")
    name, phone = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message

@input_error
def change_phone(args, book: AddressBook):
    if len(args) < 3:
        raise IndexError("Not enough arguments for change command")
    name, old_phone, new_phone = args
    record = book.find(name)
    if record:
        record.change_phone(old_phone, new_phone)
        return f"Phone number for {name} changed from {old_phone} to {new_phone}."
    else:
        return "Contact not found."

@input_error
def show_phone(args, book: AddressBook):
    if len(args) < 1:
        raise IndexError("Not enough arguments for phone command")
    name = args[0]
    record = book.find(name)
    if record:
        phones = record.show_phones()
        return f"Phones for {name}: " + ", ".join(phones) if phones else "No phone numbers."
    else:
        return "Contact not found."

@input_error
def show_all_contacts(args, book: AddressBook):
    if not book.records:
        return "Address book is empty."
    contacts = []
    for record in book.records.values():
        contact_info = f"{record.name.value}: {', '.join(record.show_phones())}"
        if record.birthday:
            contact_info += f", Birthday: {record.show_birthday()}"
        contacts.append(contact_info)
    return "\n".join(contacts)

@input_error
def add_birthday(args, book: AddressBook):
    if len(args) < 2:
        raise IndexError("Not enough arguments for add-birthday command")
    name, birthday = args
    record = book.find(name)
    if record:
        record.add_birthday(birthday)
        return f"Birthday for {name} added/updated."
    else:
        return "Contact not found."

@input_error
def show_birthday(args, book):
    if len(args) < 1:
        return "Please provide a name."
    name = args[0]
    record = book.find(name)
    if record:
        if isinstance(record, str):
            return record  # якщо метод find повернув рядок, повертаємо його без змін
        if record.birthday:
            return f"Birthday for {name} is {record.birthday.value.strftime('%d.%m.%Y')}"
        else:
            return f"Birthday for {name} is not set."
    else:
        return "Contact not found."

@input_error
def birthdays(args, book: AddressBook):
    upcoming_birthdays = book.get_upcoming_birthdays()
    if not upcoming_birthdays:
        return "No upcoming birthdays in the next week."
    return "\n".join([f"{record['name']}: {record['congratulation_date'].strftime('%d.%m.%Y')}" for record in upcoming_birthdays])

def parse_input(user_input):
    parts = user_input.split(maxsplit=1)
    command = parts[0]
    args = parts[1].split() if len(parts) > 1 else []
    return command, args

def main():
    try:
        book = AddressBook.deserialize("address_book.pkl")
        print("Address book loaded successfully.")
    except FileNotFoundError:
        book = AddressBook()
        print("No existing address book found. Creating a new one.")

    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            book.serialize("address_book.pkl")
            print("Address book saved successfully.")
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_phone(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            print(show_all_contacts(args, book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            if not args:
                print("Please provide a name.")
            else:
                print(show_birthday(args, book))

        elif command == "birthdays":
            if len(args) != 1:
                print("Please provide a name.")
            else:
                print(birthdays(args, book))

        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()
