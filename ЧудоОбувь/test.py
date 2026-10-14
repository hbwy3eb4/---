import psycopg2
conn = psycopg2.connect(host="localhost", dbname="chudoobuv", user="postgres",
                        password="qawser123098", client_encoding="UTF8")
c = conn.cursor()

for t in ["roles","users","products","sizes","stock_items","orders","order_items"]:
    c.execute(f"SELECT COUNT(*) FROM {t}")
    print(f"{t:15} = {c.fetchone()[0]}")

print("---")
c.execute("SELECT category, COUNT(*) FROM products GROUP BY category")
for r in c.fetchall(): print("Категория:", r)

c.execute("SELECT login, last_name FROM users LIMIT 3")
for r in c.fetchall(): print("Юзер:", r)