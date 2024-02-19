import telebot
import requests
import hashlib
from datetime import datetime, timedelta
import io

bot = telebot.TeleBot('6657725681:AAFgGYlrtM2t9WzPfk73VLbqivQXd-LLNAk')

user_tickets_data = {}
user_hotels_data = {}
user_contexts_tickets = {}
user_contexts_hotels = {}


@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button_tickets = telebot.types.KeyboardButton('Поиск авиабилетов')
    button_hotels = telebot.types.KeyboardButton('Поиск отелей')
    button_website = telebot.types.KeyboardButton('Перейти на сайт')
    button_help = telebot.types.KeyboardButton('Помощь')
    markup.add(button_tickets, button_hotels, button_website, button_help)
    bot.send_message(chat_id, 'Добро пожаловать в Wantee. Спланируйте свое идеальное путешествие с нами!',
                      reply_markup=markup)

# Обработчик кнопки "Перейти на сайт"
@bot.message_handler(func=lambda message: message.text == 'Перейти на сайт')
def open_website(message):
    chat_id = message.chat.id
    website_link = 'https://wantee.unisender.cc/'

    # Отправляем ссылку на сайт с отключенным предпросмотром веб-страницы
    bot.send_message(chat_id, website_link, disable_web_page_preview=True)

# Обработчик кнопки "Помощь"
@bot.message_handler(func=lambda message: message.text == 'Помощь')
def open_help(message):
    chat_id = message.chat.id
    help_text = (f'Если у вас есть вопросы, пожелания или вы столкнулись с проблемой, '
                 f'напишите https://t.me/georgeriaskin')

    # Отправляем ссылку на чат с отключенным предпросмотром веб-страницы
    bot.send_message(chat_id, help_text, disable_web_page_preview=True, parse_mode='html')

def ask_question(chat_id, questions, current_step):
    bot.send_message(chat_id, questions[current_step], parse_mode='html')

def autocomplete_city(term):
    url = f"https://autocomplete.travelpayouts.com/places2?locale=ru&types[]=city&term={term}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        return []

# Обработчик inline-кнопок, которые переключают билеты (сюда можно добавить и переключение отелей)
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id

    if call.data == "next_ticket":
        # Вызываем функцию отправки билетов снова для текущего пользователя
        send_tickets(chat_id, user_tickets_data[chat_id]['ticket_data'])

    # Переключение отелей будет проверяться условием if call.data == "next_hotel"
    if call.data == 'next_hotel':
        send_hotels(chat_id, user_hotels_data[chat_id]['hotels_data'])

# Функция проверки даты
def is_valid_date(date_str):
    try:
        date = datetime.strptime(date_str, '%d.%m.%Y').date()
        return date >= datetime.today().date()
    except ValueError:
        return False

# Функция преобразования даты для функции send_tickets
def format_date(date_str):
    # Преобразовываем строку с датой в объект datetime
    date = datetime.fromisoformat(date_str)

    # Список названий месяцев на русском
    month_names = [
        'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
        'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
    ]

    # Форматируем дату
    formatted_date = f"{date.day} {month_names[date.month - 1]} {date.year} года"

    return formatted_date

# Функция преобразования времени
def format_time(time_str):
    # Преобразовываем строку с временем в объект datetime
    time = datetime.fromisoformat(time_str).time()

    # Переводим время из UTC в МСК
    moscow_time = (datetime.combine(datetime.today(), time) + timedelta(hours=3)).time()

    # Форматируем время
    formatted_time = f"{moscow_time.hour:02d}.{moscow_time.minute:02d} МСК"

    return formatted_time

# Функция для формирования сигнатуры
def calculate_md5(string):
    # Создаем объект хеша MD5
    md5_hash = hashlib.md5()

    # Кодируем строку в байты и обновляем хеш
    md5_hash.update(string.encode('utf-8'))

    # Получаем MD5-хеш в виде строки
    md5_signature = md5_hash.hexdigest()

    return md5_signature

# Получение локального IP адреса (НУЖНО ЗАМЕНИТЬ НА USER IP)
def get_my_ip():
    try:
        # Получаем локальный IP
        local_ip = socket.gethostbyname(socket.gethostname())
        return local_ip
    except Exception as e:
        return f"An error occurred: {str(e)}"

# Функция отправки отелей пользователю
def send_hotels(user_id, hotels_data):
    # Проверяем, есть ли контекст для данного пользователя
    if user_id not in user_contexts_hotels:
        user_contexts_hotels[user_id] = {'current_hotel_index': 0}

    current_hotel_index = user_contexts_hotels[user_id]['current_hotel_index']



    # Список удобств для отелей (можно также будет добавить в фильтрацию)
    amenities_data = {148:'Отель только для взрослых',
                      4:'Телевизор в номере',
                      9:'Ресторан в отеле',
                      11:'Кондиционер в номере',
                      16:'Мини-бар в номере',
                      23:'Рум сервис 24 часа',
                      28:'Разрешено проживание с животными',
                      30:'Служба пробуждения',
                      35:'Гладильная доска',
                      47:'Факс в отеле',
                      54:'Бесплатная парковка',
                      59:'Оборудование для людей с ограниченными возможностями',
                      61:'Халаты',
                      66:'Холодильник',
                      73:'Теннисные корты',
                      78:'Доктор по вызову',
                      80:'Игровая площадка',
                      85:'Терраса для загара',
                      92:'Настольный теннис',
                      97:'Зона барбекю',
                      100:'Анимация',
                      105:'Ночной клуб',
                      112:'Верховая езда',
                      117:'Помещение для хранения лыж',
                      124:'Бесплатные местные телефонные звонки',
                      129:'Водные виды спорта',
                      131:'Wi-Fi на территории отеля',
                      136:'Персонал говорит на английском',
                      143:'Персонал говорит на русском',
                      5:'Телефон',
                      12:'Магазины на территории отеля',
                      24:'Доступ в интернет',
                      29:'Удобства для людей с ограниченными возможностями',
                      31:'Ежедневная газета',
                      36:'Сад на территории отеля',
                      43:'Ресепшн',
                      48:'Массаж',
                      50:'Ресепшн 24 часа',
                      62:'Показ фильмов в отеле',
                      67:'Детская кроватка',
                      74:'Медицинский персонал',
                      79:'Водные виды спорта (без мотора)',
                      81:'Библиотека',
                      86:'Бассейн с подогревом',
                      93:'Казино',
                      98:'Комната для игр',
                      101:'Бильярд',
                      106:'Приветственные напитки',
                      113:'Дайвинг',
                      118:'Сувенирный магазин',
                      120:'Доступ для оборудования людей с ограниченными возможностями',
                      125:'Комната для людей с ограниченными возможностями',
                      132:'Комната для курения',
                      137:'Персонал говорит на французском',
                      144:'Клининг сервис',
                      6:'Бизнес-центр',
                      13:'Прачечная',
                      18:'Радио',
                      20:'Конференц зал',
                      25:'Рум сервис',
                      32:'Сейф в номере',
                      37:'Бассейн на территории',
                      44:'Консьерж сервис',
                      49:'Трансфер',
                      51:'Голосовая почта',
                      56:'Парковка для автомобилей',
                      63:'Няня',
                      68:'Крытый бассейн',
                      70:'Поле для гольфа (в отеле)',
                      75:'Персонал говорит на нескольких языках',
                      82:'Оздоровительный комплекс',
                      87:'Бассейн для детей',
                      94:'Салон красоты',
                      99:'Видео / DVD плеер',
                      102:'Собственный пляж',
                      107:'-',
                      114:'Мини-маркет в отеле',
                      119:'Эко отель',
                      121:'Частная охрана',
                      126:'Камера для хранения багажа',
                      133:'Wi-Fi в номере',
                      138:'Персонал говорит на немецком',
                      140:'Персонал говорит на арабском',
                      145:'Депозит',
                      2:'Сушилка для рук',
                      7:'Душ в номере',
                      14:'Бар',
                      19:'Стол в номере',
                      21:'Лифт',
                      26:'Ванна',
                      33:'Балкон или терраса',
                      38:'Бассейн для плавания',
                      40:'Тренажерный зал или фитнес центр',
                      45:'Туры или экскурсии',
                      52:'Лобби',
                      57:'Джакузи',
                      64:'Банкетный зал',
                      69:'Обмен валют',
                      71:'Электронный ключ от номера',
                      76:'Пляжные зонтики',
                      83:'Wi-Fi на территории отеля',
                      88:'Завтрак с собой',
                      95:'Баня',
                      103:'Корты для сквоша',
                      108:'Водные виды спорта (моторизированные)',
                      110:'Тапочки в номере',
                      115:'Мини-гольф',
                      122:'Активности для детей',
                      127:'Сканер',
                      134:'Ежедневная уборка номеров',
                      139:'Персонал говорит на испанском',
                      141:'Персонал говорит на итальянском',
                      146:'Ванная в номере',
                      3:'Сейф в отеле',
                      10:'Раздельный душ и ванна',
                      15:'Сауна',
                      22:'Ванная комната',
                      27:'Кофе и чай',
                      41:'Кафе',
                      46:'Возможность проведения конференций',
                      53:'Мини-кухня',
                      58:'Аренда велосипедов',
                      60:'Микроволновка',
                      65:"Спа центр",
                      72:'Солярий',
                      77:'Комната для багажа',
                      84:'Раздевалка',
                      89:'Прачечная',
                      91:'Посудомоечная машина',
                      96:'Аренда автомобиля в отеле',
                      104:'Секретарь',
                      109:'Гараж',
                      111:'Услуги парковщика',
                      116:'Боулинг',
                      123:'Фильмы в отеле',
                      128:'Услуги носильщика',
                      130:'Стенд с турами',
                      135:'Объединенные номера',
                      142:'Персонал говорит на китайском',
                      147:'Объединенная ванная с туалетом',
                      0:'',
                      1:'',
                      8:'',
                      9:'',
                      17:''}


    # Проверяем, есть ли билет с таким индексом
    if current_hotel_index < len(hotels_data):
        hotel = hotels_data[current_hotel_index]

        # Позже добавить фильтрацию как в hotels_response_parse
        total_price = hotel['rooms'][0]['total']
        price_per_night = hotel['rooms'][0]['price']
        nights_amount = round(total_price / price_per_night)
        stars = hotel['stars']
        hotel_name = hotel['name']
        booking_url = hotel['rooms'][0]['fullBookingURL']
        hotel_id = hotel['id']
        hotel_address = hotel['address']
        distance = hotel['distance']
        rating = hotel['rating'] / 10
        amenities = hotel['amenities']

        # Замена ключей удобств на значения
        for i in range(len(amenities)):
            if amenities[i] in amenities_data:
                amenities[i] = amenities_data[i]

        amenities = [x for x in amenities if x != '']

        # Преобразование удобств в отеле
        for i in range(len(amenities)):
            if amenities[i] in amenities_data:
                print(amenities[i])
                amenities[i] = amenities_data[i]

        # Распаковка списка
        amenities = ', '.join(amenities)

        # Перевод расстояния от центра до отеля в метры и километры
        if distance < 1:
            metrage = 'м'
            distance *= 100
            distance = round(distance)
        else:
            metrage = 'км'

        # Позже нужно форматировать даты для выдачи (дат пока вообще нет)
        hotel_info = (f'<b>Название отеля:</b> {hotel_name} \n'
                      f'<b>Адрес:</b> {hotel_address} \n'
                      f'<b>Количество звезд:</b> {stars} \n'
                      f'<b>Расстояние от центра:</b> {distance} {metrage} \n'
                      f'<b>Цена за {nights_amount} ночей:</b> {total_price} \n'
                      f'<b>Рейтинг отеля:</b> {rating} \n'
                      f'<b>Удобства в отеле:</b> {amenities}')

        # Преобразование id отеля
        id = str(hotel_id)

        # Получение списка id фотографий
        url_for_photos = f'https://yasen.hotellook.com/photos/hotel_photos?id={id}'
        response_photos = requests.get(url_for_photos)
        photos_id = response_photos.json()[id]
        # photos_id.reverse()
        photos_id = photos_id[:1]

        # Отправка данных по отелю пользователю
        bot.send_message(user_id, hotel_info, parse_mode="html")

        # Получение фотографии и отправка ее пользователю
        id = str(id)

        for photo_id in photos_id:
            url_for_photos_2 = f'https://photo.hotellook.com/image_v2/limit/{photo_id}/1200/800.auto'
            response_photo = requests.get(url_for_photos_2)

            # Создание объекта файла в памяти
            photo_file = io.BytesIO(response_photo.content)
            bot.send_photo(chat_id=user_id, photo=photo_file)

        # Создаем и отправляем клавиатуру
        keyboard = telebot.types.InlineKeyboardMarkup()

        # Если это не последний билет, добавляем кнопку "Следующий билет"
        if current_hotel_index < len(hotels_data) - 1:
            hotels_amount = len(hotels_data)
            next_button = telebot.types.InlineKeyboardButton(text=f"Следующий отель ({current_hotel_index+1}/"
                                                                  f"{hotels_amount})", callback_data="next_hotel")
            keyboard.add(next_button)

        # Ссылку встраиваем в кнопку "Выбрать"
        callback_button = telebot.types.InlineKeyboardButton(text="Забронировать отель", url=booking_url)

        keyboard.add(callback_button)

        bot.send_message(user_id, 'Для бронирования отеля нажмите на кнопку "<b>Забронировать отель</b>"',
                         reply_markup=keyboard, parse_mode="html")

        # Обновляем контекст пользователя
        user_contexts_hotels[user_id]['current_hotel_index'] += 1


# Функция отправки билетов пользователю
def send_tickets(user_id, ticket_data):
    # Проверяем, есть ли контекст для данного пользователя
    if user_id not in user_contexts_tickets:
        user_contexts_tickets[user_id] = {'current_ticket_index': 0}

    current_ticket_index = user_contexts_tickets[user_id]['current_ticket_index']

    # Проверяем, есть ли билет с таким индексом
    if current_ticket_index < len(ticket_data['data']):
        ticket = ticket_data['data'][current_ticket_index]

        duration_to = ticket['duration_to']
        hours_to = duration_to // 60
        minutes_to = duration_to % 60

        duration_back = ticket['duration_back']
        hours_back = duration_back // 60
        minutes_back = duration_back % 60

        # Форматируем дату и время отправления и возвращения
        formatted_departure_date = format_date(ticket['departure_at'])
        formatted_return_date = format_date(ticket['return_at'])
        formatted_departure_time = format_time(ticket['departure_at'])
        formatted_return_time = format_time(ticket['return_at'])

        ticket_info = f"<b>Аэропорт вылета:</b> {ticket['origin_airport']}\n" \
                      f"<b>Аэропорт назначения:</b> {ticket['destination_airport']}\n" \
                      f"<b>Цена:</b> {ticket['price']} {ticket_data['currency']}\n" \
                      f"<b>Дата отправления:</b> {formatted_departure_date} в {formatted_departure_time}\n" \
                      f"<b>Дата возвращения:</b> {formatted_return_date} в {formatted_return_time}\n" \
                      f"<b>Длительность туда:</b> {hours_to} ч {minutes_to} мин\n" \
                      f"<b>Длительность обратно:</b> {hours_back} ч {minutes_back} мин\n" \
                      f"<b>Количество пересадок:</b> {ticket['transfers']}\n"

        # Отправляем информацию о билете
        bot.send_message(user_id, ticket_info, parse_mode="html")

        # Создаем и отправляем клавиатуру
        keyboard = telebot.types.InlineKeyboardMarkup()

        # Если это не последний билет, добавляем кнопку "Следующий билет"
        if current_ticket_index < len(ticket_data['data']) - 1:
            next_button = telebot.types.InlineKeyboardButton(text="Следующий билет",
                                                     callback_data="next_ticket")
            keyboard.add(next_button)

        # Ссылку встраиваем в кнопку "Выбрать"
        callback_button = telebot.types.InlineKeyboardButton(text="Купить билет",
                                                     url=f"https://aviasales.ru{ticket['link']}")
        keyboard.add(callback_button)

        bot.send_message(user_id, 'Для покупки билета нажмите на кнопку "<b>Купить билет</b>"',
                         reply_markup=keyboard, parse_mode="html")

        # Обновляем контекст пользователя
        user_contexts_tickets[user_id]['current_ticket_index'] += 1

def get_prices_for_dates_params(origin, destination, date, return_date):
    params = {
        "origin": origin,
        "destination": destination,
        "departure_at": date,
        "return_at": return_date,
        "unique": "false",
        "sorting": "price",
        "direct": "false",
        "cy": "rub",
        "limit": 30,
        "page": 1,
        "one_way": "false", # здесь можно будет построить логику one way or round trip
        "token": "13459216352443d80ea1e3e0f4331af0"
    }

    return params

def get_hotels_for_dates_params(destination_for_hotels, date_for_hotels, return_date_for_hotels, persons_for_hotels):
    customer_ip = '83.139.167.126'

    params_for_hotels = (f'13459216352443d80ea1e3e0f4331af0:404141:{persons_for_hotels}:{date_for_hotels}:'
                         f'{return_date_for_hotels}:0:0:{destination_for_hotels}:RUB:{customer_ip}:ru:0')

    return params_for_hotels

@bot.message_handler(func=lambda message: message.text == 'Поиск авиабилетов')
def avia_search(message):
    chat_id = message.chat.id
    user_tickets_data[chat_id] = {}
    questions = [
        'Введите <b>город вылета</b> (например, Москва):',
        'Введите <b>город прилета</b> (например, Стамбул):',
        'Введите <b>дату вылета туда</b> (в формате 22.11.2024):',
        'Введите <b>дату вылета обратно</b> (в формате 22.11.2024):'
    ]
    current_step = 0

    def get_user_input_tickets(message):
        nonlocal current_step

        if current_step in [0, 1]:
            autocomplete_result = autocomplete_city(message.text)

            if autocomplete_result:
                iata_code = autocomplete_result[0].get("code")
                user_tickets_data[chat_id][current_step] = iata_code
            else:
                bot.send_message(chat_id,
                                 'К сожалению, не удалось найти подходящий город. Пожалуйста, попробуйте снова, '
                                 '<b>нажав на "Начать поиск авиабилетов</b>.', parse_mode='html')
                return

        elif current_step == 2 or current_step == 3:  # Проверка на дату не ранее сегодняшней происходит всего один раз, нужно несколько проверок
            try:
                date_obj = datetime.strptime(message.text, '%d.%m.%Y').date()
                if date_obj < datetime.today().date():
                    bot.send_message(chat_id, 'Пожалуйста, введите дату не ранее сегодняшней. Начните поиск заново,'
                                              ' <b>нажав на "Начать поиск авиабилетов"</b>.', parse_mode='html')
                    return
                user_tickets_data[chat_id][current_step] = date_obj.strftime('%Y-%m-%d')
            except ValueError:
                bot.send_message(chat_id, 'Пожалуйста, введите дату в формате ДД.ММ.ГГГГ.  Начните поиск заново,'
                                              ' <b>нажав на "Начать поиск авиабилетов"</b>.', parse_mode='html')
                return

        else:
            user_tickets_data[chat_id][current_step] = message.text

        current_step += 1
        if current_step < len(questions):
            ask_question(chat_id, questions, current_step)
            bot.register_next_step_handler(message, get_user_input_tickets)
        else:
            bot.send_message(chat_id, 'Ищем для вас лучшие предложения. Пожалуйста, подождите...')
            print(user_tickets_data[chat_id])

            # Визуальное хранение данных для передачи в API запрос
            origin = user_tickets_data[chat_id][0]
            destination = user_tickets_data[chat_id][1]
            date = user_tickets_data[chat_id][2]
            return_date = user_tickets_data[chat_id][3]

            # Получаем параметры в json массиве для передачи в метод API
            params = get_prices_for_dates_params(origin, destination, date, return_date)

            # Метод для получения цен на билеты
            url = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"

            response = requests.get(url, params=params)

            if response.status_code == 200:
                user_tickets_data[chat_id]['ticket_data'] = response.json()
                send_tickets(user_id=chat_id, ticket_data=response.json())
            else:
                print('Произошла ошибка. Код:', response.status_code)
                print('Текст ошибки:', response.text)

                if response.status_code == 500:
                    bot.send_message(chat_id, 'Проблема с сервером API, пожалуйста, повторите попытку еще раз. '
                                              '(<b>Нажмите на кнопку "Поиск авиабилетов"</b>.', parse_mode='html')

                elif response.status_code == 400:
                    bot.send_message(chat_id, 'Разница между датой отправления и датой возвращения не должна '
                                              'составлять более 30 дней. Пожалуйста, повторите попытку '
                                              '(<b>Нажмите на кнопку "Поиск авиабилетов"</b>.', parse_mode='html')

    ask_question(chat_id, questions, current_step)
    bot.register_next_step_handler(message, get_user_input_tickets)


@bot.message_handler(func=lambda message: message.text == 'Поиск отелей')
def hotel_search(message):
    chat_id = message.chat.id
    user_hotels_data[chat_id] = {}
    questions = [
        'Введите <b>город проживания</b> (например, Стамбул):',
        'Введите <b>дату заселения</b> (в формате 22.11.2024):',
        'Введите <b>дату выселения</b> (в формате 22.11.2024):',
        'Введите <b>количество человек</b> (например, 2):'
    ]
    current_step = 0

    # Сбрасываем индекс отеля, чтобы при новом поиске отелей у индексация начиналась с первого
    if chat_id in user_contexts_hotels:
        user_contexts_hotels[chat_id]['current_hotel_index'] = 0

    def get_user_input_hotels(message):
        nonlocal current_step

        if current_step == 0:
            autocomplete_result = message.text
            print(autocomplete_result)
            url_city_id = (f'http://engine.hotellook.com/api/v2/lookup.json?'
                           f'query={autocomplete_result}&lang=ru'
                           f'&lookFor=city&limit=1&token=13459216352443d80ea1e3e0f4331af0')

            response_city_id = requests.get(url_city_id)
            if response_city_id.status_code == 200 and response_city_id.json()['results']['locations'] != []:
                city_id = response_city_id.json()['results']['locations'][0]['id']
            else:
                bot.send_message(chat_id, 'Произошла ошибка, попробуйте начать поиск снова')
                return None

            if autocomplete_result:
                user_hotels_data[chat_id][current_step] = city_id
            else:
                bot.send_message(chat_id,
                                 'К сожалению, не удалось найти подходящий город. Пожалуйста, '
                                 'начните поиск сначала, <b>нажав на "Поиск отелей"</b>.', parse_mode='html')
                return

        elif current_step in [1, 2]:  # Проверка на дату не ранее сегодняшней происходит всего один раз, нужно несколько проверок
            try:
                date_obj = datetime.strptime(message.text, '%d.%m.%Y').date()
                if date_obj < datetime.today().date():
                    bot.send_message(chat_id, 'Введена дата ранее сегодняшней. Пожалуйста, '
                                 'начните поиск сначала, нажав на "Поиск отелей"')
                    return
                user_hotels_data[chat_id][current_step] = date_obj.strftime('%Y-%m-%d')
            except ValueError:
                bot.send_message(chat_id, 'Пожалуйста, введите дату в формате ДД.ММ.ГГГГ. Начните поиск сначала, '
                                          '<b>нажав на "Поиск отелей"</b>.', parse_mode='html')
                return

        else:
            user_hotels_data[chat_id][current_step] = message.text

        current_step += 1
        if current_step < len(questions):
            ask_question(chat_id, questions, current_step)
            bot.register_next_step_handler(message, get_user_input_hotels)
        else:
            bot.send_message(chat_id, 'Ищем для вас лучшие предложения, время поиска может занять до минуты. '
                                      'Пожалуйста, подождите...')
            print(user_hotels_data[chat_id])

            # Визуальное хранение данных для передачи в API поиска отелей
            destination_for_hotels = user_hotels_data[chat_id][0]
            date_for_hotels = user_hotels_data[chat_id][1]
            return_date_for_hotels = user_hotels_data[chat_id][2]
            persons_for_hotels = user_hotels_data[chat_id][3]

            # Получаем параметры в json массиве для передачи в метод API
            params = get_hotels_for_dates_params(destination_for_hotels, date_for_hotels, return_date_for_hotels,
                                                 persons_for_hotels)

            signature = calculate_md5(params)
            customer_ip = '83.139.167.126'
            print(signature)

            url = (f'http://engine.hotellook.com/api/v2/search/start.json?cityId={destination_for_hotels}'
                   f'&checkIn={date_for_hotels}&checkOut={return_date_for_hotels}&'
                   f'adultsCount={persons_for_hotels}&customerIP={customer_ip}&childrenCount=0&childAge1=0&'
                   f'lang=ru&currency=RUB&waitForResult=0&marker=404141&signature={signature}')

            # Получение search_id
            response = requests.post(url)
            response_data = response.json()
            print(response_data)

            # Алгоритм получения самих данных об отелях в реальном времени
            search_id = response_data['searchId']
            limit = 10000
            rooms_count = 1
            sort_asc = 1
            sort_by = 'price'

            params_for_hotels = (f'13459216352443d80ea1e3e0f4331af0:404141:{limit}:0:{rooms_count}:{search_id}:'
                                 f'{sort_asc}:{sort_by}')

            signature_for_tickets = calculate_md5(params_for_hotels)
            print(signature_for_tickets)
            url_for_hotels = (f'http://engine.hotellook.com/api/v2/search/getResult.json?searchId={search_id}'
                              f'&limit={limit}&sortBy={sort_by}&sortAsc={sort_asc}&roomsCount={rooms_count}'
                              f'&offset=0&marker=404141&signature={signature_for_tickets}')

            while True:
                response_for_hotels = requests.post(url_for_hotels)
                if response_for_hotels.status_code == 200:
                    data_hotels = response_for_hotels.json()
                    print(len(data_hotels['result']))

                    hotels_data = []

                    # Параметры для фильтрации
                    # max_price = 200000 data_hotels['result'][i]['rooms'][0]['total']
                    min_stars = 3
                    distance = 5
                    min_rating = 75


                    for i in range(len(data_hotels['result'])):
                        if (data_hotels['result'][i]['stars'] >= min_stars
                                and data_hotels['result'][i]['distance'] < distance
                                and data_hotels['result'][i]['rating'] > min_rating):
                            hotels_data.append(data_hotels['result'][i])

                    user_hotels_data[chat_id]['hotels_data'] = hotels_data
                    send_hotels(user_id=chat_id, hotels_data=hotels_data)
                    print(len(hotels_data))

                    # Если отели не нашлись
                    if len(hotels_data) == 0:
                        bot.send_message(chat_id, 'К сожалению, не удалось найти варианты проживания по вашему '
                                                  'направлению. Пожалуйста, попробуйте снова, <b>нажав на '
                                                  '"Поиск отелей"</b>.', parse_mode='html')

                    break


    ask_question(chat_id, questions, current_step)
    bot.register_next_step_handler(message, get_user_input_hotels)


bot.infinity_polling(timeout=10, long_polling_timeout=5)
