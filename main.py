from os import getcwd
from bs4 import BeautifulSoup
from selenium import webdriver
from time import sleep
from random import uniform
from tkinter import *



def formation_out_page(out):
    with open("form_for_block.html", "r") as f:
        form_for_block = f.read() # форма для блоку рекламного поста

    with open("form_for_page.html", "r") as f:
        form_for_page = f.read() # форма для вихідної сторінки

    out = [form_for_block.format(*post) for post in out] # створення масиву з блоками рекламних постів

    with open("out.html", "w") as f: # запис вихідної сторінки в файл out.html
        f.write(form_for_page.format("\n\n".join(out))) # об'єднуєм масив з блоками і підставляєм у вихідну сторінку


def parse_video(soup, post_image):
    ajaxify = soup.find("a", class_="_27w8 _24mq _360f")["ajaxify"]    # знаходим id відео
    ajaxify = ajaxify.split("&id=")[1].split("&")[0]

    href = soup.find("a", class_="_2za_ _5p5v")["href"]     # знаходим нік автора
    href = href.split("/")[2]

    width = post_image["width"]     # визначаємо потрібні розміри
    height = post_image["height"]

    string = '<iframe src="https://www.facebook.com/plugins/video.php?href=https%3A%2F%2Fwww.facebook.com%2F{0}%2Fvideos%2F{1}%2F&show_text=0&width=476" width="{2}" height="{3}" style="border:none;overflow:hidden" scrolling="no" frameborder="0" allowTransparency="true" allowFullScreen="true"></iframe>'
    # форма для відео
    string = string.format(href, ajaxify, width, height)
    # підставили дані
    return string


def formation_arr_out(arr_advertising):
    out = []    # вихідний масив з відфільтрованими даними, які ми будемо підставляти у form_for_block
    for ads in arr_advertising:   # перебираєм кожну рекламу
        soup = BeautifulSoup(ads, 'html.parser')


        page_title = soup.find("span", class_="fwb fcg")  # назва сторінки
        if page_title == None:
            page_title = soup.find("span", class_="fwn fcg")
        page_title["class"] = "page_title"    # свої стилі


        # пошук посилання
        detailed = soup.find("div", class_="_3ekx _29_4")   # звичайне посилання реклами під картинкою
        if detailed == None:
            detailed = soup.find("div", class_="__x9")  # якщо журнал фоток з ссилками
        if detailed == None:
            detailed = soup.find("div", class_="_6ks")  # посилання в фото
        if detailed != None:
            detailed = soup.find("a")
            detailed.string = "Подробнее"  # міняємо текст посилання


        # пошук відео/зображення
        post_image = soup.find("video")
        if post_image == None:  # якщо пост з картинкою
            post_image = soup.find("img", class_="scaledImageFitWidth img")
            try:
                post_image["class"] = "post_image"  # встановлюємо свої стилі
            except:
                post_image = soup.find_all("img")[1]
                post_image["class"] = "post_image"
        else: # якщо пост з відео
            post_image = parse_video(soup, post_image)  # крім soup передаєм ще відео, щоб визначити його розміри


        out.append([
            soup.find("img"),  # ава
            page_title,     # нік автора
            soup.find("div", class_="_5pbx userContent _3576"),  # description
            post_image,  # картинка/відео реклами
            detailed  # посилання реклами
        ])
    return out


def scrolling(count_post, driver):
    for i in range(10):  # скролим для початку 10 разів
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # скролити стрічку
        sleep(uniform(3, 5)) # ждем, поки підгрузиться

    
    i = 0   # лічильник
    count_post_now = len(driver.find_elements_by_xpath('//div[@class="_1dwg _1w_m _q7o"]'))  # рахуєм кількість постів на даний момент
    count_post_last = count_post_now  # створюємо змінну для порівняння з минулою кількістю постів в стрічці
    while count_post > count_post_now:  # поки кількість постів не буде >= заданій
        count_post_now = len(driver.find_elements_by_xpath('//div[@class="_1dwg _1w_m _q7o"]'))
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")   # скролим до кінця стрічки
        sleep(uniform(3, 5))    # пауза, щоб прогрузилися наступні пости
        if count_post_last == count_post_now:   # якщо минула кількість співпадає з теперішньою
            i += 1
        else:
            i = 0   # якщо не співпадає - обнуляєм лічильник
        if i == 3:  # якщо протягом трьох повторів кількість постів в стрічці не збільшилась
            break   # то ми зупиняємо цикл
        count_post_last = count_post_now



def getads(count_post, driver):

    scrolling(count_post, driver) # скролим стрічку

    arr_post = driver.find_elements_by_xpath('//div[@class="_1dwg _1w_m _q7o"]') # дістаєм всі пости з стрічки
    arr_post = [i.get_attribute("outerHTML") for i in arr_post] # переводим кожен пост в html

    driver.quit() # закриваєм вкладку

    arr_advertising = [ads for ads in arr_post if "Реклама</b>" in ads or "Advertising</b>" in ads] # вибираємо серед постів рекламу

    print("Parsed post: ", len(arr_post), "; Advertising: ", len(arr_advertising)) # кількість зпарсених постів, серед них рекламних

    out = formation_arr_out(arr_advertising) # формуємо масив з відфільтрованими даними кожного рекламного поста

    formation_out_page(out) # формуємо вихідну сторінку

    driver = webdriver.Firefox(executable_path=getcwd()+"/geckodriver")
    driver.get("file://" + getcwd() + '/out.html') # Відкриваємо out.html в firefox


def main():
    driver = webdriver.Firefox(executable_path=getcwd()+"/geckodriver") # відкриваєм вікно firefox
    #os.getcwd() - шлях до даної директорії
    sleep(uniform(1, 3)) # пауза
    driver.get('https://www.facebook.com/')  # переходим на FB
    sleep(uniform(2, 5))

    def clicked():
        count_post = int(spin.get())  # отримуємо від користувача кількість постів які потрібно зпарсити
        window.destroy()    # закриваєм вікно tkinter
        getads(count_post, driver)  # передаємо потрібні дані у наступну функцію

    window = Tk()
    lbl = Label(window, text="Авторизуйтесь в Facebook пожалуйста.\nПосле авторизации введите какое примерное количество постов нужно спарсить:")
    lbl.pack()
    spin = Spinbox(window, from_=0, to=5000, width=5)
    spin.pack()
    btn = Button(window, text="Enter", command=clicked)
    btn.pack()
    window.mainloop()

main()