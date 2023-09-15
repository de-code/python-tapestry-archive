import dataclasses
import logging
import os
import re
from datetime import datetime
from pathlib import Path
import sys
import dotenv

import requests
from bs4 import BeautifulSoup


LOGGER = logging.getLogger(__name__)


COOKIE_NAME = 'tapestry_session'
IMAGES_DIR = './images/'


class EnvVarNames:
    TAPESTRY_COOKIE_VALUE = "TAPESTRY_COOKIE_VALUE"
    TAPESTRY_FIRST_OBSERVATION_ID = "TAPESTRY_FIRST_OBSERVATION_ID"
    TAPESTRY_NAME = "TAPESTRY_NAME"
    TAPESTRY_SCHOOL = "TAPESTRY_SCHOOL"


class LoggedOutException(RuntimeError):
    pass


def get_required_env_value(env_var_name: str) -> str:
    value = os.getenv(env_var_name)
    if not value:
        raise RuntimeError('Environment variable %r is required' % env_var_name)
    return value


@dataclasses.dataclass(frozen=True)
class TapestryConfig:
    cookie_value: str
    first_observation_id: str
    name: str
    school: str
    base_url: str
    timeout: float = 60

    @staticmethod
    def from_env() -> 'TapestryConfig':
        school = get_required_env_value(EnvVarNames.TAPESTRY_SCHOOL)
        base_url = f'https://tapestryjournal.com/s/{school}/observation'
        return TapestryConfig(
            cookie_value=get_required_env_value(EnvVarNames.TAPESTRY_COOKIE_VALUE),
            first_observation_id=get_required_env_value(EnvVarNames.TAPESTRY_FIRST_OBSERVATION_ID),
            name=get_required_env_value(EnvVarNames.TAPESTRY_NAME),
            school=school,
            base_url=base_url
        )


def get_doc(observation_id, config: TapestryConfig):
    cookie = {COOKIE_NAME: config.cookie_value}
    url = "{}/{}".format(config.base_url, observation_id)
    LOGGER.info('requesting: %r', url)
    response = requests.get(url, cookies=cookie, timeout=config.timeout)
    response.raise_for_status()
    return BeautifulSoup(response.text, 'html.parser')


def get_file_name(metadata, index, video=False):
    file_name = metadata['date'].strftime('./images/%Y-%m-%d-%H-%M-')
    file_name += re.sub(r'[^\x00-\x7F]', '', metadata['title']).strip().replace(' ', '-')
    file_name += "-{}".format(index) if index > 0 else ''
    file_name += '.mp4' if video else '.jpeg'
    return file_name


def get_metadata(doc):
    for alert in doc.select('.alert'):
        alert_text = alert.text.strip()
        if alert_text:
            LOGGER.warning('alert: %r', alert_text)
            if 'logged out' in alert_text:
                raise LoggedOutException()
    title = doc.select_one('h1').text.strip()
    description = doc.select_one('.page-note p').text.strip().replace('\n', ' ')
    match = re.search(
        r'Authored by (.*) added (.*)',
        doc.select_one('.obs-metadata p').text.strip()
    )
    artist = match.group(1)
    date = datetime.strptime(match.group(2), '%d %b %Y %I:%M %p')
    return {'title': title, 'description': description, 'artist': artist, 'date': date}


def save_images_for_page(images, metadata, config: TapestryConfig):
    for idx, img in enumerate(images):
        image_url = img['src']
        image_data = requests.get(image_url, timeout=config.timeout).content

        file_name = get_file_name(metadata, idx)
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        Path(file_name).write_bytes(image_data)


def save_videos_for_page(videos, metadata, config: TapestryConfig):
    for idx, video in enumerate(videos):
        video_url = video['src']
        video_data = requests.get(video_url, timeout=config.timeout).content

        file_name = get_file_name(metadata, idx, video=True)
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        Path(file_name).write_bytes(video_data)


def capture_observation_info(metadata):
    md = "## {}\n\n".format(metadata['title'])
    md += "### {}, {}\n\n".format(
        metadata['artist'],
        metadata['date'].strftime('%-d %B %Y %I:%M%p')
    )
    md += "{}\n\n".format(metadata['description'])
    return md


def save_media_for_page(doc, config: TapestryConfig):
    images = doc.select('.obs-media-gallery-main img')
    videos = doc.select('.obs-media-gallery-main .obs-video-wrapper video source')
    metadata = get_metadata(doc)
    save_images_for_page(images, metadata, config=config)
    save_videos_for_page(videos, metadata, config=config)
    return capture_observation_info(metadata)


def get_next_observation_id(doc, config: TapestryConfig):
    next_link = doc.select_one('li.previous a')
    if not next_link:
        return None
    match = re.search(r'{}/(\d*)'.format(re.escape(config.base_url)), next_link['href'])
    if not match:
        raise RuntimeError('observation id not found')
    return match.group(1)


def run(config: TapestryConfig):
    observation_id = config.first_observation_id
    md = "# Tapestry observations for {}\n\n".format(config.name)
    while observation_id:
        print(observation_id)
        doc = get_doc(observation_id, config=config)
        md += save_media_for_page(doc, config=config)
        observation_id = get_next_observation_id(doc, config=config)
    Path('./images/observations-info.md').write_text(md, encoding='utf-8')


def main():
    dotenv.load_dotenv()
    config = TapestryConfig.from_env()
    try:
        run(config)
    except LoggedOutException:
        print('ERROR: You appear to be logged out. Check cookie value.')
        sys.exit(1)


if __name__ == '__main__':
    logging.basicConfig(level='INFO')
    main()
