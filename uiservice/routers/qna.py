from datetime import datetime, timedelta

import requests as r
from fastapi import Response, BackgroundTasks
from influxdb_client import Point
from result import Result

import config
import container
from config import INFLUX_API_WRITE
from extras import try_request, check_qna_answer, transform_to_permalinks_or_text

QNA_ERROR = "Received error during interaction with Q&A app. Please, try later or contact with ODS.ai Q&A team."
QNA_INCORRECT_PAYLOAD = "Received incorrect payload from ODS.ai Q&A application. Our team is already working on it."


async def send_initial_message(user_id: str, channel_id: str, trigger_id: str):
    if not trigger_id:
        template = container.jinja_env.get_template("qna_button.json")
        result = template.render()
        await container.slacker.post_to_channel(channel_id=channel_id, blocks=result, ephemeral=True, user_id=user_id)
        return

    template = container.jinja_env.get_template("qna.json")
    result = template.render()
    await container.slacker.open_view(trigger_id=trigger_id, view=result)


async def qna_interaction_eligibility(data: dict):
    return (data.get("type", "") == "view_submission" and
            data.get("view", {}).get("callback_id", "") == "qna_submission") \
           or \
           (data.get("type", "") == "block_actions" and
            data.get("actions", [{}])[0].get("action_id", "") == "qna_fastpath")


async def qna_interaction(data: dict):
    user_id = data.get('user', {}).get('id', '')

    if data.get("type") == "view_submission":
        params = await qna_interaction_modal(data)
    else:
        params = await qna_interaction_fastpath(data)
        if params.is_err():
            await container.slacker.post_to_channel(channel_id=user_id, text=params.unwrap_err())
            return
        else:
            params = params.unwrap()

    answer = try_request(container.logger, r.get, config.QNA_REQUEST_URL, params=params)
    if answer.is_err():
        await container.slacker.post_to_channel(channel_id=user_id, text=QNA_ERROR)
        return

    answer = answer.unwrap().json()
    container.logger.debug(f"ODS Q&A answer: {answer}")

    # check that returned result is a list of strings
    answer = check_qna_answer(answer)
    if answer.is_err():
        await container.slacker.post_to_channel(channel_id=user_id, text=QNA_INCORRECT_PAYLOAD)
        return
    answer = answer.unwrap()

    # collect metric
    INFLUX_API_WRITE(Point("digestbot").field("qna_request", 1).time(datetime.utcnow()))

    # for each message get either preview or message text and then construct a final message
    blocks = await transform_to_permalinks_or_text(answer)
    template = container.jinja_env.get_template("qna_answer.json")
    blocks = template.render(query=params['query'], answers=blocks)

    await container.slacker.post_to_channel(channel_id=user_id, blocks=blocks)


async def qna_interaction_modal(data: dict) -> dict:
    user_id = data.get('user', {}).get('id', '')
    data = data.get("view", {}).get("state", {}).get("values", {})

    query = data.get('qna_query', {}).get('query', {}).get('value', '')
    model = data.get('model', {}).get('model_selection', {}).get('selected_option', {}).get('value', '')

    user_id_agreement = (
        data
            .get('uid_agreement', {})
            .get('uid_switch', {})
            .get('selected_option', {})
            .get('value', 'user_id_no')
    )

    params = {'query': query}
    if model != "default":
        params['model'] = model
    if user_id_agreement == "user_id_yes":
        params['user_id'] = user_id

    return params


async def qna_interaction_fastpath(data: dict) -> Result[dict, str]:
    channel_id = data.get("channel", {}).get("id", "")
    user_id = data.get('user', {}).get('id', '')

    # receive all messages for last 5 minutes and find last from the user
    message = await container.slacker.get_im_latest_user_message_text(
        channel_id=channel_id, oldest=datetime.now() - timedelta(minutes=5), user_id=user_id
    )

    if not message:
        return Result.Err("Didn't find your message. Is it more than 5 minutes old?")
    return Result.Ok({"query": message})


async def validate_qna_modal(tasks: BackgroundTasks, body: dict) -> Response:
    if body.get('qna_query', {}).get('query', {}).get('value', None) == '':
        return Response(
            status_code=400,
            content={"response_action": "errors", "errors": {"qna_query": "Empty input is not allowed."}}
        )

    tasks.add_task(qna_interaction, body)
    return Response(status_code=200)
