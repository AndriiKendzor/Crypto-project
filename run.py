from multiprocessing import Process, Queue
from main import run_parser
from bot import run_bot

if __name__ == "__main__":
    queue = Queue()

    # Запуск парсера
    parser_process = Process(target=run_parser, args=(queue,))
    parser_process.start()

    # Запуск бота
    bot_process = Process(target=run_bot, args=(queue,))
    bot_process.start()

    parser_process.join()
    bot_process.join()
