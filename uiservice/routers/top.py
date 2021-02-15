from datetime import datetime
import requests as r

import config
from extras import log_erroneous_answer, try_parse_int
import container


async def send_initial_message(user_id: str, channel_id: str) -> None:
    # get current date
    today = datetime.today().strftime("%Y-%m-%d")

    # get presets available for the user
    # answer = r.get(
    #     f"http://{config.DB_URL}/category/",
    #     params={'user_id': user_id, 'include_global': "true"},
    #     timeout=10
    # )
    # if answer.status_code != 200:
    #     log_erroneous_answer(answer)
    #     # TODO: sent answer.text to the user
    #     return
    #
    # presets_list = answer.json()
    presets_list = [{"name": "test1"}, {"name": "test2"}]
    sources = [('All', 'all')]
    sources.extend((y := x.get("name", "<ERROR>"), y.lower()) for x in presets_list)

    # extend them with current existing channels
    channels = await container.slacker.get_channels_list()
    sources.extend((y, x) for x, y in channels)

    # create answer for top command from the template
    template = container.jinja_env.get_template("top.json.j2")
    result = template.render(today=today, sources=sources).replace("\n", "")
    await container.slacker.post_blocks_to_channel(channel_id=channel_id, blocks=result)


async def top_interaction_eligibility(data: dict):
    return data.get("type", "") == "block_action" and data.get("actions", {}).get("action_id", "") == "top_submission"


async def top_interaction(data: dict):
    user = data['user']['id']
    channel = data['channel']['id']

    # parse values
    values = data['state']['values']

    # parse amount
    amount_str = values['top_amount_selector']['top_amount_selector']['selected_option']['value']
    amount = try_parse_int(amount_str)
    if amount is None:
        await container.slacker.post_to_channel(channel_id=channel, text=f"Erroneous number: {amount_str}")
        return

    if amount <= 0:
        await container.slacker.post_to_channel(channel_id=channel, text=f"Number of messages should be positive, "
                                                                         f"provided value: {amount}")
        return

    sorting_type = values['top_sorting_selector']['top_sorting_selector']['selected_option']['value']
    if sorting_type not in {"reply_count", "thread_length", "reactions_rate"}:
        await container.slacker.post_to_channel(channel_id=channel, text=f"Unknown sorting type: {sorting_type}")
        return

    preset = values['top_preset_selector']['top_preset_selector']['selected_option']['value']

    # TODO: channel_id or preset

    # TODO: datetime

    # TODO: request to database and return pretty formatted message
    #  with direct links in slack instead of current

