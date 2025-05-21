import json
import requests


class UserInfo():
    '''Класс, с помощью которого выполняется обращение к логину и паролю
    пользователя'''
    username = ''
    password = ''

    # URL запроса для обращения к серверу с целью проверки данных, введенных
    # пользователем
    check_login_url = 'https://tasks-website.vercel.app/api/python/check_info'

    def get_username(self):
        '''Функция геттер, считывает логин из файла и возвращает его'''
        with open('info/me.json', 'r') as f:
            info = json.load(f)
            self.username = info['username']
        return self.username

    def get_password(self):
        '''Функция геттер, считывает пароль из файла и возвращает его'''
        with open('info/me.json', 'r') as f:
            info = json.load(f)
            self.password = info['password']
        return self.password

    def set_data(self, new_username, new_password, set_text):
        '''Функция сеттер, проверяет логин и пароль пациента через запрос на сервер,
        если данные совпадают с данными из базы данных, то запомиинает их и выводит
        на экран сообщение об успехе, иначе выводится сообщение о неудаче'''
        print('set username and password')
        response = requests.post(self.check_login_url, json={'username': new_username,
                                                             'password': new_password})

        print(response)
        data = response.json()
        print(data)

        if response.status_code != 200:
            set_text("Неверные данные")
            return -1

        self.username = new_username
        self.password = new_password

        with open('info/me.json', 'r') as f:
            data = json.load(f)

        data['username'] = self.username
        data['password'] = self.password

        with open('info/me.json', 'w') as f:
            json.dump(data, f, indent=4)

        set_text("Пользователь сохранен")
