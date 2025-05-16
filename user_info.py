import json
import requests


class UserInfo():
    username = ''
    password = ''

    check_login_url = 'https://tasks-website.vercel.app/api/python/check_info'

    def get_username(self):
        with open('info/me.json', 'r') as f:
            info = json.load(f)
            self.username = info['username']
        return self.username

    def get_password(self):
        with open('info/me.json', 'r') as f:
            info = json.load(f)
            self.password = info['password']
        return self.password

    def set_username(self, new_username, new_password, set_text):
        print('set_username')
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
