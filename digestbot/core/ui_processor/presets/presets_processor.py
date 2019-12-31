from digestbot.core.db.dbengine.PostgreSQLEngine import PostgreSQLEngine
from digestbot.core.db.dbrequest.category import get_all_categories


async def process_presets_request(db_engine: PostgreSQLEngine) -> str:
    status, presets_list = await get_all_categories(db_engine)

    if not status:
        return "Oops, database is unavailable now. Please, try later or notify bot creators."
    if not presets_list:
        return "No available presets for now :("

    answer = "Available presets:\n\n"
    answer += "\n".join(
        f"`{x.name}`: " f"{', '.join(f'<#{c}>' for c in x.channel_ids)}"
        for x in presets_list
    )
    return answer
