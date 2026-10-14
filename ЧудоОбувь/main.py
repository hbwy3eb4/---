import os
import tkinter as tk
from tkinter import ttk, messagebox

import psycopg2
from PIL import Image, ImageTk

BASE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(BASE, "resources")
ALL = "Все категории"

try:
    conn = psycopg2.connect(host="localhost", dbname="chudoobuv", user="postgres",
                            password="qawser123098", client_encoding="UTF8")
except Exception as e:
    r = tk.Tk(); r.withdraw()
    messagebox.showerror("Ошибка", f"Не удалось подключиться к базе данных:\n{e}")
    raise SystemExit(1)

root = tk.Tk()
root.title("Чудо Обувь")
root.geometry("900x600")
try:
    root.iconbitmap(os.path.join(RES, "Чудо Обувь.ico"))
except tk.TclError:
    pass
photos = []


def load_image(name):
    for path in (os.path.join(RES, str(name)), os.path.join(RES, "picture.png")):
        try:
            return Image.open(path).resize((90, 90))
        except (OSError, ValueError):
            continue
    return Image.new("RGB", (90, 90), "#cccccc")


def load(event=None):
    for w in box.winfo_children():
        w.destroy()
    photos.clear()
    cat, text = combo.get(), ent.get().strip()
    sql = ("SELECT p.id, p.category, p.name, p.manufacturer, p.price, p.image_path, "
           "COALESCE((SELECT SUM(s.quantity) FROM stock_items s WHERE s.product_id = p.id), 0) "
           "FROM products p WHERE 1=1")
    params = []
    if cat != ALL:
        sql += " AND p.category = %s"
        params.append(cat)
    if text:
        sql += " AND (p.name ILIKE %s OR p.manufacturer ILIKE %s OR p.description ILIKE %s)"
        params += [f"%{text}%"] * 3
    sql += " ORDER BY p.id"
    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    conn.rollback()
    for pid, cat_, name, man, price, img, qty in rows:
        bg = "#ff8080" if qty <= 3 else "#D2F6E7"
        card = tk.Frame(box, bg=bg, bd=1, relief="solid")
        card.pack(fill="x", padx=5, pady=3)
        ph = ImageTk.PhotoImage(load_image(img))
        photos.append(ph)
        tk.Label(card, image=ph, bg=bg).pack(side="left", padx=5, pady=5)
        tk.Label(card, text=f"{man} | {name}\n{cat_}\nКол-во: {qty}", bg=bg, justify="left",
                 anchor="w").pack(side="left")
        tk.Label(card, text=f"{price:.0f} ₽", font=("Calibri", 16), bg=bg).pack(side="right", padx=10)
    canvas.yview_moveto(0)


# Верх: фильтр + поиск
top = tk.Frame(root)
top.pack(fill="x")
with conn.cursor() as cur:
    cur.execute("SELECT DISTINCT category FROM products ORDER BY category")
    cats = [ALL] + [r[0] for r in cur.fetchall()]
conn.rollback()
combo = ttk.Combobox(top, values=cats, state="readonly")
combo.set(ALL)
combo.pack(side="left", padx=5, pady=5)
combo.bind("<<ComboboxSelected>>", load)
ent = tk.Entry(top)
ent.pack(side="left", fill="x", expand=True, padx=5, pady=5)
ent.bind("<KeyRelease>", load)

# Скролл
sb = ttk.Scrollbar(root)
sb.pack(side="right", fill="y")
canvas = tk.Canvas(root, yscrollcommand=sb.set, highlightthickness=0)
sb.configure(command=canvas.yview)
canvas.pack(side="left", fill="both", expand=True)
box = tk.Frame(canvas)
win = canvas.create_window((0, 0), window=box, anchor="nw")
box.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.bind("<Configure>", lambda e: canvas.itemconfigure(win, width=e.width))
root.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))

load()
root.mainloop()
