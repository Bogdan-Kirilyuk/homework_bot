# Telegram bot
## _Что должен делать бот_

- раз в 10 минут опрашивать API сервиса Практикум.Домашка и проверять статус отправленной на ревью домашней работы

 - при обновлении статуса анализировать ответ API и отправлять вам соответствующее уведомление в Telegram

 - логировать свою работу и сообщать вам о важных проблемах сообщением в Telegram.

#### Не забывай делать следующие штуки:
- Установите и активируйте виртуальное окружение
```
python3 -m venv venv
```
```
source venv/Scripts/activate
```
- Установить зависимости из файла requirements.txt
```
pip install -r requirements.txt
``` 
- Для запуска проекта, в папке с файлом manage.py выполните команду:
```
python homework.py
```
