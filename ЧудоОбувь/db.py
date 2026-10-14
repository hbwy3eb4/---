import os
import re

import pandas as pd
import psycopg2

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")


def norm(s):
    """Нормализация текста: неразрывные пробелы, лишние пробелы."""
    return re.sub(r"\s+", " ", str(s).replace("\xa0", " ")).strip()


def fix_latin(s):
    """Заменяет латинские буквы-двойники на кириллические (опечатки в Excel)."""
    table = str.maketrans({"e": "е", "a": "а", "o": "о", "p": "р", "c": "с", "x": "х", "y": "у"})
    return norm(s).translate(table)


def read(name):
    df = pd.read_excel(os.path.join(DATA, name))
    df.columns = [norm(c) for c in df.columns]
    return df


users = read("Users_import.xlsx")
sizes = read("Sizes_import.xlsx")
products = read("Products_import.xlsx")
stock = read("Stock_Items_import.xlsx")
orders = read("Orders_import.xlsx")

conn = psycopg2.connect(host="localhost", dbname="chudoobuv", user="postgres",
                        password="qawser123098", client_encoding="UTF8")
c = conn.cursor()

# Пересоздание таблиц по create_db.sql
c.execute("DROP TABLE IF EXISTS order_items,orders,stock_items,sizes,products,users,roles CASCADE")
with open(os.path.join(BASE, "create_db.sql"), encoding="utf-8") as f:
    c.execute(f.read())

# Роли и пользователи
role_ids = {}
for r in users["Роль"].map(norm).unique():
    c.execute("INSERT INTO roles(name) VALUES(%s) RETURNING id", (r,))
    role_ids[r] = c.fetchone()[0]

user_ids = {}
for _, r in users.iterrows():
    last, first, middle = fix_latin(r["Фамилия"]), fix_latin(r["Имя"]), fix_latin(r["Отчетсво"])  # опечатка в заголовке файла
    c.execute("INSERT INTO users(last_name,first_name,middle_name,login,role_id) VALUES(%s,%s,%s,%s,%s) RETURNING id",
              (last, first, middle, norm(r["Логин"]), role_ids[norm(r["Роль"])]))
    user_ids[f"{last} {first} {middle}"] = c.fetchone()[0]

# Размеры
size_ids = {}
for v in sizes["Размер"]:
    c.execute("INSERT INTO sizes(value) VALUES(%s) RETURNING id", (float(v),))
    size_ids[float(v)] = c.fetchone()[0]

# Товары
product_list = []  # (id, название, производитель)
for _, r in products.iterrows():
    name, man = norm(r["Наименование товара"]), norm(r["Производство"])
    c.execute("INSERT INTO products(category,subcategory,image_path,name,manufacturer,description,composition,price) "
              "VALUES(%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
              (norm(r["Категория"]), norm(r["Подкатегория"]), norm(r["Изображение"]), name, man,
               r["Описание"], r["Состав"], float(r["Цена"])))
    product_list.append((c.fetchone()[0], name, man))


def find_product(name, man):
    """Ищет товар по названию и производителю (допускает сокращённое название)."""
    name, man = norm(name), norm(man)
    for pid, pname, pman in product_list:
        if pname == name and pman == man:
            return pid
    for pid, pname, pman in product_list:
        if pman == man and (pname.startswith(name) or name.startswith(pname)):
            return pid
    return None


# Остатки
skipped = 0
for _, r in stock.iterrows():
    pid = find_product(r["Наименование товара"], r["Производство"])
    sid = size_ids.get(float(r["Размер"]))
    if pid and sid:
        c.execute("INSERT INTO stock_items(product_id,size_id,quantity) VALUES(%s,%s,%s)",
                  (pid, sid, int(r["Количество доступное для заказа"])))
    else:
        skipped += 1
        print("Пропущен остаток:", r["Наименование товара"], r["Размер"])

# Заказы
for number, grp in orders.groupby("Номер заказа", sort=True):
    first = grp.iloc[0]
    uid = user_ids.get(fix_latin(first["ФИО"]))
    c.execute("INSERT INTO orders(order_date,user_id) VALUES(%s,%s) RETURNING id",
              (pd.to_datetime(first["Дата заказа"]).date(), uid))
    oid = c.fetchone()[0]
    for _, r in grp.iterrows():
        pid = find_product(r["Наименование товара"], r["Производство"])
        sid = size_ids.get(float(r["Размер"]))
        if pid and sid:
            c.execute("INSERT INTO order_items(order_id,product_id,size_id,quantity,price) VALUES(%s,%s,%s,%s,%s)",
                      (oid, pid, sid, int(r["Количество"]), float(r["Цена за единицу"])))
        else:
            skipped += 1
            print("Пропущена позиция заказа:", number, r["Наименование товара"], r["Размер"])

conn.commit()
print("Готово", f"(пропущено строк: {skipped})")
