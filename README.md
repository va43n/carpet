## Коврик
Разработка интерактивного приложения для реабилитационного комплекса с Raspberry Pi, направленного на содействие восстановлению ходьбы с использованием машинного зрения для отслеживания движений. Приложение связано с [Сайтом с заданиями](https://github.com/va43n/tasks-website).
![image](https://github.com/user-attachments/assets/e82257d5-e5d9-4e62-bba5-e90ba910999d)
![image](https://github.com/user-attachments/assets/e60e850f-0662-45e7-8a1c-4d648dbf643c)
![image](https://github.com/user-attachments/assets/70f34437-b435-4f2a-b00d-8cd31d92985a)

## Начало работы
Для работы с приложением понадобится Raspberry Pi версии не менее 4 model B с установленной камерой. Также потребуется проектор, подключенный к Raspberry, например, через microHDMI-HDMI. 
```bash
# Клонирование репозитория
git clone https://github.com/va43n/carpet.git
```
Запуск можно осуществлять вручную:
```bash
cd carpet
py main.py
```
Или настроить службу для автозапуска при включении. Для этого в папке /etc/systemd/system/ нужно создать файл carpet.service со следующим содержимым: 
```bash
[Unit]
Description=Python carpet program
After=network.target
Wants=network.target

[Service]
ExecStart=/usr/bin/python3 /home/login/Desktop/prog/main.py
WorkingDirectory=/home/login/Desktop/prog/
StandardOutput=inherit
StandardError=inherit
Restart=no
User=login
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/login/.Xauthority

[Install]
WantedBy=graphical.target
```
Затем службу нужно включить последовательностью команд:
```bash
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable carpet.service
sudo systemctl start carpet.service
```
## Основные функции
- Аутентификация пациентов из базы данных Сайта с заданиями;
- Автоматическое скачивание выбранных файлов заданий из базы данных Сайта с заданиями;
- Выбор и удаление задания из уже скачанных;
- Калибровка камеры;
- Поиск движущихся объектов;
- Отправка активностей пациента на сервер Сайта с заданиями.
## Стек технологий
Python: PyQt для интерфейса, Picamera2 для работы с камерой Raspberry Pi, cv2 для обработки кадров с камеры.
