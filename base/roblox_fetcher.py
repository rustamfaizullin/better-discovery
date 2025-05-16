import requests
import aiohttp
import datetime
from base.models import Game, Review
from asgiref.sync import sync_to_async
from dotenv import load_dotenv
import os
import asyncio
from django.db.models import Avg, Count
from django.db.models.functions import Coalesce

load_dotenv()

class PlacePlayerCount:
    def __init__(self, place_id, icon, name, playerCount, rating):
        self.place_id = place_id
        self.icon = icon
        self.name = name
        self.playerCount = playerCount
        self.rating = rating

class Place:
    def __init__(self, place_id, icon, name, rating):
        self.place_id = place_id
        self.icon = icon
        self.name = name
        self.rating = rating

class GameData:
    def __init__(self, place_id, source_name, source_description, creator_id, creator_type, creator_name, 
                 visits, favorited_count, created, updated, active, avatar_type):
        self.place_id = place_id
        self.source_name = source_name
        self.source_description = source_description
        self.creator_id = creator_id
        self.creator_type = creator_type
        self.creator_name = creator_name
        self.visits = visits
        self.favorited_count = favorited_count
        self.created = created
        self.updated = updated
        self.active = active
        self.avatar_type = avatar_type
        self.rating = None

class RobloxFetcher:
    API_CONFIG = {
        'COOKIE': os.environ.get('COOKIE'),
        'USER_AGENT': 'Mozilla/5.0',
        'THUMBNAIL_SIZE': '700x700',  # 30x30, 42x42 ... 250x250
        'THUMBNAIL_FORMAT': 'Png',  # Jpeg, Webp
        'IS_CIRCULAR': False  # True
    }
    UNIVERSE_URL = 'https://apis.roblox.com/universes/v1/places/{input}/universe'
    # MEDIA_URL = 'https://games.roblox.com/v2/games/{universe_id}/media?fetchAllExperienceRelatedMedia=false'
    # THUMBNAIL_URL = 'https://thumbnails.roblox.com/v1/assets?assetIds={ids_str}&size={size}&format={format}&isCircular={is_circular}'
    THUMBNAIL_URL = 'https://thumbnails.roblox.com/v1/games/multiget/thumbnails?universeIds={input}&countPerUniverse=16&defaults=true&size=768x432&format=Png&isCircular=false'
    GAME_DATA_URL = 'https://games.roblox.com/v1/games?universeIds={input}'
    GAME_UNIVERSE_IDS_URL = 'https://games.roblox.com/v1/games/multiget-place-details?placeIds={input}'
    GAME_ICON_URL = 'https://thumbnails.roblox.com/v1/places/gameicons?placeIds={input}&returnPolicy=PlaceHolder&size=256x256&format=Png&isCircular=false'
    SEARCH_QUERY_URL = 'https://apis.roblox.com/search-api/omni-search?searchQuery={input}&sessionId=246624'

    def __init__(self):
        self.headers = {
            'User-Agent': self.API_CONFIG['USER_AGENT'],
            'Cookie': self.API_CONFIG['COOKIE'],
        }

    # возвращает ответ роблокс апи
    def fetch_json(self, url_template, input_value):
        url = url_template.format(input=input_value)
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    async def fetch_json_async(self, url_template, input_value, session):
        url = url_template.format(input=input_value)
        async with session.get(url, headers=self.headers) as response:
            return await response.json()

    # методы для работы с universe ID
    def get_universe_id(self, place_id):
        data = self.fetch_json(self.UNIVERSE_URL, place_id)
        return data['universeId']
    
    async def get_universe_id_async(self, place_id, session):
        data = await self.fetch_json_async(self.UNIVERSE_URL, place_id, session)
        return data['universeId']
    
    def get_universe_ids(self, place_ids):
        universe_ids = [self.get_universe_id(place_id) for place_id in place_ids]
        return ','.join(str(universe_id) for universe_id in universe_ids)
    
    async def get_universe_ids_async(self, place_ids):
        async with aiohttp.ClientSession() as session:
            universe_ids = await asyncio.gather(
                *[self.get_universe_id_async(place_id, session) for place_id in place_ids]
            )
            return ','.join(str(universe_id) for universe_id in universe_ids)
    
    # методы для работы с иконками и тамбнейлами
    def get_games_icons(self, place_ids):
        if not place_ids:
            return None
        place_ids_icons = ','.join(str(id) for id in place_ids)
        icons_data = self.fetch_json(self.GAME_ICON_URL, place_ids_icons)['data']
        return {item["targetId"]: item["imageUrl"] for item in icons_data}

    async def get_games_icons_async(self, place_ids, session):
        if not place_ids:
            return None
        place_ids_icons = ','.join(str(id) for id in place_ids)
        icons_data = await self.fetch_json_async(self.GAME_ICON_URL, place_ids_icons, session)
        return icons_data
    
    async def get_game_icon_async(self, place_id, session):
        if not place_id:
            return None
        icons_data = await self.fetch_json_async(url_template=self.GAME_ICON_URL, input_value=place_id, session=session)
        return icons_data
    
    def get_game_icon(self, place_id):
        if not place_id:
            return None
        icons_data = self.fetch_json(self.GAME_ICON_URL, place_id)
        return icons_data

    async def fetch_game_thumbnails_async(self, session, universe_id):
        data = await self.fetch_json_async(self.THUMBNAIL_URL, universe_id, session)
        return data
    
    def fetch_game_thumbnails(self, universe_id):
        data = self.fetch_json(self.THUMBNAIL_URL, universe_id)
        return data

    async def fetch_games_thumbnails(self, session, universe_ids):
        """В разработке"""
        data = await self.fetch_json_async(self.THUMBNAIL_URL, universe_ids, session)
        return data
        # return [{item['universeId']: item['thumbnails']} for item in data['data']]
    
    async def fetch_game_data_async(self, session, universe_id):
        data = await self.fetch_json_async(self.GAME_DATA_URL, universe_id, session)
        data = data['data'][0]
        return data
    
    def fetch_game_data(self, universe_id):
        data = self.fetch_json(self.GAME_DATA_URL, universe_id)
        return data['data'][0]
    
    def get_discover_games_datas(self, data):
        place_ids = [item['contents'][0]['rootPlaceId'] for item in data]
        temp_playerCounts = [item['contents'][0]['playerCount'] for item in data]
        names = [item['contents'][0]['name'] for item in data]

        playerCounts = []
        for playerCount in temp_playerCounts:
            playerCount = self.change_value(playerCount)
            playerCounts.append(playerCount)

        games_infos = {}
        for i, item in enumerate(place_ids):
            games_infos.update({item: {'name': names[i], 'playerCount': playerCounts[i]}})

        icon_dict = self.get_games_icons(place_ids)
        if icon_dict is None:
            return None
        
        games_ratings = []
        for i, place_id in enumerate(place_ids):
            game = Game.objects.filter(id=place_id)
            if game:
                game = Game.objects.get(id=place_id)
                reviews = Review.objects.filter(game=game)
                number_reviews = len(reviews)
                if number_reviews > 0:
                    game_rate = sum(review.score for review in reviews) / number_reviews
            if not game or number_reviews == 0:
                game_rate = 0.00
            games_ratings.append(game_rate)

        results = []
        for i, place_id in enumerate(place_ids):
            icon = icon_dict.get(place_id)
            name = games_infos[place_id]['name']
            playerCount = games_infos[place_id]['playerCount']
            game_rate = games_ratings[i]
            game = PlacePlayerCount(place_id, icon, name, playerCount, game_rate)
            results.append(game)
            
            # if i == 2:
            #     results[0], results[2] = results[2], results[0]
        
        return results
    
    async def get_feed_games_datas_async(self, games_ids_ratings, session):
        games_ids = [id for id, _ in games_ids_ratings]
        games_ratings = [rating for _, rating in games_ids_ratings]

        api_input = '&placeIds='.join(str(id) for id in games_ids)

        icons_data, data = await asyncio.gather(
            self.get_games_icons_async(games_ids, session),
            self.fetch_json_async(self.GAME_UNIVERSE_IDS_URL, api_input, session)
        )

        names = [item['sourceName'] for item in data]

        icons_data = icons_data['data']
        icon_dict = {item['targetId']: item['imageUrl'] for item in icons_data}
        
        results = []
        for i, game_id in enumerate(games_ids):
            icon = icon_dict.get(int(game_id))
            name = names[i]
            game_rate = games_ratings[i]
            game = Place(game_id, icon, name, game_rate)
            results.append(game)
        
        return results
    
    async def get_feed_async(self, games_ids_ratings, expected_games_ids):
        async with aiohttp.ClientSession() as session:
            place_objects = await self.get_feed_games_datas_async(games_ids_ratings, session)
            output_games_ids = [item.place_id for item in place_objects]

            error_list = [item for item in expected_games_ids if item not in output_games_ids]

            return place_objects, error_list
        
    async def get_game_async(self, place_id):
        async with aiohttp.ClientSession() as session:
            universe_id = await self.get_universe_id_async(place_id, session)
            thumbnail_data, raw_game_data, icon_data = await asyncio.gather(
                self.fetch_game_thumbnails_async(session, universe_id),
                self.fetch_game_data_async(session, universe_id),
                self.get_game_icon_async(session=session, place_id=place_id),
            )
            icon_url = icon_data['data'][0]['imageUrl']
            thumbnail_urls = list(reversed([item['imageUrl'] for item in thumbnail_data['data'][0]['thumbnails']]))

            game_data = GameData(
                place_id = raw_game_data['rootPlaceId'],
                source_name = raw_game_data['name'],
                source_description = raw_game_data['description'],
                creator_id = raw_game_data['creator']['id'],
                creator_type = raw_game_data['creator']['name'],
                creator_name = raw_game_data['creator']['type'],
                visits = self.change_value(raw_game_data['visits']),
                favorited_count = self.change_value(raw_game_data['favoritedCount']),
                created = datetime.datetime.fromisoformat(raw_game_data['created']).strftime('%d/%m/%Y'),
                updated = datetime.datetime.fromisoformat(raw_game_data['updated']).strftime('%d/%m/%Y'),
                active = self.change_value(raw_game_data['playing']),
                avatar_type = raw_game_data['universeAvatarType'],
            )

            return game_data, icon_url, thumbnail_urls
        
    async def get_feed_game_async(self, place_id):
        async with aiohttp.ClientSession() as session:
            universe_id = await self.get_universe_id_async(place_id, session)
            thumbnail_data, raw_game_data, icon_data = await asyncio.gather(
                self.fetch_game_thumbnails_async(session=session, universe_id=universe_id),
                self.fetch_game_data_async(session=session, universe_id=universe_id),
                self.get_game_icon_async(session=session, place_id=place_id),
            )
            icon_url = icon_data['data'][0]['imageUrl']
            game_data = GameData(
                source_name = raw_game_data['name'],
                source_description = raw_game_data['description'],
                creator_id = raw_game_data['creator']['id'],
                creator_type = raw_game_data['creator']['name'],
                creator_name = raw_game_data['creator']['type'],
                visits = self.change_value(raw_game_data['visits']),
                favorited_count = self.change_value(raw_game_data['favoritedCount']),
                created = datetime.datetime.fromisoformat(raw_game_data['created']).strftime('%d/%m/%Y'),
                updated = datetime.datetime.fromisoformat(raw_game_data['updated']).strftime('%d/%m/%Y'),
                active = self.change_value(raw_game_data['playing']),
                avatar_type = raw_game_data['universeAvatarType']
            )
            thumbnail_urls = reversed([item['imageUrl'] for item in thumbnail_data['data'][0]['thumbnails']])

            return game_data, icon_url
        
    def get_game(self, place_id):
        universe_id = self.get_universe_id(place_id)
        icon_url = self.get_game_icon(place_id)['data'][0]['imageUrl']
        raw_game_data = self.fetch_game_data(universe_id=universe_id)
        thumbnail_data = self.fetch_game_thumbnails(universe_id=universe_id)
        game_data = GameData(
                place_id = raw_game_data['rootPlaceId'],
                source_name = raw_game_data['name'],
                source_description = raw_game_data['description'],
                creator_id = raw_game_data['creator']['id'],
                creator_type = raw_game_data['creator']['type'],
                creator_name = raw_game_data['creator']['name'],
                visits = self.change_value(raw_game_data['visits']),
                favorited_count = self.change_value(raw_game_data['favoritedCount']),
                created = datetime.datetime.fromisoformat(raw_game_data['created']).strftime('%d/%m/%Y'),
                updated = datetime.datetime.fromisoformat(raw_game_data['updated']).strftime('%d/%m/%Y'),
                active = self.change_value(raw_game_data['playing']),
                avatar_type = raw_game_data['universeAvatarType'],
            )
        thumbnail_urls = list(reversed([item['imageUrl'] for item in thumbnail_data['data'][0]['thumbnails']]))

        return game_data, icon_url, thumbnail_urls
    
    def cleanup_games(self, place_ids):
        api_input = '&placeIds='.join(str(id) for id in place_ids)
        data = self.fetch_json(self.GAME_UNIVERSE_IDS_URL, api_input)
        return [item["placeId"] for item in data]

    def get_search_query(self, search_query):
        data = self.fetch_json(self.SEARCH_QUERY_URL, search_query)['searchResults']
        if data == []:
            return None
        else:
            return self.get_discover_games_datas(data)
        
    def change_value(self, game_data_value):
        if game_data_value >= 1000000000:
            value = game_data_value / 1000000000
            return f'{value:.1f}B'
        elif game_data_value >= 1000000:
            value = game_data_value / 1000000
            return f'{value:.1f}M'
        elif game_data_value >= 1000:
            value = game_data_value / 1000
            return f'{value:.1f}K'
        else:
            return str(game_data_value)
            

# entry point
if __name__ == "__main__":
    fetcher = RobloxFetcher()

    place_ids = [116495829188952, 109444064268030, 97916836477883, 97302920770927, 91775736217182, 100998285081535, 137934409945962, 94857518748707, 70754779249108]  # replace with the desired place IDs
    place_id = 116495829188952  # replace with the desired place ID

    # feed = fetcher.get_feed()

    # print(asyncio.run(fetcher.get_game_async(place_id)))

    # search_query = 'deadrails'
    # print(fetcher.get_search_query(search_query))

    # print(fetcher.fetch_games_data(place_ids))
    # print(fetcher.fetch_game_data(place_id))

    # print(fetcher.fetch_game_thumbnails(place_id))

    # thumbnail_urls = fetcher.get_game_thumbnails(place_id)

    # print(fetcher.fetch_game_stats(place_id))

    # for url in thumbnail_urls:
    #     print(url)

    # fetcher.fetch_game_description(place_id)

    # name, description, builder = 
    # print(fetcher.fetch_game_data(place_id))
    # print(name)
    # print(description)
    # print(builder)

    # game_icons = fetcher.get_games_icons(place_ids)
    # print(game_icons)
    # game_icons_async = asyncio.run(fetcher.get_games_icons_async(place_ids))
    # print(game_icons_async)
    # print(game_icons_async)