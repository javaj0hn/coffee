import sqlite3
import time

def connect(target):
    return sqlite3.connect(target)

def getLeaderboard():
    try:
        db = connect('drunkcoin.db')
        data = db.execute('SELECT discord_id, balance FROM clients order by balance desc LIMIT 5').fetchall()
        db.commit()
        db.close()
        return data
    except Exception as e:
        return False

def enrollUser(data):
    try:
        db = connect('drunkcoin.db')
        db.execute('INSERT INTO clients(discord_id, balance) VALUES(?,?)', (data.discord_id, data.balance))
        db.commit()
        db.close()
        return True
    except Exception as e:
        return False

def getBalance(discord_id):
    try:
        db = connect('drunkcoin.db')
        data = db.execute('SELECT balance FROM clients WHERE discord_id = ?', (discord_id,)).fetchall()
        db.commit()
        db.close()
        return data
    except Exception as e:
        print(e)
        return False

def getFights():
    try:
        db = connect('drunkcoin.db')
        data = db.execute('SELECT id, title, date, status from fights where status = 1').fetchall()
        db.commit()
        db.close()
        return data
    except Exception as e:
        return False

def getResults():
    try:
        db = connect('drunkcoin.db')
        data = db.execute('')
        db.commit()
        db.close()
        return data
    except Exception as e:
        return False        