from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, MenuButton, MenuButtonCommands
from dotenv import load_dotenv
import os
import shutil
from TerraYolo.TerraYolo import TerraYoloV5             # загружаем фреймворк TerraYolo

# возьмем переменные окружения из .env
load_dotenv()

# загружаем токен бота
TOKEN =  os.environ.get("TOKEN") # ВАЖНО !!!!!

# инициализируем класс YOLO
WORK_DIR = './yolo'
os.makedirs(WORK_DIR, exist_ok=True)
yolov5 = TerraYoloV5(work_dir=WORK_DIR)

# функция команды /start
async def start(update, context):
    keyboard = [
        [
            InlineKeyboardButton("Люди", callback_data="люди"),

            InlineKeyboardButton("Животные", callback_data="животные"),
        ],
        [
            InlineKeyboardButton("Еда и кухня", callback_data="еда"),
            InlineKeyboardButton("Транспорт", callback_data="транспорт")
        ],
        [InlineKeyboardButton("Всё подряд", callback_data="всё подряд")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Пожалуйста, выберите, что будем распознавать:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""

    query = update.callback_query
    context.user_data['user_choice'] = query.data
    await query.answer()
    await query.edit_message_text(text="А теперь пришлите фото для распознавания объектов")
    # await query.edit_message_text(text=f"Вы выбрали для распознования: {query.data}") 

# функция для работы с текстом
async def help(update, context):
    await update.message.reply_text(update)

async def attachment(update, context):
    # получаем файл изображения из сообщения
    file = update.message.document

    if file.mime_type.split('/')[0] == 'image':
        await update.message.reply_text('Привет! Мы получили фото от тебя!')
    else:
        await update.message.reply_text('Привет! Мы получили от тебя файл, а не фото. Пришли фото!')
    
    # # проверяем размер файла
    if file.file_size > 1024 * 1024:
        await update.message.reply_text('Изображение слишком большое. Пожалуйста, отправьте сжатую версию.')
    else:
        await update.message.reply_text('Пожалуйста, отправьте сжатую версию.')

# функция обработки изображения
async def detection(update, context, od_type=None):
    # удаляем папку images с предыдущим загруженным изображением и папку runs с результатом предыдущего распознавания
    try:
        shutil.rmtree('images') 
        shutil.rmtree(f'{WORK_DIR}/yolov5/runs') 
    except:
        pass

    my_message = await update.message.reply_text('Мы получили от тебя фотографию. Идет распознавание объектов...')
    # получение файла из сообщения
    new_file = await update.message.photo[-1].get_file()
    
    # имя файла на сервере
    os.makedirs('images', exist_ok=True)
    image_name = str(new_file['file_path']).split("/")[-1]
    image_path = os.path.join('images', image_name)
    # скачиваем файл с сервера Telegram в папку images
    await new_file.download_to_drive(image_path)
    
    user_choice = context.user_data.get('user_choice')

    # создаем словарь с параметрами
    test_dict = dict()
    test_dict['weights'] = 'yolov5m.pt'     # Самые сильные веса yolov5x.pt, вы также можете загрузить версии: yolov5n.pt, yolov5s.pt, yolov5m.pt, yolov5l.pt (в порядке возрастания)
    test_dict['source'] = 'images'          # папка, в которую загружаются присланные в бота изображения

    # test_dict['conf'] = 0.99           # порог распознавания [0.01, 0.5, 0.99]
    # test_dict['iou'] = 0.99            # порог NMS [0.01, 0.5, 0.99]
    # test_dict['classes'] = '39 46 47 49'        # классы, которые будут распознаны

    if user_choice == 'люди':
        test_dict['classes'] = '0'
    elif user_choice == 'животные':
        test_dict['classes'] = '14 15 16 17 18 19 20 21 22 23'
    elif user_choice == 'еда':
        test_dict['classes'] = '39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55'
    elif user_choice == 'транспорт':
        test_dict['classes'] = '1 2 3 4 5 6 7 8 9 10 11 12'

    _iou = 'iou =' + str(test_dict['iou']) if 'iou' in test_dict.keys() else 'iou = None'
    _conf = 'conf =' + str(test_dict['conf']) if 'conf' in test_dict.keys() else 'conf = None'
    _classes = f'classes = {user_choice}' if 'classes' in test_dict.keys() else 'classes = None'
    _options = ", ".join([_conf, _iou, _classes])
    
    # вызов функции detect из класса TerraYolo)
    yolov5.run(test_dict, exp_type='test') 

    # удаляем предыдущее сообщение от бота
    await context.bot.deleteMessage(message_id = my_message.message_id, # если не указать message_id, то удаляется последнее сообщение
                                    chat_id = update.message.chat_id) # если не указать chat_id, то удаляется последнее сообщение

    # отправляем пользователю результат
    await update.message.reply_text(f'Распознавание объектов завершено. [Опции: {_options}]') # отправляем пользователю результат 
    await update.message.reply_photo(f"{WORK_DIR}/yolov5/runs/detect/exp/{image_name}") # отправляем пользователю результат изображение



def main():

    # точка входа в приложение
    application = Application.builder().token(TOKEN).build() # создаем объект класса Application
    print('Бот запущен...')
    
    # добавляем обработчик команды /start
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("attachment", attachment))

    # добавляем обработчик изображений, которые загружаются в Telegram в СЖАТОМ формате
    # (выбирается при попытке прикрепления изображения к сообщению)
    application.add_handler(MessageHandler(filters.PHOTO, detection, block=False))
    application.add_handler(MessageHandler(filters.TEXT, help))
    application.add_handler(MessageHandler(filters.ATTACHMENT, attachment))

    application.run_polling(allowed_updates=Update.ALL_TYPES) # запускаем бота (остановка CTRL + C)

if __name__ == "__main__":
    main()
