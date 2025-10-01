from multiprocessing import Process
from bot import run_bot

def start_bot():
    run_bot()

if __name__ == "__main__":
    p = Process(target=start_bot)
    p.start()
    p.join()