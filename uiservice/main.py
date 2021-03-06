import json
import os
import urllib.parse

import uvicorn
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Depends, Body, Response
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from jinja2 import Environment, PackageLoader

import config
from common.LoggerFactory import create_logger
from common.Slacker import Slacker
from routers import request_parser, top, timer, preset, internal, qna
import extras
import container

app = FastAPI()
app.include_router(internal.router, prefix="/internal", tags=['internal'])

container.logger = create_logger("UI", level=config.LOG_LEVEL)


@app.post("/events", dependencies=[Depends(extras.verify_origin)])
async def events(tasks: BackgroundTasks, data: dict = Body(...)):
    # Slack auth check
    if extras.check_url_verification(data):
        return extras.process_url_verification(data)

    # check if it is callback of message
    if not extras.check_message_callback(data):
        container.logger.error(f"Unknown payload: {data}")
        raise HTTPException(status_code=501, detail="Currently only callbacks of messages are processed.",
                            headers={'X-Slack-No-Retry': '1'})

    data = data.get('event', {})
    if data.get("type", "") == "message" and data.get("subtype", "") in {"message_deleted", "message_changed"}:
        return

    is_im = (data.get("channel_type", "") == "im")
    # check if it is in private channel
    if config.PM_ONLY and not is_im:
        return  # processed: do nothing

    # do not answer to own messages
    username = data.get("user", "") or data.get("username", "")
    if username == config.BOT_NAME:
        return

    # answer only on direct messages and mentions in chats
    if container.slacker.user_id not in data.get('text', "") and not is_im:
        return

    # parse message and answer
    tasks.add_task(request_parser.process_message, data)
    return


@app.post("/interactivity", dependencies=[Depends(extras.verify_origin)])
async def interactivity(tasks: BackgroundTasks, payload: Request):
    body = (await payload.body()).decode("utf-8")
    body = body[8:]  # remove 'payload='
    body = json.loads(urllib.parse.unquote(body))

    if await request_parser.request_picker_eligibility(body):
        command_text = body.get('actions', [{}])[0].get('value')

        tasks.add_task(request_parser.process_message, {
            'text': command_text,
            'user': body.get('user', {}).get('id', ''),
            'channel': body.get('channel', {}).get('id', ''),
            'trigger_id': body.get('trigger_id', '')
        })
        return
    elif await top.top_interaction_eligibility(body):
        tasks.add_task(top.top_interaction, body)
        return
    elif await timer.timer_interaction_eligibility(body):
        tasks.add_task(timer.timer_interaction, body)
        return
    elif await preset.preset_interaction_eligibility(body):
        tasks.add_task(preset.preset_interaction, body)
        return Response(status_code=200)    # for modal views response should be ABSOLUTELY empty
    elif await qna.qna_interaction_eligibility(body):
        return await qna.validate_qna_modal(tasks, body)
    return


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, exc):
    container.logger.exception(exc)
    return await http_exception_handler(request, exc)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    container.logger.exception(exc)
    return await request_validation_exception_handler(request, exc)


@app.on_event("startup")
async def startup():
    container.slacker = Slacker(
        user_token=config.SLACK_USER_TOKEN,
        bot_token=config.SLACK_BOT_TOKEN,
        logger=container.logger,
        async_init=True
    )
    await container.slacker.__ainit__(bot_token=config.SLACK_BOT_TOKEN)

    container.jinja_env = Environment(
        loader=PackageLoader(os.path.basename(os.path.dirname(__file__)), 'resources'),
        autoescape=False
    )


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
