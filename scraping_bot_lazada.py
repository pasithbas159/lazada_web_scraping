from lib2to3.pgen2 import driver
import string
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
# from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import bs4
import time
import pandas as pd


class Lazada_Scraper: 
    def __init__(self): 
        self.driver = webdriver.Chrome(executable_path=r'.\chromedriver\chromedriver.exe')
        self.driver.get('https://www.lazada.co.th/')
        self.category = [self.driver.find_element_by_id('Level_1_Category_No' + str(i)) for i in range(1, 13, 1)]
        self.sub_category = [self.driver.find_element_by_xpath('/html/body/div[2]/div/div[2]/div/div/div/div/div/div/div/ul/ul[' + str(i) + ']') for i in range(1, 13, 1)]

    def get_category_info(self, url): 

        sub_cat_list = {}
        grand_cat_list = {}
        
        for i, cat in enumerate(self.category):
            # print(cat.text)
            cat.click()
            
            time.sleep(2)
            
            sub_cat_list[cat.text] = list(filter(None, self.sub_category[i].text.split('\n')))

            for j, sub_cat in enumerate(sub_cat_list[cat.text]): 
                SUB_PATH = '/html/body/div[2]/div/div[2]/div/div/div/div/div/div/div/ul/ul[' + str(i+1) + ']/li[' + str(j+1) + ']'
                GRAND_PATH = '/html/body/div[2]/div/div[2]/div/div/div/div/div/div/div/ul/ul[' + str(i+1) + ']/li[' + str(j+1) + ']/ul'

                hover = ActionChains(self.driver).move_to_element(self.driver.find_element_by_xpath(SUB_PATH))
                hover.perform()

                time.sleep(1)

                grand_category = []

                try:
                    grand_category.append(self.driver.find_element_by_xpath(GRAND_PATH))
                    grand_cat_list[sub_cat] = list(filter(None, grand_category[0].text.split('\n')))
                    # print(grand_cat_list[sub_cat])
                except NoSuchElementException: 
                    grand_cat_list[sub_cat] = ""
            
            # Get sub_category data into DataFrame
            sub_cat_data = pd.DataFrame()
            
            if sub_cat_data.empty:
                sub_cat_data = pd.DataFrame.from_dict(sub_cat_list, orient='index')
            else: 
                sub_cat_data.append(pd.DataFrame.from_dict(sub_cat_list, orient='index'), ignore_index=True)

            sub_cat_data = sub_cat_data.reset_index()
            sub_cat_data = pd.melt(sub_cat_data, id_vars=['index'], value_vars=sub_cat_data[1:].columns)

            # Get grand_category data into DataFrame
            grand_cat_data = pd.DataFrame()
            
            if grand_cat_data.empty: 
                grand_cat_data = pd.DataFrame.from_dict(grand_cat_list, orient='index')
            else: 
                grand_cat_data.append(pd.DataFrame.from_dict(grand_cat_list, orient='index'), ignore_index=True)
                
            grand_cat_data = grand_cat_data.reset_index()
            grand_cat_data = pd.melt(grand_cat_data, id_vars=['index'], value_vars=grand_cat_data[1:].columns)
        
        # Merge both DataFrame to category_table
        category_table = sub_cat_data.merge(grand_cat_data, left_on='value', right_on='index')
        category_table = category_table[~((~category_table['variable_y'].isin([0])) & category_table['value_y'].isna())]
        category_table['value_y'].fillna(category_table['variable_y'], inplace=True)
        category_table = category_table[['index_x', 'value_x', 'value_y']]
        category_table.columns = ['Category', 'Sub Category', 'Grand Category']
        category_table = category_table.reset_index()
        print(category_table.head())

        category_table.to_csv(r'.\category_data.csv')
        print('file save done!!')
            
        time.sleep(3)
        self.driver.quit()
        return category_table

    def get_grand_category_metadata(self, url, keyword: string): 

        sub_cat_list = {}
        grand_cat_list = {}

        for i, cat in enumerate(self.category):
            cat.click()
            
            time.sleep(2)

            sub_cat_list[cat.text] = list(filter(None, self.sub_category[i].text.split('\n')))

            for j, sub_cat in enumerate(sub_cat_list[cat.text]): 
                SUB_PATH = '/html/body/div[2]/div/div[2]/div/div/div/div/div/div/div/ul/ul[' + str(i+1) + ']/li[' + str(j+1) + ']'
                GRAND_PATH = '/html/body/div[2]/div/div[2]/div/div/div/div/div/div/div/ul/ul[' + str(i+1) + ']/li[' + str(j+1) + ']/ul'

                hover_sub = ActionChains(self.driver).move_to_element(self.driver.find_element_by_xpath(SUB_PATH))
                hover_sub.click(GRAND_PATH)
                hover_sub.perform()

                # time.sleep(1)

                # self.driver.implicitly_wait(5)


        
# =============================================================================
#         try:
#             element = WebDriverWait(driver, 10).until(
#                 EC.presence_of_element_located((By.ID, "myDynamicElement"))
#             )
#         finally:
#             driver.quit()
# =============================================================================
        

if __name__ == '__main__':
    bot = Lazada_Scraper()
    category_data = bot.get_category_info('https://www.lazada.co.th/') # get category info from lazada
    # bot.get_grand_category_metadata('https://www.lazada.co.th/', "Mobiles") # get results from each grand category