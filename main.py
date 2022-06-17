import datetime
import os.path
import time
import traceback
from typing import NamedTuple

import openpyxl
from pyvirtualdisplay.smartdisplay import SmartDisplay
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import httplib2

from file import read_file
from typing_class import DisplaySelf, Item, ItemInput


def my_print(text, name_file, is_print=True):
    type_time = "%d.%m.%Y_%H:%M:%S"
    if is_print:
        print(f'{datetime.datetime.now().strftime(type_time)} {text}')
    with open(name_file, 'a', encoding='utf-8') as file:
        file.write(f'{datetime.datetime.now().strftime(type_time)} {text}\n')


def get_webdriver_chrome():
    # options
    options = webdriver.ChromeOptions()

    # user-agent
    options.add_argument("user-agent=Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0")

    # for ChromeDriver version 79.0.3945.16 or over
    options.add_argument("--disable-blink-features=AutomationControlled")

    # headless mode
    # options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument('--disable-dev-shm-usage')
    # options.headless = True

    # Headless MODE - скрываем браузер
    options.headless = False

    # Hide browser Errors in bat executing
    # options.add_argument('log-level=3')
    options.add_argument('--enable-logging --log-level=1')

    options.add_argument('--no-sandbox')
    options.add_argument("--disable-dev-shm-usage")

    options.add_argument('--disable-gpu')
    options.add_argument('--no-default-browser-check')

    s = Service('/usr/local/bin/chromedriver')
    driver = webdriver.Chrome(
        service=s,
        options=options
    )
    driver.maximize_window()
    driver.set_page_load_timeout(10)
    driver.implicitly_wait(10)

    return driver


def download_image(link_image: str, path: str, h: httplib2.Http):
    """Скачиваем изображение с сервера и сохраняем в папку"""
    response, content = h.request(link_image)
    out = open(path, 'wb')
    out.write(content)
    out.close()


def get_images(driver: webdriver.Chrome, ean: int):
    """Получаем изображения товара"""
    images = driver.find_element(By.XPATH, "//div[@data-widget='webGallery']").find_elements(By.TAG_NAME, 'img')

    print(len(images))

    h = httplib2.Http('.cache')
    folder = os.path.join('img', str(ean))

    try:
        os.makedirs(folder)
    except FileExistsError:
        pass

    for number, image in enumerate(images, start=0):
        # Это не главное изображение товара, сохраняем его
        if image != images[0]:
            path = os.path.join(folder, f'{number}.jpg')
            # print(image.get_attribute('src'))
            link_image = image.get_attribute('src').replace('/wc50/', '/wc1200/')

            # Это ссылка на внутренний ресурс OZONE
            if 'https://cdn1.ozone.ru' in link_image:
                # print(link_image)

                download_image(link_image, path, h)


def parsing_one_item(driver: webdriver.Chrome, link: str, item_input: ItemInput, name_file: str):
    """Парсим параметры одного товара"""
    driver.get(link)
    time.sleep(1)

    name = driver.find_element(By.XPATH, "//div[@data-widget='webProductHeading']").text.split(' |')[0]
    print([name])

    dict_result = {'name': name}

    driver.execute_script("window.scrollTo(0, 2000)")
    time.sleep(0.5)

    characteristics = driver.find_element(By.ID, 'section-characteristics').find_elements(By.TAG_NAME, 'dl')
    print(len(characteristics))
    dict_characteristics = {}

    for characteristic in characteristics:
        # print([characteristic.text])
        if characteristic.text:
            print([characteristic.text])
            try:
                key, value = characteristic.text.split('\n')
            except ValueError:
                key, value = characteristic.text.split(': ')
            dict_characteristics[key] = value

    # print(dict_characteristics)

    # Это нужный товар
    if dict_characteristics['Издательство'] == item_input.publishing_house:

        description = driver.find_element(By.ID, 'section-description').find_elements(By.TAG_NAME, 'div')[-1].text

        item = Item(code=item_input.code, isbn=item_input.isbn, ean=item_input.ean,
                    publishing_house=item_input.publishing_house, name=name, author=dict_characteristics.get('Автор'),
                    series=dict_characteristics.get('Серия'), year_of_issue=dict_characteristics.get('Год выпуска'),
                    cover_type=dict_characteristics.get('Тип обложки'),
                    illustrator=dict_characteristics.get('Иллюстратор'),
                    age_restrictions=dict_characteristics.get('Возрастные ограничения'),
                    number_of_pages=dict_characteristics.get('Количество страниц'),
                    paper_type=dict_characteristics.get('Тип бумаги'),
                    reader_age=dict_characteristics.get('Возраст читателя'),
                    product_weight=dict_characteristics.get('Вес товара, г'), description=description)

        print(item)

        get_images(driver, item.ean)

    else:
        my_print(f'Не подходит издательство, {dict_characteristics["Издательство"]}, '
                 f'а нужно: {item_input.publishing_house}, EAN: {item_input.ean}, {link}', name_file)


def parsing_one_link(driver: webdriver.Chrome, item_input: ItemInput, name_file: str):
    """Парсим товары с одной ссылки"""

    arr_all_links = []
    link = f'https://www.ozon.ru/search/?text={item_input.ean}&from_global=true'

    driver.get(link)

    items_shop = driver.find_element(By.XPATH, "//div[@data-widget='searchResultsV2']")\
        .find_elements(By.CLASS_NAME, 'tile-hover-target')

    my_print(f'Товаров с EAN {item_input.ean}: {len(items_shop)}', name_file)

    for item_shop in items_shop:
        link_item_shop = item_shop.get_attribute('href')

        if link_item_shop not in arr_all_links:
            arr_all_links.append(link_item_shop)

    for link_item_shop in arr_all_links:
        print(link_item_shop)
        parsing_one_item(driver, link_item_shop, item_input, name_file)

    x = input('dsf')


def parsing_all_items(name_file: str, display: SmartDisplay):
    """Парсим все товары из входного файла"""

    arr_input = read_file()

    driver = get_webdriver_chrome()

    len_arr_all_links = len(arr_input)
    number = 1

    # Создаем выходной файл
    date_update = datetime.datetime.today().strftime("%H.%M.%S %Y-%m-%d")
    file_name = f'result/Результат ' + date_update + '.xlsx'
    number_row = 2
    try:
        os.mkdir('result')
    except FileExistsError:
        pass

    wb = openpyxl.load_workbook('template_result.xlsx')
    wb.save(file_name)

    for item_input in arr_input:

        my_print(f'Ссылка {number} из {len_arr_all_links}, EAN: {item_input.ean}', name_file)
        parsing_one_link(driver, item_input, name_file)
        # for number_error in range(1, 4):
        #     try:

                # parsing_one_link(driver, item_input)
                # number_row = save_one_item(dict_input, number_row, file_name)
                # break


            # except:
            #     my_print(f'Ошибка ({number_error}/3)\n :{traceback.format_exc()}', name_file)
            #     time_now = datetime.datetime.strftime(datetime.datetime.now(), "%Y.%m.%d %H:%M:%S")
            #     with open('error.txt', 'a', encoding='utf-8') as file:
            #         text_error = f"""{'*' * 100}
            #                                            \n{time_now}
            #                                            \n{item_input.ean}
            #                                            \n{traceback.format_exc()}\n"""
            #         file.write(text_error)
            #     if number_error == 3:
            #         pass
                    # number_row = save_one_item(dict_input, number_row, file_name)
                    # dict_input["competitor"] = 0, []
                    # dict_input["name"] = '?'

        number += 1




def main(need_display=False):

    if need_display:
        display = SmartDisplay(size=(1920, 1080), backend='xvfb')
        display.start()
    else:
        display = DisplaySelf()

    name_dir = 'logs'

    if not os.path.exists(name_dir):
        os.mkdir(name_dir)

    try:
        name_file = os.path.join(name_dir, f'my_log_{datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S")}.txt')

        parsing_all_items(name_file, display)
    except:
        my_print(f'Ошибка :{traceback.format_exc()}', name_file)
        time_now = datetime.datetime.strftime(datetime.datetime.now(), "%Y.%m.%d %H:%M:%S")
        with open('error_main.txt', 'a', encoding='utf-8') as file:
            text_error = f"""{'*' * 100}
                                                       \n{time_now}
                                                       \n{traceback.format_exc()}\n"""
            file.write(text_error)

    display.stop()


    # x = input('Нажмите ENTER для выхода... ')
    #
    #
    #
    # driver = get_webdriver_chrome()
    # ean = '9785978108804'
    # ean = '97859781088049'
    # link = 'https://www.ozon.ru/product/sem-gnomov-knizhka-s-raskraskoy-kozhevnikov-viktor-dmitrievich-268579992/?asb=IAhQNWxN71av9TLA9kUQ5ShSmj7597a%252FwRQiSn%252B4A%252Bg%253D&asb2=ypnAwEv2pKBjdxv0D12TGKhJyOnk9EuC8fWSSeuZowO_HXQn1NhO1P9qvSDawzl8&keywords=9785978108804&sh=4AXjGyh1yg'
    # link = 'https://www.ozon.ru/product/chasodei-chasovaya-bashnya-kniga-3-148803723/?advert=uWpZq_pwKxG1wKKUaEmNmyxSFn6VZQGyXuDBe-fCWojvW1zsoDiOzGwhtu-1xXWxmqQ54_PPpI4r1aRY7GrcBzD_D5c9rjJr_h_LUwHPNYfNJxSxeh6qpVS8pg&sh=gGdeRjkZdA'
    # parsing_one_item(driver, link, ean)


if __name__ == '__main__':
    main()


