from fastapi import FastAPI, BackgroundTasks, Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

import threading


from pydantic import BaseModel

from job_bot import JobBot as Bot
import bot_config as config
from job_data import load_job_count


app = FastAPI()

bot = None
bot_thread = None

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')


class Token(BaseModel):
    access_token: str
    token_type: str


def authenticate_user(username: str, password: str):
    if username == config.USERNAME and password == config.PASSWORD:
        return True
    return False


@app.post('/token', response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if authenticate_user(form_data.username, form_data.password):
        return {'access_token': form_data.username, 'token_type': 'bearer'}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')


@app.post('/start_bot/')
def start_bot(background_tasks: BackgroundTasks, token: str = Depends(oauth2_scheme)):
    global bot, bot_thread
    if bot_thread and bot_thread.is_alive():
        raise HTTPException(status_code=400, detail='Bot already running')
    bot = Bot(config.__dict__)
    bot_thread = threading.Thread(target=bot.run)
    bot_thread.start()
    background_tasks.add_task(bot_thread.join)
    return JSONResponse(status_code=200, content={'message': 'Bot started'})


@app.post('/stop_bot/')
def stop_bot(token: str = Depends(oauth2_scheme)):
    global bot_thread
    if not bot_thread or not bot_thread.is_alive():
        return JSONResponse(status_code=200, content={'message': 'Bot not running, nothing to stop'})

    bot.stop()
    bot_thread.join()
    return JSONResponse(status_code=200, content={'message': 'Bot stopped'})


@app.get('/status/')
def get_status(token: str = Depends(oauth2_scheme)):
    job_count = load_job_count(config.JOB_COUNT_FILE)
    if bot_thread and bot_thread.is_alive():
        status = 'Running'
    else:
        status = 'Stopped'
    return JSONResponse(status_code=200, content={'status': status, 'job_count': job_count})


if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app:app", host='0.0.0.0', port=8001, reload=True)
