# Quick and dirty (muddy even) tools to scrape clay characteristics from Laguna's website.

# Why would you mess with this code if you just want the data?
# I don't know. Maybe the spreadsheet is down. Maybe Laguna has some new clays.
# Just access the Google Sheet and get back to slinging that mud:

# Due to inconsistent formatting, this will return a pretty sloppy final csv.
# For example, firing color is split across five different columns due to variants in spelling/formatting.
# Some of these problems are pretty simple fixes in the Python console, but a few of the minor one-off issues are
# faster to edit in the final spreadsheet.

import re
from bs4 import BeautifulSoup
import pandas as pd
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
import pathlib
import time

laguna_link_re_get = """lagunaclay\.com/product-page/(?P<link>[A-Za-z\d-]*)\" class=\"JPDEZd(?:.*?)data-hook=\"product-item-name\">(?P<clay>[A-Za-z\s\d]*)<"""
laguna_clay_info_re_get = """<meta name=\"description\" content=\"(?P<description>.*)  Cone: (?P<cone>.*)Wet Color: (?P<wet>.*)Fired color: (?P<fired>.*)Texture: (?P<texture>.*)Penetrometer Target: (?P<pene>.*)Avg\. Water Absorption (?P<absorp>.*)Avg\. Shrinkage (?P<shrink>.*)COE (?P<coe>.*)\"/>"""

laguna_clay_url = "https://www.lagunaclay.com/shop?page=6"

laguna_product_page_url = "https://www.lagunaclay.com/product-page/"

working_dir = pathlib.Path.cwd()
raw_clay_csv_path = pathlib.Path(working_dir / "laguna_clay_list.csv")  #just info from the main list
wedged_clay_csv_path = pathlib.Path(working_dir / "laguna_clay_list_descripts.csv")  #with the raw descriptions
final_clay_csv_path = pathlib.Path(working_dir / "laguna_clay_list_final.csv")  #split out into different characteristics

desc_split_words = {"Cone:", "Wet Color:", "Firing Color:", "Texture:", "Consistency:",
                    "Avg. Shrinkage", "Avg. Water Absorption", "COE", "Penetrometer Target:"}


def cut_clay(raw):  # massage all of that no delimiter description content into categories
    clay_dict = dict()
    # split on "Cone:" first part is description, second part is clay characteristics (if it exists)

    first_split = re.split("Cone:", raw)

    # tidy up that description a little
    clean_descript = first_split[0].split("Ships from", 1)[0]
    clean_descript = clean_descript.split("Characteristics", 1)[0]
    clean_descript = clean_descript.split("SDS Sheet", 1)[0]


    clay_dict["description"] = clean_descript

    if len(first_split) > 1:  # we got clay characteristics!
        characteristics_matcher = re.compile("(.*?[a-z\d\%])([A-Z].*?\:)")  # Find all the distinct characteristics
        avg_matcher = re.compile("(?P<label>.*) (?P<percentage>\d.*)")  # Split up the weird Avg. characteristics

        coe_split = re.split("COE", first_split[1])
        # split off COE, this is formatted strangely
        if len(coe_split) > 1:
            clay_dict["coe"] = coe_split[1]

        # split up all of the characteristics: first should be cone, then alternate name and content
        clay_characteristics = characteristics_matcher.findall(first_split[1])

        try:  # but sometimes there isn't cone information for some reason...
            clay_dict["cone"] = clay_characteristics[0][0].strip()

            for n in range(0, len(clay_characteristics) - 1):
                if clay_characteristics[n][1][0:3] == "Avg":  # Avg. Shrinkage/Absorption are weird.
                    avg_split = avg_matcher.match(clay_characteristics[n][1])

                    clay_dict[avg_split.group(1).lower()] = avg_split.group(2) + clay_characteristics[n + 1][0]

                else:
                    clay_dict[clay_characteristics[n][1].lower().strip(":")] = clay_characteristics[n + 1][0].strip()
        except:
            return clay_dict
    return clay_dict


class TrimTools():  # Some methods to crawl Laguna's website with Selenium

    def __init__(self):
        opts = Options()
        opts.add_argument("--headless")
        self.browser = Chrome(options=opts)

    def make_clay_list(self):  # Get a base list of clays from Laguna
        self.browser.get(laguna_clay_url)
        self.browser.execute_script("window.scrollTo(0,document.body.scrollHeight)")
        time.sleep(3)

        laguna_clay_html = self.browser.page_source
        slip = BeautifulSoup(laguna_clay_html, "html.parser")

        #something like this, different tags/classes
        clay_names = slip.find('pre', class_='_28cEs').text

        #replace this
        clay_list = re.findall(laguna_link_re_get, laguna_clay_html)
        print(clay_list)


        clay_list_df = pd.DataFrame(clay_list, columns=["page link", "clay"])

        #modify this
        clay_list_df["page link"] = laguna_product_page_url + clay_list_df["page link"]


        clay_list_df.to_csv("laguna_clay_list.csv")

    def wedge(self):  # get info for each clay in a csv and update
        try:
            clay_list_df = pd.read_csv(raw_clay_csv_path)

            clay_dict = dict()

            for link in clay_list_df["page link"]:
                self.browser.get(link)
                time.sleep(1)
                clay_page = self.browser.page_source
                slip = BeautifulSoup(clay_page, "html.parser")
                clay_desc = slip.find('pre', class_='_28cEs').text  # looking for pre tag, class="_28cEs"
                clay_dict[link] = clay_desc

            clay_list_df['raw descripts'] = clay_list_df["page link"].map(clay_dict)
            clay_list_df.to_csv("laguna_clay_list_descripts.csv")

        except:
            print("Clay list not found or formatted correctly, try make_clay_list first.")

    def shape(self):  # format all those descriptions nicely and pull out the stats
        try:
            clay_list_df = pd.read_csv(wedged_clay_csv_path)

            clay_dict = dict()

            for clay in clay_list_df["clay"]:
                clay_dict[clay] = cut_clay(clay_list_df.loc[clay_list_df["clay"] == clay, 'raw descripts'].item())

        except:
            print("Clay list not found or formatted correctly, try wedge first")

        clay_characteristics_df = pd.DataFrame(clay_dict).T.reset_index()

        final_clay_df = clay_list_df.merge(clay_characteristics_df, left_on="clay", right_on="index")

        final_clay_df.to_csv(final_clay_csv_path)

