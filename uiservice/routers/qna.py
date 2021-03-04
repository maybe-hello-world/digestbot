import requests as r

import config
import container
from extras import try_request


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

    params = {'q': query}
    if model != "default":
        params['model'] = model

    answer = try_request(container.logger, r.get, config.QNA_REQUEST_URL, params=params)
    if answer.is_err():
        await container.slacker.post_to_channel(
            channel_id=user_id,
            text="Received error during interaction with Q&A app. Please, try later or contact with ODS.ai Q&A team."
        )
        return

    answer = answer.unwrap().json()

    # check that returned result is a list of strings
    if isinstance(answer, list) and all(isinstance(x, str) for x in answer):
        answer = '\n'.join(answer)
    else:
        container.logger.error("Received incorrect payload from ODS.ai Q&A application.\n\n\n" + str(answer.text))
        answer = 'Received incorrect payload from ODS.ai Q&A application. Our team is already working on it.'
    await container.slacker.post_to_channel(channel_id=user_id, text=answer)


