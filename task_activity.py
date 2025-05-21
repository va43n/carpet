import requests
from user_info import UserInfo


class TaskActivity():
    '''Класс, используемый для отправки активности пациента на сервер'''

    # URL запроса для обращения к серверу с целью отправки сообщения о начале
    # выполнения задания
    task_started_url = 'https://tasks-website.vercel.app/api/python/task_started'

    # URL запроса для обращения к серверу с целью отправки сообщения о завершении
    # выполнения задания
    task_ended_url = 'https://tasks-website.vercel.app/api/python/task_ended'

    # Объект класса с информацией пользователя
    user = UserInfo()

    def task_started(self, task_id):
        '''Функция, отправляющая запрос на сервер о начале выполнения задания'''
        print('start', task_id)

        username = self.user.get_username()
        if username == '':
            return -1

        password = self.user.get_password()
        if password == '':
            return -1

        response = requests.post(self.task_started_url, json={'username': username,
                                                              'password': password,
                                                              'task_id': task_id})

        print(response)

        if response.status_code == 200:
            data = response.json()
            print('task started on server')
        else:
            print('Cannot start task on server:', response.status_code,
                                                  response.text)

    def task_ended(self, task_id, result):
        '''Функция, отправляющая запрос на сервер о завершении выполнения задания'''
        print('end', task_id)

        username = self.user.get_username()
        if username == '':
            return -1

        password = self.user.get_password()
        if password == '':
            return -1

        response = requests.post(self.task_ended_url, json={'username': username,
                                                            'password': password,
                                                            'task_id': task_id,
                                                            'result': result})

        print(response)

        if response.status_code == 200:
            print('task ended on server')
        else:
            print('Cannot end task on server:', response.status_code,
                                                response.text)
