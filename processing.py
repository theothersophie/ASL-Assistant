from discord import Embed, Colour

def search_result_list(search_results):
    num_results = len(search_results)
    processed_results = ""
    if num_results == 0:
        return "No results found."
    for result in search_results:
        phrase = result[0]
        video_url = result[1]
        processed_results += f"• [{phrase}]({video_url})\n"

    return processed_results

def embeds_generator(search_results, search_input):
    num_results = len(search_results)
    embeds = []
    if num_results == 0:
        embed = make_search_embed(search_input, "No results found.")
        embeds.append(embed)
        return embeds
    elif num_results > 10:
        for i in range(0, num_results, 10):
            result_list = search_results[i:i+10]
            processed_results = search_result_list(result_list)
            embed = make_search_embed(search_input, processed_results)
            embeds.append(embed)
    else:
        processed_results = search_result_list(search_results)
        embed = make_search_embed(search_input, processed_results)
        embeds.append(embed)

    return embeds

def make_search_embed(search_input, processed_results):
    query_formatted = '+'.join(search_input.split())
    embed = Embed(
        title=f"Search results: {search_input}",
        description=processed_results,
        colour=Colour.red()
    )
    embed.set_footer(text="Lifeprint.com",
                     icon_url="https://i.imgur.com/OreZulQ.png")
    embed.add_field(name='Additional info',
                    value=f'[See Google search results >>](https://www.google.com/search?hl=en&q=site%3Alifeprint.com+{query_formatted})')

    return embed
