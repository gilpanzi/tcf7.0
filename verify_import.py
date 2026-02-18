import sqlite3
try:
    conn = sqlite3.connect('data/fan_pricing.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM MotorPrices WHERE Brand="BBL" AND "Motor kW"=7.5 AND Pole=2 AND Efficiency="IE2"')
    print(cursor.fetchone())
    conn.close()
except Exception as e:
    print(e)
