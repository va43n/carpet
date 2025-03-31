import requests
import os
import patoolib
import py7zr
from user_info import UserInfo


class Download():
    chunk_size = 1024
    url = 'https://tasks-website.vercel.app/api/python/download_files'
    dir_path = os.getcwd() + '/db/'
    user = UserInfo()

    def dowload_patient_files(self):
        username = self.user.get_username()
        if username == '':
            return -1

        response = requests.post(self.url, json={'username': username})

        print(response)

        if response.status_code == 200:
            data = response.json()
            for file_data in data['files']:
                file_url = file_data['fileUrl']
                file_name = file_url.split('/')[-1]
                file_path = self.dir_path + file_name

                with requests.get(file_url, stream=True) as r:
                    if r.status_code == 200:
                        with open(file_path, "wb") as file:
                            for chunk in r.iter_content(self.chunk_size):
                                file.write(chunk)
                        print(f'File {file_name} was downloaded on path '
                              f'{file_path}')

                        ext = file_name.split('.')[-1]
                        print(f'File has extention {ext}')

                        if ext == 'zip' or ext == 'rar' or ext == 'tar' or ext == 'gzip':
                            try:
                                patoolib.extract_archive(file_path, outdir=self.dir_path)
                                os.remove(file_path)
                                print(f'Archive was extracted and deleted')
                            except Exception as e:
                                print(f'Extracting error: {e}')
                        elif ext == '7z':
                            try:
                                with py7zr.SevenZipFile(file_path, mode='r') as archive:
                                    archive.extractall(path=self.dir_path)
                                os.remove(file_path)
                                print(f'Archive was extracted and deleted')
                            except Exception as e:
                                print(f'Extracting error: {e}')
                    else:
                        print(f'Cannot download file {file_name} '
                              f'{r.status_code}')
        else:
            print('Cannot get patient files:', response.status_code,
                                               response.text)
