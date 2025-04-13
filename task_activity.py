import requests
from user_info import UserInfo


class TaskActivity():
    chunk_size = 1024
    task_started_url = 'https://tasks-website.vercel.app/api/python/task_started'
    task_ended_url = 'https://tasks-website.vercel.app/api/python/task_ended'
    user = UserInfo()

    def task_started(self, task_id):
        username = self.user.get_username()
        if username == '':
            return -1

        response = requests.post(self.task_started_url, json={'username': username,
                                                              'task_id': task_id})

        print(response)

        if response.status_code == 200:
            data = response.json()
            print('good luck!')
        else:
            print('Cannot start task on server:', response.status_code,
                                                  response.text)

    def task_ended(self, task_id, result):
        username = self.user.get_username()
        if username == '':
            return -1

        response = requests.post(self.task_ended_url, json={'username': username,
                                                              'task_id': task_id,
                                                              'result': result})

        print(response)

        if response.status_code == 200:
            data = response.json()
            print('task ended on server')
        else:
            print('Cannot end task on server:', response.status_code,
                                                response.text)
