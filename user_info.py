import json


class UserInfo():
    username = ''

    def get_username(self):
        with open('info/me.json', 'r') as f:
            info = json.load(f)
            self.username = info['username']
        return self.username

    def set_username(self, new_username):
        self.username = new_username

        with open('info/me.json', 'r') as f:
            data = json.load(f)

        data['username'] = new_username

        with open('info/me.json', 'w') as f:
            json.dump(data, f, indent=4)
