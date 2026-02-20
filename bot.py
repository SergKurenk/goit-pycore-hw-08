import re, pickle
from datetime import datetime, timedelta
from collections import UserDict

class Field: #Базовий клас для полів запису.
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field): #Клас для зберігання імені контакту. Обов'язкове поле.
	pass

class Phone(Field): #Клас для зберігання номера телефону. Має валідацію формату (10 цифр).
    def __init__(self, value):
        match = re.match(r'^\d{10}$', value)
        if match is None:
            raise ValueError(f"Invalid phone number format: {value}")
        super().__init__(value)

class Birthday(Field):
    def __init__(self, value):
        try:
            datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("Невірний формат дати. Використовуйте DD.MM.YYYY")
        super().__init__(value)

class Record: #Клас для зберігання інформації про контакт, включаючи ім'я та список телефонів.
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone_number: str):
        phone = Phone(phone_number)
        self.phones.append(phone)
    
    def remove_phone(self, phone_number: str):
        phone = self.find_phone(phone_number)
        self.phones.remove(phone)
    
    def edit_phone(self, old_phone_number: str, new_phone_number: str):
        new_phone = Phone(new_phone_number)
        phone = self.find_phone(old_phone_number)
        phone.value = new_phone.value

    def find_phone(self, phone_number: str):
        for phone in self.phones:
            if phone.value == phone_number:
                return phone
        return None
    
    def add_birthday(self, birthday: str):
        self.birthday = Birthday(birthday)

    def show_birthday(self):
        return f"У контакта {self.name.value} день народження {self.birthday.value}" if self.birthday else f"У контакта {self.name.value} день народження не заповнено"

    def __str__(self):
        return f"контакт {self.name.value}, номер телефону: {'; '.join(p.value for p in self.phones)}" if self.phones else ""

class AddressBook(UserDict): #Клас для зберігання та управління записами.
    def __str__(self):
        result = "Address Book:\n"
        for record in self.data:
            result += f"{self.data.get(record)}" + "\n"
        return result.strip()

    def add_record(self, record: Record):
        self.data[record.name.value] = record
    
    def find(self, name: str):
        return self.data.get(name, None)

    def delete(self, name: str):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self, days=7):
        upcoming_birthdays = []
        today = datetime.today()

        for record in self.data.values():
            if record.birthday:
                user_birthday = datetime.strptime(record.birthday.value, "%d.%m.%Y")
                birthday_this_year = user_birthday.replace(year=today.year)

                if birthday_this_year < today:
                    birthday_this_year = user_birthday.replace(year=today.year+1)

                if 0 <= (birthday_this_year - today).days <= days:

                    birthday_this_year = adjust_for_weekend(birthday_this_year)

                    congratulation_date_str = birthday_this_year.strftime("%d.%m.%Y")
                    upcoming_birthdays.append({"name": record.name.value, "birthday": congratulation_date_str})
        return upcoming_birthdays
    
def input_error_decorator(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return "Контакт не знайдено. Будь ласка, перевірте правильність введеного імені."
        except IndexError:
            return "Недостатньо параметрів для виконання команди. Будь ласка, додайте необхідні аргументи."
        except ValueError:
            return "Невірно введений формат даних."
        except AttributeError:
            return "Помилка пошуку даних."
    return inner

def parse_input(user_input: str):
    if user_input.strip() == "":
        return "", []
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args

@input_error_decorator 
def show_contacts(args, book: AddressBook):
    if not book:
        return "Записи відсутні"
    return book

@input_error_decorator 
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    message = "Контакт знайдено."

    if (old_phone or new_phone) is None:
        message = "Невірно вказані номера телефонів"
        return message
    
    record.edit_phone(old_phone, new_phone)
    message = "Номер телефону оновлено."
    return message

@input_error_decorator
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message

@input_error_decorator
def del_contact(args, book: AddressBook):
    name, *_ = args
    book.delete(name)
    return("Контакт видалено.")

@input_error_decorator
def show_phone(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    return record

@input_error_decorator
def add_birthday(args, book: AddressBook):
    name, birth, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError
    if birth:
        record.add_birthday(birth)
        return "День народження до контакту додано"

@input_error_decorator
def show_birthday(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    return record.show_birthday()

@input_error_decorator
def birthdays(args, book):
    birthday_list = book.get_upcoming_birthdays()
    if not birthday_list:
        return "Найближчими днями днів народжень не знайдено."

    s = "У наступних контактів скоро дні народження:\n"
    s += "\n".join(f"{b["name"]} - {b["birthday"]}" for b in birthday_list)

    return s

def find_next_weekday(start_date, weekday=0):
    wd = weekday - start_date.weekday()
    return start_date + timedelta(days=wd+(7 if wd <= 0 else 0))

def adjust_for_weekend(birthday):
    if birthday.weekday() >= 5:
        birthday = find_next_weekday(birthday, 0)
    return birthday

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()  # Повернення нової адресної книги, якщо файл не знайдено

def main():
    book = load_data()
    # book = AddressBook()
    print('Welcome to the assistant bot!')
    while True:
        user_input = input("Ведіть команду: ")
        command, *args = parse_input(user_input)

        match command:
            case "exit":
                save_data(book)  # Викликати перед виходом з програми
                print("Бувай!")
                break
            case "hello":
                print("Чим я можу вам допомогти?")
            case "add":
                print(add_contact(args, book))
            case "change":
                print(change_contact(args, book))
            case "phone":
                print(show_phone(args, book))
            case 'all':
                print(show_contacts(args, book))
            case 'del':
                print(del_contact(args, book))
            case 'add-birthday':
                print(add_birthday(args, book))
            case 'show-birthday':
                print(show_birthday(args, book))
            case 'birthdays':
                print(birthdays(args, book))
            case "help":
                print("Список всіх команд:")
                print("hello - привітання")
                print("add <ім'я> <номер телефону> - додати новий контакт")
                print("change <ім'я> <старий номер телефону> <старий номер телефону> - змінити номер телефону існуючого контакту")
                print("phone <ім'я> - показати номер телефону контакта")
                print("all - показати всі контакти")
                print("add-birthday <ім'я> <дата народження DD.MM.YYYY> - додати дату народження для вказаного контакту")   #!!!!!!
                print("show-birthday <ім'я> - показати дату народження для вказаного контакту")  #!!!!!!!!
                print("birthdays - показати дні народження на найближчі 7 днів з датами, коли їх треба привітати")  #!!!!!!
                print("del <ім'я> - видалити контакт")
                print("exit - закрити чат")
            case "":
                print("Будь ласка, введіть команду. Для списку команд введіть 'help'.")
            case _:
                print("Вибачте, я не знаю таку команду.")

if __name__ == "__main__":
    main()