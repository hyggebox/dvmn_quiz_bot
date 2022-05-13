# Бот-автоответчик для Telegram и ВК



## Требования

- Для запуска вам понадобится Python 3.6 или выше.
- Токен телеграм-бота (создайте бота через диалог с ботом 
[@BotFather](https://telegram.me/BotFather) и получите токен) 
- API-ключ сообщества в Контакте. Для этого необходимо:
  1. создать сообщество в ВК
(или использовать имеющееся, в которой вы админ), 
  2. получить ключ доступа в 
настройках сообщества **Работа с API**,
  3. в разделе **Сообщения** разрешить отправку сообщений.
- Адрес, порт и пароль базы данных [Redis](https://redislabs.com/)


## Переменные окружения

<table>
<tr>
<td>Переменная</td>
<td>Тип данных</td>
<td>Значение</td>
</tr>
<tr>
<td>DB_ENDPOINT</td>
<td>str</td>
<td>Адрес базы данных <a href="https://redislabs.com/">Redis</a> вида: redis-13965.f18.us-east-4-9.wc1.cloud.redislabs.com</td>
</tr>
<tr>
<td>DB_PORT</td>
<td>int</td>
<td>Порт базы данных</td>
</tr>
<tr>
<td>DB_PASSWORD</td>
<td>str</td>
<td>Пароль к базе данных</td>
</tr>
<tr>
<td>VK_TOKEN</td>
<td>str</td>
<td>Ключ доступа вашего сообщества ВК</td>
</tr>
<tr>
<td>VK_ADMIN_USER_ID</td>
<td>str</td>
<td>user id администратора сообщества (этому пользователю будут приходить логи бота)</td>
</tr>
<tr>
<td>TG_BOT_TOKEN</td>
<td>str</td>
<td>Токен Телеграм-бота</td>
</tr>
<tr>
<td>TG_ADMIN_CHAT_ID</td>
<td>str</td>
<td>ID администратора в Телеграм (этому пользователю будут приходить логи бота)</td>
</tr>
</table>


## Установка

- Загрузите код из репозитория
- Создайте файл `.env` в корневой папке и пропишите переменные окружения 
в формате: `ПЕРЕМЕННАЯ=значение`

- Установите зависимости командой:
```shell
pip install -r requirements.txt
```


### Запуск бота

Зарпустите ботов командами:
```commandline
python tg_bot.py
python vk_bot.py
```

## Пример реализации бота
Вариант чата с ботом в Telegram:

![](http://g.recordit.co/3rpBRa8S5t.gif)

Демо реализации бота:  
- [@GreatSpacePicsBot](https://telegram.me/GreatSpacePicsBot)  
- [Бот в ВК](https://vk.com/im?sel=-184085204)