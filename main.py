from src.Company import Company
from src.DataQuery import YahooSession
import yfinance as yf

def main_menu():
    print("STOCK MARKET DATABASE")
    print("###################################")
    print("1: Current Positions")
    print("2: Company Data")
    print("Q: Quit")
    print("###################################")
    choice = input("Please choose an option:")
    if choice == "1":
        raise NotImplementedError
    elif choice == "2":
        raise NotImplementedError
    elif choice.lower() == "q":
        exit(0)
    else:
        print("Invalid Input")
    main_menu()

def main():
    main_menu()

if __name__ == '__main__':
    main()
