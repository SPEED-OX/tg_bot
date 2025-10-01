import multiprocessing
import uvicorn
from bot import run_bot
from webapp import app

def start_bot():
    run_bot()

def start_web():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    p1 = multiprocessing.Process(target=start_bot)
    p2 = multiprocessing.Process(target=start_web)
    p1.start()
    p2.start()
    p1.join()
    p2.join()