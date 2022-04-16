from numpy import number
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementClickInterceptedException
# from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import bs4
import time
import pandas as pd


class Lazada_Scraper: 


    def __init__(self): 
        s = Service(r'.\chromedriver\chromedriver.exe')
        self.driver = webdriver.Chrome(service=s)
        self.driver.get('https://www.lazada.co.th/')
        self.category = [self.driver.find_element(by=By.ID, value='Level_1_Category_No' + str(i)) for i in range(1, 13, 1)]
        self.sub_category = [self.driver.find_element(by=By.XPATH, value='/html/body/div[2]/div/div[2]/div/div/div/div/div/div/div/ul/ul[' + str(i) + ']') for i in range(1, 13, 1)]


    def get_category_info(self): 

        sub_cat_list = {}
        grand_cat_list = {}
        
        for i, cat in enumerate(self.category):
            cat.click()
            
            time.sleep(1)
            
            sub_cat_list[cat.text] = list(filter(None, self.sub_category[i].text.split('\n')))

            for j, sub_cat in enumerate(sub_cat_list[cat.text]): 
                SUB_PATH = '/html/body/div[2]/div/div[2]/div/div/div/div/div/div/div/ul/ul[' + str(i+1) + ']/li[' + str(j+1) + ']'
                GRAND_PATH = '/html/body/div[2]/div/div[2]/div/div/div/div/div/div/div/ul/ul[' + str(i+1) + ']/li[' + str(j+1) + ']/ul'

                hover = ActionChains(self.driver).move_to_element(self.driver.find_element(by=By.XPATH, value=SUB_PATH))
                hover.perform()

                time.sleep(1)

                grand_category = []

                try:
                    grand_category.append(self.driver.find_element(by=By.XPATH, value=GRAND_PATH))
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


    def get_grand_category_metadata(self, keyword: str, num_pages: int): 

        sub_cat_list = {}
        grand_cat_list = {}

        for i, cat in enumerate(self.category):
            cat.click()
            
            time.sleep(1)

            sub_cat_list[cat.text] = list(filter(None, self.sub_category[i].text.split('\n')))

            for j, sub_cat in enumerate(sub_cat_list[cat.text]): 
                SUB_PATH = '/html/body/div[2]/div/div[2]/div/div/div/div/div/div/div/ul/ul[' + str(i+1) + ']/li[' + str(j+1) + ']'
                GRAND_PATH = '/html/body/div[2]/div/div[2]/div/div/div/div/div/div/div/ul/ul[' + str(i+1) + ']/li[' + str(j+1) + ']/ul'

                time.sleep(1)

                grand_category = []

                try:
                    hover_sub = ActionChains(self.driver).move_to_element(self.driver.find_element(by=By.XPATH, value=SUB_PATH))
                    hover_sub.perform()

                    grand_element = self.driver.find_element(by=By.XPATH, value=GRAND_PATH)

                    grand_category.append(grand_element)
                    grand_cat_list[sub_cat] = list(filter(None, grand_category[0].text.split('\n')))
                    # print(grand_cat_list[sub_cat])
                    for key in grand_cat_list[sub_cat]:
                        # print(key)
                        if key == keyword: 
                            print('Keyword Matched: ', keyword)
                            grand_click = self.driver.find_element(by=By.LINK_TEXT, value=key)
                            grand_click.click()
                            
                            self.scraping_metadata(keyword=key, pages=num_pages)
                            return
                        else: 
                            pass
                except NoSuchElementException: 
                    pass

        print('The keyword does not matched in any category.')


    def scraping_metadata(self, keyword: str, pages: int):
        NEXT_PATH = 'ant-pagination-next'
        count = 1
        all_product_list = []
        all_price_list = []
        number_of_pages = 102

        while count <= pages:
            if count <= number_of_pages: 
                print('Current Page:', str(count))
                time.sleep(4)
                self.driver.implicitly_wait(10)
                self.driver.execute_script("document.body.style.zoom='10%'")

                data = self.driver.page_source
                soup = bs4.BeautifulSoup(data, features="html.parser")

                self.driver.execute_script("document.body.style.zoom='100%'")
                # time.sleep(5)

                try: 
                    WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.CLASS_NAME, NEXT_PATH))).click()
                except ElementClickInterceptedException: 
                    print('except')
                    next_page = ActionChains(self.driver).move_to_element(self.driver.find_element(by=By.CLASS_NAME, value=NEXT_PATH))
                    next_page.click().perform()
                    # time.sleep(5)

                # Get product name from lazada
                all_product = soup.find_all('div', {'class':'RfADt'})

                for product in all_product:
                    all_product_list.append(product.text)

                # Get price from lazada
                all_price = soup.find_all('div', {'class':'aBrP0'})

                for price in all_price: 
                    all_price_list.append(price.text)

                print('The data is collected')
                count += 1

            else: 
                print('Scraping done!!!')
                # print('Page:', str(count))

        # Merge all list into DataFrame
        lazada_data = pd.DataFrame([all_product_list, all_price_list])

        lazada_data = lazada_data.transpose()
        lazada_data.columns = ['title', 'price']

        # Save metadata into csv file
        lazada_data.to_csv(r'.\lazada_metadata_{}.csv'.format(keyword), encoding='utf-8-sig')

        print('The data is saved!!')
        self.driver.quit()

        return lazada_data

       
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
    # category_data = bot.get_category_info('https://www.lazada.co.th/') # get category info from lazada
    df = bot.get_grand_category_metadata(keyword="Mobiles", num_pages=10) # get results from each grand category