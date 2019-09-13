import sqlite3

############ WRITE TO DATABASE ###############

'''
#connection will create a database if one does not exist
connection = sqlite3.connect("test.db")

#create the cursor object
# multiple connections are OK
crsr = connection.cursor()

# SQL command, create the table
sql_command = """CREATE TABLE employee (
staff_number INT,
name VARCHAR(20));"""

crsr.execute(sql_command)

# add a row to the table
sql_command = """INSERT INTO employee VALUES(20, "TEST DUDE1!");"""
crsr.execute(sql_command)

#very important, do not skip!
# if there is something to commit, commit, else, move on
connection.commit()

# close the connection
# put in stop function
connection.close()
'''

############### READ DATABASE ##############


connection = sqlite3.connect("database.db")
crsr = connection.cursor()

# fetch all data from table employee
crsr.execute("SELECT * FROM licenseplates")

# store all fetched data into a variable
ans = crsr.fetchall()

for i in ans:
    print(i)

