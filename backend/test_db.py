import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        database="rpg_gamemaster",
        user="postgres",
        password="rpg11!"  
    )
    print("Połączenie z bazą działa!")
    conn.close()
except Exception as e:
    print(f"Błąd połączenia: {e}")