import requests
import aiohttp
import datetime
from base.models import Game, Review
from asgiref.sync import sync_to_async
from dotenv import load_dotenv
import os

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
    SEARCH_QUERY_URL = 'https://apis.roblox.com/search-api/omni-search?searchQuery={input}&sessionId=1'

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
    
    def get_universe_ids(self, place_ids):
        universe_ids = [self.get_universe_id(place_id) for place_id in place_ids]
        return ','.join(str(universe_id) for universe_id in universe_ids)
    
    # методы для работы с иконками и тамбнейлами
    def get_game_icon(self, place_id):
        data = self.fetch_json(self.GAME_ICON_URL, place_id)
        if 'errors' in data:
            return 'Too many requests'
        else:
            return data['data'][0]['imageUrl']
        
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
        
    def fetch_game_thumbnails(self, place_id):
        universe_id = self.get_universe_id(place_id)
        data = self.fetch_json(self.THUMBNAIL_URL, universe_id)['data'][0]['thumbnails']
        return list(reversed([item['imageUrl'] for item in data]))

    def fetch_games_thumbnails(self, place_ids):
        universe_ids = self.get_universe_ids(place_ids)
        data = self.fetch_json(self.THUMBNAIL_URL, universe_ids)['data']
        return [{item['universeId']: item['thumbnails']} for item in data]

    def fetch_game_data(self, place_id):
        universe_id = self.get_universe_id(place_id)
        data = self.fetch_json(self.GAME_DATA_URL, universe_id)['data'][0]
        place_id = data['rootPlaceId']
        source_name = data['sourceName']
        source_description = data['sourceDescription']
        creator_id = data['creator']['id']
        creator_name = data['creator']['name']
        creator_type = data['creator']['type']
        visits = data['visits']
        favorited_count= data['favoritedCount']
        created_data = data['created']
        updated_data = data['updated']
        active = data['playing']
        avatar_type = data['universeAvatarType']

        created = datetime.datetime.fromisoformat(created_data).strftime('%d/%m/%Y')
        updated = datetime.datetime.fromisoformat(updated_data).strftime('%d/%m/%Y')

        visits = self.change_value(visits)
        favorited_count = self.change_value(favorited_count)
        active = self.change_value(active)

        return GameData(place_id, source_name, source_description, creator_id, creator_type, creator_name, visits,
                 favorited_count, created, updated, active, avatar_type)

    def fetch_games_data(self, place_ids):
        universe_ids = self.get_universe_ids(place_ids)
        data = self.fetch_json(self.GAME_DATA_URL, universe_ids)['data']
        return [
            [
                item['id'],
                item['sourceName'],
                item['sourceDescription'],
                item['creator']['id'],
                item['creator']['name'],
                item['creator']['type'], 
                item['visits'], 
                item['favoritedCount'], 
                item['created'], 
                item['updated'], 
                item['playing'], 
                item['universeAvatarType']
            ]
            for item in data
        ]
    
    def get_games_datas(self, data):
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
            game = Game.objects.get_or_create(id=place_id)
            reviews = Review.objects.filter(game=game)
            number_reviews = len(reviews)
            if number_reviews > 0:
                game_rate = sum(review.score for review in reviews) / number_reviews
            else:
                game_rate = 0
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
        
    def get_feed_games_datas(self, games_ids_ratings):
        games_ids = [id for id, _ in games_ids_ratings]
        games_ratings = [rating for _, rating in games_ids_ratings]

        icon_dict = self.get_games_icons(games_ids)

        api_input = '&placeIds='.join(str(id) for id in games_ids)
        data = self.fetch_json(self.GAME_UNIVERSE_IDS_URL, api_input)
        names = [item['sourceName'] for item in data]
        
        results = []
        for i, game_id in enumerate(games_ids):
            icon = icon_dict.get(int(game_id))
            name = names[i]
            game_rate = games_ratings[i]
            game = Place(game_id, icon, name, game_rate)
            results.append(game)
        
        return results
    
    async def get_feed_games_datas_async(self, games_ids_ratings, session):
        games_ids = [id for id, _ in games_ids_ratings]
        games_ratings = [rating for _, rating in games_ids_ratings]

        icons_data = await self.get_games_icons_async(games_ids, session)
        icons_data = icons_data['data']
        icon_dict = {item['targetId']: item['imageUrl'] for item in icons_data}

        api_input = '&placeIds='.join(str(id) for id in games_ids)
        data = await self.fetch_json_async(self.GAME_UNIVERSE_IDS_URL, api_input, session)
        names = [item['sourceName'] for item in data]
        
        results = []
        for i, game_id in enumerate(games_ids):
            icon = icon_dict.get(int(game_id))
            name = names[i]
            game_rate = games_ratings[i]
            game = Place(game_id, icon, name, game_rate)
            results.append(game)
        
        return results

    def get_feed(self):
        games_ids_ratings = self.get_feed_ids_ratings()
        expected_games_ids = [item for item, _ in games_ids_ratings]
        place_objects = self.get_feed_games_datas(games_ids_ratings)
        output_games_ids = [item.place_id for item in place_objects]

        error_list = [item for item in expected_games_ids if item not in output_games_ids]

        return place_objects, error_list, expected_games_ids
    
    async def get_feed_async(self):
        games_ids_ratings = await sync_to_async(self.get_feed_ids_ratings)()
        expected_games_ids = [item for item, _ in games_ids_ratings]
        async with aiohttp.ClientSession() as session:
            place_objects = await self.get_feed_games_datas_async(games_ids_ratings, session)
            output_games_ids = [item.place_id for item in place_objects]

            error_list = [item for item in expected_games_ids if item not in output_games_ids]

            return place_objects, error_list, expected_games_ids

    def get_feed_ids_ratings(self):
        games = Game.objects.all()

        games_ids_ratings = []
        for game in games:
            reviews = Review.objects.filter(game=game)
            number_reviews = len(reviews)
            if number_reviews > 0:
                game_rate = sum(review.score for review in reviews) / number_reviews
            else:
                game_rate = 0
            games_ids_ratings.append((game.id, game_rate))

        return sorted(games_ids_ratings, key=lambda x: x[1], reverse=True)[:49]

    def get_search_query(self, search_query):
        data = self.fetch_json(self.SEARCH_QUERY_URL, search_query)['searchResults']
        if data == []:
            return None
        else:
            return self.get_games_datas(data)
        
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
            return game_data_value
            

# entry point
if __name__ == "__main__":
    fetcher = RobloxFetcher()

    place_ids = [116495829188952, 109444064268030, 97916836477883, 97302920770927, 91775736217182, 100998285081535, 137934409945962, 94857518748707, 70754779249108]  # replace with the desired place IDs
    place_id = 116495829188952  # replace with the desired place ID

    feed = fetcher.get_feed()

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