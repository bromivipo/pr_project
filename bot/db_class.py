from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class Data:
    def __init__(self, db):
        self.__cursor = db.cursor()
        self.__db = db

    def add_user(self, id, log, psw):
        self.__cursor.execute(f"SELECT COUNT() as 'count' FROM logins WHERE user_id LIKE '{id}'")
        res = self.__cursor.fetchone()
        if res[0] > 0:
            return -1
        self.__cursor.execute(f"SELECT COUNT() as 'count' FROM logins WHERE login LIKE '{log}'")
        res = self.__cursor.fetchone()
        if res[0] > 0:
            return 0
        self.__cursor.execute("INSERT INTO logins VALUES(?, ?, ?)", (id, log, generate_password_hash(psw)))
        self.__db.commit()
        return 1

    def check_login(self, log, psw):
        self.__cursor.execute(f"SELECT user_id, password FROM logins WHERE login LIKE '{log}'")
        res = self.__cursor.fetchone()
        if res and check_password_hash(res['password'], psw):
            return res['user_id']
        return 0

    def add_personal(self, id, name, desc, deadl):
        self.__cursor.execute("INSERT INTO deadlines VALUES(NULL, ?, ?, ?, ?, ?)", (id, name, desc, deadl, "WAITING FOR SOLUTION"))
        self.__db.commit()
    
    def get_deadlines(self, id):
        wait = 'WAITING FOR SOLUTION'
        self.__cursor.execute(f"SELECT deadline_id, task_name, task_description, deadline FROM deadlines WHERE user_id LIKE '{id}' AND status LIKE '{wait}'")
        res = self.__cursor.fetchall()
        new_res = ""
        i = 1
        for row in res:
            new_res += f"\n{i}) id задачи - " + str(row[0])
            new_res += "\nНазвание задачи - " + str(row[1])
            new_res += "\nОписание задачи - " + str(row[2])
            if datetime.strptime(str(row[3]), "%d/%m/%Y %H:%M:%S") < datetime.now():
                new_res += "\nДедлайн(просрочен) - " + str(row[3])
            else:
                new_res += "\nДедлайн - " + str(row[3])
            i += 1
        return new_res

    def get_upcoming_deadlines(self, id):
        wait = 'WAITING FOR SOLUTION'
        self.__cursor.execute(f"SELECT deadline_id, task_name, task_description, deadline FROM deadlines WHERE user_id LIKE '{id}' AND status LIKE '{wait}'")
        res = self.__cursor.fetchall()
        new_res = ""
        i = 1
        for row in res:
            if datetime.strptime(str(row[3]), "%d/%m/%Y %H:%M:%S") >= datetime.now():
                new_res += f"\n{i}) id задачи - " + str(row[0])
                new_res += "\nНазвание задачи - " + str(row[1])
                new_res += "\nОписание задачи - " + str(row[2])
                new_res += "\nДедлайн - " + str(row[3])
                i += 1
        return new_res
    
    def set_deadline_done(self, dedl_id, user_id):
        done = "DONE"
        self.__cursor.execute(f"SELECT COUNT() as 'count' FROM deadlines WHERE user_id LIKE '{user_id}' AND deadline_id LIKE '{dedl_id}'")
        res = self.__cursor.fetchone()[0]
        if res == 0:
            return False
        self.__cursor.execute(f"UPDATE deadlines SET status = '{done}' WHERE deadline_id LIKE '{dedl_id}'")
        self.__db.commit()
        return True
    
    def delete_deadline(self, dedl_id, user_id):
        self.__cursor.execute(f"SELECT COUNT() as 'count' FROM deadlines WHERE user_id LIKE '{user_id}' AND deadline_id LIKE '{dedl_id}'")
        res = self.__cursor.fetchone()[0]
        if res == 0:
            return False
        self.__cursor.execute(f"DELETE FROM deadlines WHERE deadline_id LIKE '{dedl_id}'")
        self.__db.commit()
        return True