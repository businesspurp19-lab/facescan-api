import mysql.connector

conn = mysql.connector.connect(

    host="sql304.infinityfree.com",

    user="if0_42591666",

    password="lYWKwj5rSZE",

    database="if0_42591666_facescan_db"
)

cursor = conn.cursor()