import os
import csv
import json
import time
import random
import hashlib
import subprocess
import sys

ACCOUNTS_FOLDER = "bank_accounts"
TRANSACTIONS_FOLDER = "bank_transactions"
ACCOUNT_NUMBERS_FOLDER = "account_numbers"

os.makedirs(ACCOUNTS_FOLDER, exist_ok=True)
os.makedirs(TRANSACTIONS_FOLDER, exist_ok=True)
os.makedirs(ACCOUNT_NUMBERS_FOLDER, exist_ok=True)


def open_file(filepath):
    if os.name == "nt":
        os.startfile(filepath)
    elif sys.platform == "darwin":
        subprocess.call(["open", filepath])
    else:
        subprocess.call(["xdg-open", filepath])


class BankLogic:

    def __init__(self):
        self.username = None
        self.balance = 0
        self.pin = None
        self.account_number = None
        self.blocked = False
        self.blocked_until = None
        self.account_file = None
        self.transaction_file = None

    def hash_pin(self, pin):
        return hashlib.sha256(pin.encode()).hexdigest()

    def save_data(self):
        with open(self.account_file, "w") as f:
            json.dump({
                "username": self.username,
                "balance": round(self.balance, 2),
                "pin": self.pin,
                "account_number": self.account_number,
                "blocked": self.blocked,
                "blocked_until": self.blocked_until,
                "transaction_file": self.transaction_file
            }, f, indent=4)

    def log_transaction(self, transaction, details):
        with open(self.transaction_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                transaction,
                f"${self.balance:.2f}",
                time.strftime("%d-%m-%Y"),
                time.strftime("%H:%M"),
                details
            ])

    def check_block_status(self):
        if self.blocked:
            remaining = self.blocked_until - time.time()
            if remaining <= 0:
                self.blocked = False
                self.blocked_until = None
                self.save_data()
                return False
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            print(f"Account blocked. Try again in {minutes}m {seconds}s")
            return True
        return False

    def validate_pin(self):
        attempts = 0
        while attempts < 3:
            print()
            pin = input("Enter your 4 digit PIN: ")
            if not pin.isdigit() or len(pin) != 4:
                print("Digits only, 4 characters")
                continue
            if self.hash_pin(pin) == self.pin:
                return True
            attempts += 1
            remaining = 3 - attempts
            if remaining == 0:
                print("Wrong PIN, no more tries left")
                break
            print(
                f"Wrong PIN, {remaining} tries left"
                if remaining > 1
                else f"Wrong PIN, {remaining} try left"
            )

        self.blocked = True
        self.blocked_until = time.time() + (30 * 60)
        self.save_data()
        print("\nAccount temporarily blocked for 30 minutes")
        return False

    def create_account(self):
        print("\n_________CREATE ACCOUNT_________")

        while True:
            username = input("\nEnter username [letters and numbers only, max 12 characters]: ")
            self.account_file = os.path.join(ACCOUNTS_FOLDER, f"{username}.json")

            if not username.isalnum():
                print("Letters and numbers only\n")
                continue
            if len(username) > 12:
                print("Maximum 12 characters\n")
                continue
            if os.path.exists(self.account_file):
                print("Username already exists\n")
                continue

            self.username = username
            break

        print("\nPlease set your PIN")
        while True:
            pin = input("Enter a 4 digit PIN: ")
            if not pin.isdigit() or len(pin) != 4:
                print("Invalid PIN\n")
                continue
            self.pin = self.hash_pin(pin)
            print("PIN set successfully\n")
            break

        print("You need to deposit a minimum of $50.00 to activate your account")
        while True:
            try:
                amount = float(input("Initial deposit: $"))
                if amount < 50:
                    print("Minimum deposit is $50\n")
                    continue
                print("\nDepositing amount...")
                time.sleep(1)
                self.balance = amount
                break
            except ValueError:
                print("Invalid input\n")

        while True:
            account_number = "".join(str(random.randint(0, 9)) for _ in range(12))
            account_path = os.path.join(ACCOUNT_NUMBERS_FOLDER, f"{account_number}.json")
            if not os.path.exists(account_path):
                self.account_number = account_number
                with open(account_path, "w") as f:
                    json.dump({"account_file": self.account_file}, f, indent=4)
                break

        self.transaction_file = os.path.join(TRANSACTIONS_FOLDER, f"{self.username}_transactions.csv")
        with open(self.transaction_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["________________TRANSACTION HISTORY________________"])
            writer.writerow(["Transaction", "Balance", "Date", "Time", "Details"])

        self.save_data()
        self.log_transaction(f"+ ${amount:.2f}", "Initial Deposit")

        print(f"\nWelcome aboard, '{self.username}'!")
        print(f"Your account number is: {self.account_number}\n")

    def login(self):
        print("\n_________LOGIN_________")
        username = input("\nEnter your username: ")
        account_file = os.path.join(ACCOUNTS_FOLDER, f"{username}.json")

        if not os.path.exists(account_file):
            print(f"'{username}' not found in our database\n")
            return False

        with open(account_file, "r") as f:
            data = json.load(f)

        self.username = data["username"]
        self.balance = data["balance"]
        self.pin = data["pin"]
        self.account_number = data["account_number"]
        self.blocked = data["blocked"]
        self.blocked_until = data["blocked_until"]
        self.transaction_file = data["transaction_file"]
        self.account_file = account_file

        if self.check_block_status():
            return False

        if self.validate_pin():
            print(f"\nWelcome back, '{self.username}'!")
            print("Loading....")
            time.sleep(2)
            return True

        return False

    def get_balance(self):
        if self.validate_pin():
            print(f"\nYour balance is ${self.balance:.2f}")
            print("Going back to main menu....")
            time.sleep(3)

    def deposit(self):
        while True:
            try:
                amount = float(input("\nDeposit amount [0 to go back]: $"))
                if amount == 0:
                    print("\nGoing back to main menu....")
                    time.sleep(3)
                    return
                if amount < 0:
                    print("Invalid amount\n")
                    continue
                if self.validate_pin():
                    self.balance += amount
                    self.save_data()
                    self.log_transaction(f"+ ${amount:.2f}", "Deposit")
                    print("Deposited successfully")
                    print(f"New balance: ${self.balance:.2f}")
                    print("\nGoing back to main menu....")
                    time.sleep(3)
                return
            except ValueError:
                print("Invalid input\n")

    def withdraw(self):
        while True:
            try:
                amount = float(input("\nWithdraw amount [0 to go back]: $"))
                if amount == 0:
                    print("\nGoing back to main menu....")
                    time.sleep(3)
                    return
                if amount < 0:
                    print("Invalid amount\n")
                    continue
                if amount > self.balance:
                    print("Insufficient funds\n")
                    continue
                if self.validate_pin():
                    self.balance -= amount
                    self.save_data()
                    self.log_transaction(f"- ${amount:.2f}", "Withdrawal")
                    print("Withdrawn successfully")
                    print(f"New balance: ${self.balance:.2f}")
                    print("\nGoing back to main menu....")
                    time.sleep(3)
                return
            except ValueError:
                print("Invalid input\n")

    def transfer(self):
        print()
        while True:
            receiver_account = input("Recipient account number [0 to go back]: ")
            if receiver_account == "0":
                print("\nGoing back to main menu....")
                time.sleep(3)
                return

            if receiver_account == self.account_number:
                print("Cannot transfer to yourself\n")
                continue

            receiver_path = os.path.join(ACCOUNT_NUMBERS_FOLDER, f"{receiver_account}.json")
            if not os.path.exists(receiver_path):
                print("Account not found\n")
                continue

            with open(receiver_path, "r") as f:
                receiver_data = json.load(f)

            receiver_account_file = receiver_data["account_file"]

            with open(receiver_account_file, "r") as f:
                receiver = json.load(f)

            if receiver["blocked"]:
                if receiver["blocked_until"] and time.time() < receiver["blocked_until"]:
                    print("Recipient's account is currently blocked\n")
                    continue

            while True:
                try:
                    amount = float(input("Transfer amount: $"))
                    if amount <= 0:
                        print("Invalid amount\n")
                        continue
                    if amount > self.balance:
                        print("Insufficient funds\n")
                        continue
                    break
                except ValueError:
                    print("Invalid input\n")

            if self.validate_pin():
                self.balance -= amount
                self.save_data()
                self.log_transaction(f"- ${amount:.2f}", f"Transfer to {receiver_account}")

                receiver["balance"] = round(receiver["balance"] + amount, 2)
                with open(receiver_account_file, "w") as f:
                    json.dump(receiver, f, indent=4)

                with open(receiver["transaction_file"], "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        f"+ ${amount:.2f}",
                        f"${receiver['balance']:.2f}",
                        time.strftime("%d-%m-%Y"),
                        time.strftime("%H:%M"),
                        f"Transfer from {self.account_number}"
                    ])

                print("\nTransferring funds....")
                time.sleep(2)
                print("Transaction complete")
                print(f"New balance: ${self.balance:.2f}")
                print("\nGoing back to main menu....")
                time.sleep(3)
            return

    def my_account(self):
        while True:
            print("\n___MY ACCOUNT___")
            print("1. Reset PIN")
            print("2. Transaction History")
            print("3. Account Number")
            print("0. Go back")

            decision = input("\nSelect: ")

            if decision == "0":
                print("\nGoing back to main menu....")
                time.sleep(3)
                return

            elif decision == "1":
                attempts = 0
                while attempts < 3:
                    print()
                    old_pin = input("Enter your current PIN: ")
                    if not old_pin.isdigit() or len(old_pin) != 4:
                        print("Invalid PIN")
                        attempts += 1
                        continue
                    if self.hash_pin(old_pin) != self.pin:
                        attempts += 1
                        remaining = 3 - attempts
                        if remaining == 0:
                            print("Too many wrong attempts")
                            break
                        print(
                            f"Wrong PIN, {remaining} tries left"
                            if remaining > 1
                            else f"Wrong PIN, {remaining} try left"
                        )
                        continue

                    while True:
                        new_pin = input("\nEnter new 4 digit PIN: ")
                        if not new_pin.isdigit() or len(new_pin) != 4:
                            print("Invalid PIN\n")
                            continue

                        no_ = 0
                        while no_ < 3:
                            confirm = input("Confirm new PIN: ")
                            if confirm != new_pin:
                                print("PINs do not match\n")
                                no_ += 1
                            else:
                                self.pin = self.hash_pin(new_pin)
                                self.save_data()
                                print("\nNew PIN set successfully")
                                print("Going back to main menu....")
                                time.sleep(3)
                                return

                        print("Too many attempts, going back to main menu....")
                        time.sleep(3)
                        return

                if attempts == 3:
                    self.blocked = True
                    self.blocked_until = time.time() + (30 * 60)
                    self.save_data()
                    print("Account temporarily blocked for 30 minutes")
                    return

            elif decision == "2":
                if self.validate_pin():
                    open_file(self.transaction_file)
                time.sleep(3)
                return

            elif decision == "3":
                print(f"\nYour account number is: {self.account_number}")
                input("\nPress Enter to go back...")
                print("Going back to main menu....")
                time.sleep(3)
                return

            else:
                print("Invalid option\n")


class BankUI:

    def __init__(self):
        self.bank = BankLogic()

    def dashboard(self):
        while True:
            if self.bank.check_block_status():
                return

            os.system("cls" if os.name == "nt" else "clear")
            print(f"\n=== {self.bank.username} ===")
            print("1. Balance")
            print("2. Deposit")
            print("3. Withdraw")
            print("4. Transfer")
            print("5. My Account")
            print("6. Logout")

            choice = input("\nSelect: ")

            match choice:
                case "1":
                    self.bank.get_balance()
                case "2":
                    self.bank.deposit()
                case "3":
                    self.bank.withdraw()
                case "4":
                    self.bank.transfer()
                case "5":
                    self.bank.my_account()
                case "6":
                    while True:
                        confirm = input("\nAre you sure you want to logout? (y/n): ").lower()
                        if confirm == "y":
                            print("Logging out....")
                            time.sleep(2)
                            self.bank = BankLogic()
                            return
                        elif confirm == "n":
                            break
                        else:
                            print("Invalid input")
                case _:
                    print("Invalid option\n")

    def start(self):
        while True:
            os.system("cls" if os.name == "nt" else "clear")
            print("\n_________WELCOME TO ZEKE BANK_________")
            print("1. Create Account")
            print("2. Login")
            print("3. Exit")

            choice = input("\nSelect: ")

            match choice:
                case "1":
                    self.bank.create_account()
                case "2":
                    if self.bank.login():
                        self.dashboard()
                case "3":
                    print("\nHave a lovely day ❤️")
                    return
                case _:
                    print("Invalid option\n")


if __name__ == "__main__":
    app = BankUI()
    app.start()

# just a beginner here :(