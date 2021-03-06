import requests as r
from fastapi import Response, BackgroundTasks

import config
import container
from extras import try_request, check_qna_answer, transform_to_permalinks_or_text


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
    return data.get("type", "") == "view_submission" and \
           data.get("view", {}).get("callback_id", "") == "qna_submission"


async def qna_interaction(data: dict):
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

    answer = try_request(container.logger, r.get, config.QNA_REQUEST_URL, params=params)
    if answer.is_err():
        await container.slacker.post_to_channel(
            channel_id=user_id,
            text="Received error during interaction with Q&A app. Please, try later or contact with ODS.ai Q&A team."
        )
        return

    answer = answer.unwrap().json()
    container.logger.debug(f"ODS Q&A answer: {answer}")

    # check that returned result is a list of strings
    answer = check_qna_answer(answer)
    if answer.is_err():
        await container.slacker.post_to_channel(
            channel_id=user_id,
            text="Received incorrect payload from ODS.ai Q&A application. Our team is already working on it."
        )
        return
    answer = answer.unwrap()

    # for each message get either preview or message text and then construct a final message
    blocks = await transform_to_permalinks_or_text(answer)
    template = container.jinja_env.get_template("qna_answer.json")
    blocks = template.render(query=query, answers=blocks)

    await container.slacker.post_to_channel(channel_id=user_id, blocks=blocks)


async def validate_qna_modal(tasks: BackgroundTasks, body: dict) -> Response:
    if body.get('qna_query', {}).get('query', {}).get('value', None) == '':
        return Response(
            status_code=400,
            content={"response_action": "errors", "errors": {"qna_query": "Empty input is not allowed."}}
        )

    tasks.add_task(qna_interaction, body)
    return Response(status_code=200)
