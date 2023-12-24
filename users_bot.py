import telebot
from telebot import types
import io
import re
from conn_db import connect, close_db_connect

# Считываем токен из файла
with open("token.txt", "r") as file:
    token = file.read().strip()

bot = telebot.TeleBot(token)

# Исходная клавиатура
keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
button_courses = types.KeyboardButton('Курсы')
button_teachers = types.KeyboardButton('Преподаватели')
button_enroll = types.KeyboardButton('Запись на курс')
button_language = types.KeyboardButton('Смена языка')
button_review = types.KeyboardButton('Оставить отзыв')
keyboard.add(button_courses, button_teachers, button_enroll, button_language, button_review)

# Клавиатура без кнопок при активной операции
empty_keyboard = types.ReplyKeyboardRemove(selective=False)

# Словарь для хранения данных пользователя перед подачей заявки
user_data = {}
is_operation_active = False


# Функция для получения информации о преподавателях из БД
def get_teachers(offset=0, limit=5):
    connection = connect()
    cursor = connection.cursor()

    try:
        cursor.execute(
            f'SELECT * FROM "Teachers" LIMIT {limit} OFFSET {offset};'
        )
        teachers = cursor.fetchall()
        return teachers
    except Exception as e:
        print(f"Error: {e}")
    finally:
        close_db_connect(connection, cursor)


# Функция для получения информации о курсах из БД
def get_courses():
    connection = connect()
    cursor = connection.cursor()

    try:
        cursor.execute('SELECT * FROM "Courses";')
        courses = cursor.fetchall()
        return courses
    except Exception as e:
        print(f"Error: {e}")
    finally:
        close_db_connect(connection, cursor)


def get_available_places(course_id):
    connection = connect()
    cursor = connection.cursor()

    try:
        # Получите информацию о курсе из базы данных
        cursor.execute('SELECT available_places FROM "Courses" WHERE course_id = %s;', (course_id,))
        result = cursor.fetchone()

        if result:
            available_places = result[0]
            return available_places
        else:
            return None
    except Exception as e:
        print(f"Error: {e}")
    finally:
        close_db_connect(connection, cursor)


def get_enrolled_users_count(course_id):
    connection = connect()
    cursor = connection.cursor()

    try:
        # Получите количество записей в usercourses для указанного курса
        cursor.execute('SELECT COUNT(user_id) FROM "usercourses" WHERE course_id = %s;', (course_id,))
        result = cursor.fetchone()

        if result:
            enrolled_users_count = result[0]
            return enrolled_users_count
        else:
            return 0
    except Exception as e:
        print(f"Error: {e}")
    finally:
        close_db_connect(connection, cursor)


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Добро пожаловать! С помощью этого бота вы можете просматривать доступные курсы '
                                      'и преподавателей, а также оставлять заявки на определенный курс.',
                     reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.text == 'Смена языка')
def handle_language_change(message):
    bot.send_message(message.chat.id, 'В данный момент эта функция недоступна', reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.text == 'Преподаватели')
def handle_teachers(message):
    offset = 0
    show_next_teachers_button(message.chat.id, offset)


@bot.message_handler(func=lambda message: message.text == 'Курсы')
def handle_courses(message):
    user_chat_id = message.chat.id
    show_all_courses_button(user_chat_id)


@bot.message_handler(func=lambda message: message.text == 'Запись на курс')
def handle_enroll(message):
    user_chat_id = message.chat.id
    show_all_courses_for_enrollment(user_chat_id)


def show_all_courses_for_enrollment(chat_id):
    courses = get_courses()
    global is_operation_active
    is_operation_active = True
    if is_operation_active:
        bot.send_message(chat_id, 'Началось выполнение операции.', reply_markup=empty_keyboard)

    if courses:
        courses_text = '\n'.join([f'{index + 1}. {course[1]}' for index, course in enumerate(courses)])
        message_text = f'Выберите курс для подачи заявки:\n{courses_text}'

        keyboard_courses = types.InlineKeyboardMarkup()
        buttons = [types.InlineKeyboardButton(course[1], callback_data=f'enrollment_course_selection:{course[1]}') for
                   course in courses]
        keyboard_courses.add(*buttons)

        # Отправляем сообщение с выбором курса
        message = bot.send_message(chat_id, message_text, reply_markup=keyboard_courses)

        # Store the message ID in the user_data
        user_data['course_messages_for_enrollment'] = [message.message_id]
    else:
        bot.send_message(chat_id, 'Курсы закончились')


# Внесем изменения в обработчик callback_query для выбора курса при подаче заявки
@bot.callback_query_handler(func=lambda call: call.data.startswith('enrollment_course_selection:'))
def callback_enrollment_course_selection(call):
    course_name = call.data.split(':')[1]
    user_data['course'] = course_name

    # Получите course_id для выбранного курса
    course_id = get_course_id(course_name)

    # Получите количество свободных мест и количество уже записанных пользователей
    available_places = get_available_places(course_id)
    enrolled_users_count = get_enrolled_users_count(course_id)

    if available_places is not None and enrolled_users_count < available_places:
        bot.send_message(call.message.chat.id, f"Вы выбрали курс для подачи заявки: {course_name}")
        bot.send_message(call.message.chat.id, 'Введите ваше имя:')
        bot.register_next_step_handler(call.message, process_first_name)
        clear_previous_messages(call.message.chat.id)
    else:
        bot.send_message(call.message.chat.id, f"Извините, места на курсе {course_name} закончились.")


def clear_previous_messages(chat_id):
    # Получаем идентификаторы всех сообщений с курсами и "Выберите действие: Еще 5 курсов"
    course_messages = user_data.get('course_messages_for_enrollment', [])
    action_messages = user_data.get('action_messages_for_enrollment', [])

    # Удаляем все сообщения
    for message_id in course_messages + action_messages:
        bot.delete_message(chat_id, message_id)

    # Clear the lists in user_data
    user_data['course_messages_for_enrollment'] = []
    user_data['action_messages_for_enrollment'] = []


def process_first_name(message):
    user_data['first_name'] = message.text
    bot.send_message(message.chat.id, 'Введите вашу фамилию:')
    bot.register_next_step_handler(message, process_last_name)


def process_last_name(message):
    user_data['last_name'] = message.text
    bot.send_message(message.chat.id, 'Введите ваше отчество (если есть):')
    bot.register_next_step_handler(message, process_patronymic)


def process_patronymic(message):
    user_data['patronymic'] = message.text
    bot.send_message(message.chat.id, 'Введите ваш возраст (от 12 до 120 лет):')
    bot.register_next_step_handler(message, process_age)


def process_age(message):
    try:
        age = int(message.text)
        if 12 <= age <= 120:
            user_data['age'] = age
            bot.send_message(message.chat.id, 'Введите ваш номер телефона в формате 8(XXX)XXX-XX-XX:')
            bot.register_next_step_handler(message, process_phone_number)
        else:
            bot.send_message(message.chat.id, 'Пожалуйста, введите корректный возраст (от 12 до 120 лет):')
            bot.register_next_step_handler(message, process_age)
    except ValueError:
        bot.send_message(message.chat.id, 'Пожалуйста, введите число в качестве возраста:')
        bot.register_next_step_handler(message, process_age)


def process_phone_number(message):
    if validate_phone_number(message.text):
        user_data['phone_number'] = message.text
        submit_enrollment(message.chat.id)
    else:
        bot.send_message(message.chat.id, 'Неверный формат номера телефона. Попробуйте еще раз.')
        bot.send_message(message.chat.id, 'Введите ваш номер телефона в формате 8(XXX)XXX-XX-XX:')
        bot.register_next_step_handler(message, process_phone_number)


def validate_phone_number(phone_number):
    pattern = re.compile(r'^8\(\d{3}\)\d{3}-\d{2}-\d{2}$')
    return pattern.match(phone_number) is not None


def submit_enrollment(chat_id):
    global is_operation_active
    is_operation_active = False
    connection = connect()
    cursor = connection.cursor()

    try:
        # Получите chat_id из сообщения пользователя
        user_chat_id = chat_id

        # Вставьте данные заявки в базу данных, включая chat_id
        cursor.execute(
            'INSERT INTO "Requests" (first_name, second_name, patronymic, age, phone_number, course_id) VALUES (%s, '
            '%s, %s, %s, %s, %s) RETURNING request_id;',
            (user_data['first_name'], user_data['last_name'], user_data['patronymic'], user_data['age'],
             user_data['phone_number'], get_course_id(user_data['course']))
        )
        request_id = cursor.fetchone()[0]
        connection.commit()

        # Отправьте сообщение о подаче заявки
        bot.send_message(chat_id, 'Заявка успешно подана!', reply_markup=keyboard)

        # Вызовите функцию для создания договора и его отправки
        send_contract_loop(user_chat_id, request_id)

    except Exception as e:
        print(f"Error: {e}")
        bot.send_message(user_chat_id, "Произошла ошибка при подаче заявки. Попробуйте позже.")
    finally:
        close_db_connect(connection, cursor)


def send_contract_loop(chat_id, request_id):
    while not send_contract(chat_id, request_id):
        # Если отправка не удалась, попробуйте снова, пока не будет успешной
        pass


def send_contract(chat_id, request_id):
    connection = connect()
    cursor = connection.cursor()

    try:
        # Получите информацию о договоре по request_id из базы данных
        cursor.execute('SELECT contract_file FROM "Contracts" WHERE request_id = %s;', (request_id,))
        result = cursor.fetchone()

        if result and result[0]:
            # Отправьте договор пользователю
            contract_bytes = bytes(result[0])  # Получаем байты из bytea
            contract_file = io.BytesIO(contract_bytes)
            contract_file.name = 'contract.docx'  # Имя файла

            # Создаем Inline-кнопки
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            sign_button = types.InlineKeyboardButton('Подписать.', callback_data=f'sign:{request_id}')
            decline_button = types.InlineKeyboardButton("Отказаться", callback_data=f'decline:{request_id}')
            keyboard.add(sign_button, decline_button)

            # Отправляем документ с кнопками
            message = bot.send_document(chat_id, contract_file, reply_markup=keyboard,
                                        caption="Пожалуйста, подпишите документ:")

            # Записываем в словарь данные о последнем отправленном сообщении с договором
            user_data['last_contract_message'] = message.message_id
            return True  # Успешная отправка договора
        else:
            # bot.send_message(chat_id, "Договор не найден.")
            return False  # Договор не найден

    except Exception as e:
        print(f"Error: {e}")
        # bot.send_message(chat_id, "Произошла ошибка при отправке договора.")
        return False  # Ошибка при отправке договора
    finally:
        close_db_connect(connection, cursor)


@bot.callback_query_handler(func=lambda call: call.data.startswith('sign:'))
def callback_sign(call):
    request_id = call.data.split(':')[1]
    sign_contract(call.message.chat.id, request_id)
    hide_buttons_after_action(call.message.chat.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('decline:'))
def callback_decline(call):
    request_id = call.data.split(':')[1]
    decline_contract(call.message.chat.id, request_id)
    hide_buttons_after_action(call.message.chat.id)


def hide_buttons_after_action(chat_id):
    # Получаем идентификаторы последнего сообщения с договором
    last_contract_message_id = user_data.get('last_contract_message')

    # Удаляем кнопки из сообщения
    if last_contract_message_id:
        bot.edit_message_reply_markup(chat_id, last_contract_message_id, reply_markup=None)


def sign_contract(chat_id, request_id):
    connection = connect()
    cursor = connection.cursor()

    try:
        # Копируем данные из Requests в Users
        cursor.execute(
            'INSERT INTO "Users" (first_name, second_name, age, patronymic, phone_number) '
            'SELECT first_name, second_name, age, patronymic, phone_number FROM "Requests" WHERE request_id = %s '
            'RETURNING user_id;', (request_id,)
        )
        user_id = cursor.fetchone()[0]

        # Обновляем signed в Contracts
        cursor.execute('UPDATE "Contracts" SET signed = TRUE, user_id = %s WHERE request_id = %s RETURNING user_id;',
                       (user_id, request_id))

        # Заносим данные о курсе в usercourses
        cursor.execute('INSERT INTO "usercourses" (user_id, course_id) SELECT %s, course_id FROM "Requests" WHERE '
                       'request_id = %s;', (user_id, request_id))

        connection.commit()

        bot.send_message(chat_id, "Договор успешно подписан.")
    except Exception as e:
        print(f"Error: {e}")
        bot.send_message(chat_id, "Произошла ошибка при подписании договора.")
    finally:
        close_db_connect(connection, cursor)


def decline_contract(chat_id, request_id):
    connection = connect()
    cursor = connection.cursor()

    try:
        # Удаляем контракт
        cursor.execute('DELETE FROM "Contracts" WHERE request_id = %s;', (request_id,))

        connection.commit()

        bot.send_message(chat_id, "Договор отклонен.")
    except Exception as e:
        print(f"Error: {e}")
        bot.send_message(chat_id, "Произошла ошибка при отказе от договора.")
    finally:
        close_db_connect(connection, cursor)


def get_course_id(course_name):
    connection = connect()
    cursor = connection.cursor()

    try:
        cursor.execute('SELECT course_id FROM "Courses" WHERE name_course = %s;', (course_name,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        close_db_connect(connection, cursor)


@bot.callback_query_handler(func=lambda call: call.data == 'next_teachers')
def callback_next_teachers(call):
    offset = int(call.message.text.split(':')[-1])
    show_next_teachers_button(call.message.chat.id, offset)


def show_next_teachers_button(chat_id, offset):
    teachers = get_teachers(offset=offset)

    if teachers:
        for teacher in teachers:
            teacher_info = f"Преподаватель: {teacher[1]} {teacher[2]} {teacher[3]}\nОбразование: {teacher[4]}\n" \
                           f"Специальность: {teacher[5]}\nСтаж: {teacher[6]}"
            bot.send_message(chat_id, teacher_info)

        if len(teachers) == 5:
            # Показываем кнопку "Следующие 5 преподавателей", если есть еще записи
            button_next_teachers = types.InlineKeyboardButton('Следующие 5 преподавателей',
                                                              callback_data='next_teachers')
            keyboard_next_teachers = types.InlineKeyboardMarkup().add(button_next_teachers)

            # Увеличиваем смещение только если есть еще преподаватели
            offset += 5
            bot.send_message(chat_id, f"Выберите действие: {offset}", reply_markup=keyboard_next_teachers)
        else:
            bot.send_message(chat_id, "Преподаватели закончились")
    else:
        bot.send_message(chat_id, "Преподаватели закончились")


# Update the show_next_courses_button function
def show_all_courses_button(chat_id):
    courses = get_courses()

    if courses:
        courses_text = "\n\n".join(
            [
                f"Курс: {course[1]}\nОписание: {course[2]}\nДоступные места: {course[3]}\nПреподаватель: {get_teacher_name(course[4])}"
                for course in courses]
        )
        message_text = f"Информация о курсах:\n{courses_text}"

        message = bot.send_message(chat_id, message_text, reply_markup=keyboard)

        # Store the message ID in the user_data
        user_data['course_messages_for_enrollment'] = [message.message_id]
    else:
        bot.send_message(chat_id, 'Курсы закончились')


def get_teacher_name(teacher_id):
    connection = connect()
    cursor = connection.cursor()

    try:
        cursor.execute('SELECT first_name, second_name FROM "Teachers" WHERE teacher_id = %s;', (teacher_id,))
        result = cursor.fetchone()
        if result:
            return f"{result[0]} {result[1]}"
        else:
            return "Неизвестно"
    except Exception as e:
        print(f"Error: {e}")
        return "Неизвестно"
    finally:
        close_db_connect(connection, cursor)


@bot.message_handler(func=lambda message: message.text == 'Оставить отзыв')
def handle_review(message):
    global is_operation_active
    if is_operation_active:
        bot.send_message(message.chat.id, 'Началось выполнение операции.', reply_markup=empty_keyboard)
    else:
        user_chat_id = message.chat.id
        show_all_courses_for_review(user_chat_id)


def show_all_courses_for_review(chat_id):
    courses = get_courses()
    global is_operation_active
    is_operation_active = True
    if is_operation_active:
        bot.send_message(chat_id, 'Началось выполнение операции.', reply_markup=empty_keyboard)

    if courses:
        buttons = [
            types.InlineKeyboardButton(f"{course[1]}", callback_data=f'review_course_selection:{course[1]}')
            for course in courses
        ]
        keyboard_courses = types.InlineKeyboardMarkup(row_width=2).add(*buttons)
        message_text = "Выберите курс для оставления отзыва:"
        message = bot.send_message(chat_id, message_text, reply_markup=keyboard_courses)

        user_data['last_courses_message_for_review'] = message.message_id
    else:
        bot.send_message(chat_id, "Курсы закончились")


# Внесем изменения в обработчик callback_query для кнопки "Отзыв" при выборе курса
@bot.callback_query_handler(func=lambda call: call.data.startswith('review_course_selection:'))
def callback_review_course_selection(call):
    course_name = call.data.split(':')[1]
    user_data['course'] = course_name
    bot.send_message(call.message.chat.id, f"Вы выбрали курс: {course_name}")
    bot.send_message(call.message.chat.id, "Оставьте отзыв:")
    bot.register_next_step_handler(call.message, process_review_text)
    clear_previous_messages(call.message.chat.id)


def process_review_text(message):
    user_data['review_text'] = message.text
    bot.send_message(message.chat.id, "Введите вашу оценку от 1 до 5:")
    bot.register_next_step_handler(message, process_rating)


def process_rating(message):
    try:
        rating = int(message.text)
        if 1 <= rating <= 5:
            user_data['rating'] = rating
            submit_review(message.chat.id, user_data['review_text'], user_data['rating'])
        else:
            bot.send_message(message.chat.id, "Оценка должна быть от 1 до 5. Попробуйте еще раз.")
            bot.send_message(message.chat.id, "Введите вашу оценку от 1 до 5:")
            bot.register_next_step_handler(message, process_rating)
    except ValueError:
        bot.send_message(message.chat.id, "Введите число от 1 до 5. Попробуйте еще раз.")
        bot.send_message(message.chat.id, "Введите вашу оценку от 1 до 5:")
        bot.register_next_step_handler(message, process_rating)


def submit_review(chat_id, review_text, rating):
    global is_operation_active
    is_operation_active = False
    connection = connect()
    cursor = connection.cursor()

    try:
        # Получите course_id из user_data
        course_id = get_course_id(user_data['course'])

        # Вставьте данные отзыва в базу данных
        cursor.execute(
            'INSERT INTO "Review" (review_text, rating, course_id) VALUES (%s, %s, %s) RETURNING review_id;',
            (review_text, rating, course_id)
        )
        review_id = cursor.fetchone()[0]
        connection.commit()

        bot.send_message(chat_id, "Отзыв успешно добавлен!", reply_markup=keyboard)

    except Exception as e:
        print(f"Error: {e}")
        bot.send_message(chat_id, "Произошла ошибка при добавлении отзыва. Попробуйте позже.")
    finally:
        close_db_connect(connection, cursor)


bot.polling()
