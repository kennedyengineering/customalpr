import sqlite3
connection = sqlite3.connect("plate.db")
cursor = connection.cursor()
cursor.execute("SELECT * FROM plates")
result = cursor.fetchall()
for r in result:
	print(r)
connection.close()
