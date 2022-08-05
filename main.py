# Quick and dirty (muddy even) tools to scrape clay characteristics from a couple of different manufacturer websites.

# Why would you mess with this code if you just want the data?
# I don't know. Maybe the spreadsheet is down. Maybe new clays just dropped.
# Just access the Google Sheet and get back to slinging that mud:
# https://docs.google.com/spreadsheets/d/1-OB2215MkYa8ahn4SySlFGC3SruQsl-Ac-zunVDWkUo/edit?usp=sharing

# Due to very inconsistent formatting on the source pages, this will return pretty sloppy final output.
# Most are one-off issues that don't generalize well, so I'm fixing those in the final spreadsheet

import re
from bs4 import BeautifulSoup
import pandas as pd
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
import pathlib
import time

man_dict = {"1": "laguna", "2": "rocky mountain"}  # mappings for manufacturers

# For Selenium
opts = Options()
opts.add_argument("--headless")

working_dir = pathlib.Path.cwd()

# set up manufacturer info based on menu selection
class Manufacturer:

    def __init__(self, n):
        assert n in man_dict.keys()
        self.manu = man_dict[n]
        self.raw_clay_csv = self.manu + "_raw_clay_list.csv"  # just info from the main list
        self.wedged_clay_csv = self.manu + "_clay_list_descripts.csv"  # with the raw descriptions
        self.final_clay_xlsx = self.manu + "_clay_list_final.xlsx"  # split out into different characteristics

        if self.manu == "laguna":
            self.clay_url = "https://www.lagunaclay.com/shop?page=6"
            self.content_tag = 'pre'
            self.content_class = '_28cEs'
        elif self.manu == "rocky mountain":
            self.clay_url = "https://rockymountainclay.com/product-category/all-clays/"
            self.content_tag = 'div'
            self.content_class = 'et_pb_row et_pb_row_1'
        else:
            raise ValueError("No manufacturer found")


def print_manufacturer_selection_menu():
    print("Select a Manufacturer")
    for key in man_dict.keys():
        print(key + ': ' + man_dict[key])
    print("Q: Quit")

def print_action_selection_menu(brand):
    print("You selected " + brand.manu + ". What do you want to do?")
    print('''
    1: Make a list of clays
    2: Get characteristics for a list of clays
    3: Choose another manufacturer
    Q: Quit''')


# Cut a list of paragraphs into a description, and characteristics
def cut_list(line_list):
    clay_dict = dict()

    line_list = [l for l in line_list if l != "" and l != "Description:"] #remove empty lines and leading Description line

    clay_dict["description"] = line_list[0]

    characteristics_matcher = re.compile("(?P<label>[A-Z].*?): (?P<val>.*)")  # Capture distinct characteristics
    avg_matcher = re.compile("(?P<label>Avg.*) (?P<err>(±|\d).*%): (?P<val>\d.*%)")  # Split up the weird Avg. characteristics

    for n in range(1, len(line_list)):
        if line_list[n][0:3] == "Avg":  # Avg. Shrinkage/Absorption are weird, so handle these differently
            avg_split = avg_matcher.match(line_list[n])

            if avg_split is not None:
                clay_dict[avg_split.group("label").lower()] = avg_split.group("val")
                clay_dict[avg_split.group("label").lower() + " error"] = avg_split.group("err")
        else:
            char_split = characteristics_matcher.match(line_list[n])
            if char_split is not None:
                if char_split.group("label").lower() == 'sds sheetcharacteristicscone': #issue for Laguna
                    clay_dict['cone'] = char_split.group("val")
                elif char_split.group("label").lower()[0:3] == 'fir': #fired color naming is all over the place
                    clay_dict["fired color"] = char_split.group("val")
                else:
                    clay_dict[char_split.group("label").lower()] = char_split.group("val")

    return clay_dict


# Create a base list of clays with links to their respective pages.
def make_clay_list(brand):
    assert isinstance(brand, Manufacturer)
    browser = Chrome(options=opts)
    browser.get(brand.clay_url)
    browser.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    time.sleep(3)

    clay_page = browser.page_source

    slip = BeautifulSoup(clay_page, "html.parser")

    clay_dict = dict()

    if brand.manu == "laguna":
        clay_divs = slip.find_all('div', class_='ETPbIy EGg5Ga')

        for div in clay_divs:
            clay_link = div.find('a').get("href")
            clay_name = div.find("h3").text
            clay_dict[clay_name] = clay_link

    elif brand.manu == "rocky mountain":  # rocky mountain
        clay_ul = slip.find('ul', class_="products columns-4")
        clay_items = clay_ul.find_all('li')

        for div in clay_items:
            clay_link = div.find('a').get("href")
            clay_name = div.find("h2").text
            clay_dict[clay_name] = clay_link

    else:
        browser.quit()
        raise ValueError("Manufacturer not valid.")

    clay_list_df = pd.DataFrame(list(clay_dict.items()), columns=["clay", "page link"])

    clay_list_df.to_csv(brand.raw_clay_csv)
    browser.quit()


def wedge(brand):  # get raw info for each clay in a csv and update
    assert isinstance(brand, Manufacturer)
    browser = Chrome(options=opts)
    clay_dict = dict()

    try:
        clay_list_df = pd.read_csv(pathlib.Path(working_dir / brand.raw_clay_csv))

        link_content_dict = dict()

        for link in clay_list_df["page link"]:
            browser.get(link)
            time.sleep(1)
            clay_page = browser.page_source
            slip = BeautifulSoup(clay_page, "html.parser")
            link_content_dict[link] = slip

        browser.quit()

        for link in link_content_dict.keys():
            clay_content = link_content_dict[link].find(brand.content_tag, class_=brand.content_class)

            for br in clay_content.find_all("br"):
                br.replace_with("\n")

            clay_info = clay_content.find_all('p')
            p_content = [p.text for p in clay_info]
            clay_dict[link] = cut_list([line.strip() for entry in p_content for line in re.split("\n|\xa0", entry)])

    except:
        browser.quit()
        print("Clay list not found or formatted correctly, try making a clay list first.")

    clay_characteristics_df = pd.DataFrame(clay_dict).T.reset_index()
    final_clay_df = clay_list_df.merge(clay_characteristics_df, left_on="page link", right_on="index")
    final_clay_df.drop(['index'], axis=1, inplace=True)
    final_clay_df.to_excel(brand.final_clay_xlsx)


#Run the menu and get throwing!

while(True):
    print_manufacturer_selection_menu()
    option = input('Choice: ')

    if option in man_dict.keys():
        brand = Manufacturer(option)

        submenu = True

        while(submenu == True):
            print_action_selection_menu(brand)
            option2 = input('Choice: ')

            if option2 == "1":
                make_clay_list(brand)
                print("List of clay links created")
            elif option2 == "2":
                wedge(brand)
                print("Characteristics spreadsheet created. See " + brand.final_clay_xlsx)
            elif option2 == "3":
                print("Returning to manufacturer selection...")
                submenu = False
            elif option2 == "Q":
                exit()
            else:
                print('Invalid option.')

    elif option == "Q":
        exit()
    else:
        print('Invalid option.')