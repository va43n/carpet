import requests
import os
import json

import py7zr

from user_info import UserInfo


class Download():
    '''Класс для скачивания заданий с сервера на Коврик'''

    # Размер порции в байтах, которыми будет выполняться скачивание файлов 
    chunk_size = 1024

    # URL запроса для обращения к серверу с целью скачивания данных
    url = 'https://tasks-website.vercel.app/api/python/download_files'

    # Путь к каталогу, в который необходимо скачать файлы
    dir_path = os.getcwd() + '/db/'

    # Объект класса с информацией пользователя
    user = UserInfo()

    def download_patient_files(self):
        '''Функция для скачивания файлов пациента'''
        username = self.user.get_username()
        if username == '':
            return -1

        password = self.user.get_password()
        if password == '':
            return -1

        # Запрос на сервер
        response = requests.post(self.url, json={'username': username,
                                                 'password': password})

        print(response)

        if response.status_code != 200:
            print('Cannot get patient files:', response.status_code,
                                               response.text)
            return -1

        # Получение данных
        data = response.json()

        # Для каждого полученного файла, определяемого ссылкой на
        # скачивание, названием и id, необходимо выполнить установку
        for file_data in data['files']:
            file_url = file_data['file_url']
            file_name = file_url.split('/')[-1]
            file_path = self.dir_path + file_name

            # Скачивание файла по ссылке 
            with requests.get(file_url, stream=True) as r:
                if r.status_code != 200:
                    print(f'Cannot download file {file_name} '
                          f'{r.status_code}')
                    continue

                with open(file_path, "wb") as file:
                    for chunk in r.iter_content(self.chunk_size):
                        file.write(chunk)
                print(f'File {file_name} was downloaded on path '
                      f'{file_path}')

                ext = file_name.split('.')[-1]
                print(f'File has extention {ext}')

                # Файл необходимо разархивировать. Подразумевается, что
                # файл архивируется с помощью 7zip
                if ext != '7z':
                    os.remove(file_path)
                    continue

                try:
                    with py7zr.SevenZipFile(file_path, mode='r') as archive:
                        files_in_archive = archive.getnames()
                        old_name = files_in_archive[0]

                        old_path = self.dir_path + old_name
                        new_path = self.dir_path + file_data['task_id']

                        archive.extractall(path=self.dir_path)

                        os.rename(old_path, new_path)

                        # В файл задания необходимо поместить информацию
                        # о названии задания, логине пациента и id задания
                        task_info = {}
                        with open(f'{new_path}/task.json', 'r') as file:
                            task_info = json.load(file)

                        task_info['title'] = file_data['title']
                        task_info['username'] = username
                        task_info['task_id'] = file_data['task_id']

                        with open(f'{new_path}/task.json', 'w') as file:
                            json.dump(task_info, file, indent=4)

                    os.remove(file_path)

                    print(f'Archive was extracted and deleted')
                except Exception as e:
                    os.remove(file_path)
                    print(f'Extracting error: {e}')
