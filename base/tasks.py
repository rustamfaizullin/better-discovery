from celery import shared_task
from django.core.cache import cache
from base.models import Game
from django.db.models import Avg, Count
from django.db.models.functions import Coalesce
from .roblox_fetcher import RobloxFetcher
import time
import requests
import logging

logger = logging.getLogger(__name__)
fetcher = RobloxFetcher()

@shared_task
def update_feed():
    games = Game.objects.annotate(
        average_rating=Coalesce(Avg('reviews__score'), 0.0), count=Count('reviews')
    ).order_by('-average_rating', '-count')[:49]

    for game in games:
        game_data, icon_url, thumbnail_urls = fetcher.get_game(game.id)
        logger.info(game_data.source_name)
        cache.set(f'game_{game.id}', {
            'source_name': game_data.source_name,
            'source_description': game_data.source_description,
            'creator_id': game_data.creator_id,
            'creator_type': game_data.creator_type,
            'creator_name': game_data.creator_name,
            'visits': game_data.visits,
            'favorited_count': game_data.favorited_count,
            'created': game_data.created,
            'updated': game_data.updated,
            'avatar_type': game_data.avatar_type,
            'active': game_data.active,
            'icon_url': icon_url,
            'thumbnail_urls': thumbnail_urls
        }, timeout=100)

@shared_task
def cleanup_games(offset=0, batch_size=49, error_list=None):
    logger.info(f'{offset} - {offset+batch_size}')
    games_ids = list(int(id) for id in Game.objects.values_list('id', flat=True)[offset:offset + batch_size])
    logger.info(f'games in query count: {len(games_ids)}')
    logger.info(games_ids)

    returned_ids = fetcher.cleanup_games(games_ids)
    missing_ids = set(games_ids) - set(returned_ids)
    error_list.extend(list(missing_ids))

    total_games = Game.objects.count()
    if offset + batch_size < total_games:
        logger.info('again')
        cleanup_games.apply_async(args=[offset+batch_size, batch_size, error_list], countdown=1)
    else:
        logger.info('end')
        logger.info(error_list)