import asyncio
from datetime import datetime

from pywui import command, PyWuiApp, PyWuiWindow, listener, with_window


@with_window
@listener("message")
async def on_message(window: PyWuiWindow, message: str):
    print("Message received: {}".format(message))


@with_window
@command()
async def greet(window: PyWuiWindow):
    # window.toggle_fullscreen()
    window.emit("message", "Hello from python")
    return "Hello World!"


async def on_start(window: PyWuiWindow):
    async def send_time():
        while True:
            window.emit("time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            await asyncio.sleep(1)

    await asyncio.create_task(send_time())


app = PyWuiApp()
main_window = app.get_window('main')
app.run(func=on_start, args=[main_window], debug=True)
