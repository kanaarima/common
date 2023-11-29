
from boto3_type_annotations.s3 import Client
from botocore.exceptions import ClientError
from typing import List

from datetime import timedelta
from typing import Optional
from redis import Redis

from .database.repositories import scores

from .helpers.external import Beatmaps
from .streams import StreamOut
from .helpers import replays

import logging
import config
import boto3
import os
import io

class Storage:
    """This class aims to provide a higher level api for using/managing storage."""

    def __init__(self) -> None:
        self.logger = logging.getLogger('storage')

        self.cache = Redis(
            config.REDIS_HOST,
            config.REDIS_PORT
        )

        self.s3: Client = boto3.client(
            's3',
            endpoint_url=config.S3_BASEURL,
            aws_access_key_id=config.S3_ACCESS_KEY,
            aws_secret_access_key=config.S3_SECRET_KEY
        )

        self.api = Beatmaps()

    def get_avatar(self, id: str) -> Optional[bytes]:
        if (image := self.get_from_cache(f'avatar:{id}')):
            return image

        if config.S3_ENABLED:
            if not (image := self.get_from_s3(id, 'avatars')):
                return

        elif not (image := self.get_file_content(f'/avatars/{id}')):
            return

        self.save_to_cache(
            name=f'avatar:{id}',
            content=image,
            expiry=timedelta(days=1)
        )

        return image
    
    def get_screenshot(self, id: int) -> Optional[bytes]:
        if config.S3_ENABLED:
            if not (image := self.get_from_s3(str(id), 'screenshots')):
                return

        elif not (image := self.get_file_content(f'/screenshots/{id}')):
            return

        return image
    
    def get_replay(self, id: int) -> Optional[bytes]:
        if (replay := self.get_from_cache(f'osr:{id}')):
            return replay

        if config.S3_ENABLED:
            if not (replay := self.get_from_s3(str(id), 'replays')):
                return

        elif not (replay := self.get_file_content(f'/replays/{id}')):
            return

        self.save_to_cache(
            name=f'osr:{id}',
            content=replay,
            expiry=timedelta(hours=1)
        )

        return replay
    
    def get_full_replay(self, id: int) -> Optional[bytes]:
        if not (replay := self.get_replay(id)):
            return

        score = scores.fetch_by_id(id)

        stream = StreamOut()
        stream.u8(score.mode)
        stream.s32(score.client_version)
        stream.string(score.beatmap.md5)
        stream.string(score.user.name)
        stream.string(replays.compute_score_checksum(score))
        stream.u16(score.n300)
        stream.u16(score.n100)
        stream.u16(score.n50)
        stream.u16(score.nGeki)
        stream.u16(score.nKatu)
        stream.u16(score.nMiss)
        stream.s32(score.total_score)
        stream.u16(score.max_combo)
        stream.bool(score.perfect)
        stream.s32(score.mods)
        stream.string('') # TODO: HP Graph
        stream.s64(replays.get_ticks(score.submitted_at))
        stream.s32(len(replay))
        stream.write(replay)
        stream.s32(score.id)

        return stream.get()

    def get_beatmap(self, id: int) -> Optional[bytes]:
        if (osu := self.get_from_cache(f'osu:{id}')):
            return osu

        # Check for custom beatmap files

        if config.S3_ENABLED:
            osu = self.get_from_s3(str(id), 'beatmaps')

        else:
            osu = self.get_file_content(f'/beatmaps/{id}')

        if not osu:
            # Get beatmap file from peppy's servers if not found
            osu = self.api.osu(id)

        if not osu:
            return

        self.save_to_cache(
            name=f'osu:{id}',
            content=osu,
            expiry=timedelta(hours=1)
        )

        return osu

    def get_background(self, id: str) -> Optional[bytes]:
        if (image := self.get_from_cache(f'mt:{id}')):
            return image

        set_id = int(id.replace('l', ''))
        large = 'l' in id

        if not (image := self.api.background(set_id, large)):
            return

        self.save_to_cache(
            name=f'mt:{id}',
            content=image,
            expiry=timedelta(weeks=3)
        )

        return image

    def get_mp3(self, set_id: int) -> Optional[bytes]:
        if (mp3 := self.get_from_cache(f'mp3:{set_id}')):
            return mp3

        if not (mp3 := self.api.preview(set_id)):
            return

        self.save_to_cache(
            name=f'mp3:{set_id}',
            content=mp3,
            expiry=timedelta(hours=1)
        )

        return mp3

    def get_release_file(self, filename: str) -> Optional[bytes]:
        if config.S3_ENABLED:
            return self.get_from_s3(filename, 'release')
        else:
            return self.get_file_content(f'/release/{filename}')

    def get_patch_file(self, filename: str) -> Optional[bytes]:
        if config.S3_ENABLED:
            return self.get_from_s3(filename, 'patches')
        else:
            return self.get_file_content(f'/patches/{filename}')

    def upload_avatar(self, id: int, content: bytes):
        if config.S3_ENABLED:
            self.save_to_s3(content, str(id), 'avatars')

        else:
            self.save_to_file(f'/avatars/{id}', content)
        
        self.save_to_cache(
            name=f'avatar:{id}',
            content=content,
            expiry=timedelta(weeks=1)
        )

    def upload_screenshot(self, id: int, content: bytes):
        if config.S3_ENABLED:
            self.save_to_s3(content, str(id), 'screenshots')

        else:
            self.save_to_file(f'/screenshots/{id}', content)
    
    def upload_replay(self, id: int, content: bytes):
        if config.S3_ENABLED:
            self.save_to_s3(content, str(id), 'replays')

        else:
            self.save_to_file(f'/replays/{id}', content)

        self.save_to_cache(
            name=f'osr:{id}',
            content=content,
            expiry=timedelta(days=1)
        )

    def upload_beatmap_file(self, id: int, content: bytes):
        if config.S3_ENABLED:
            self.save_to_s3(content, str(id), 'beatmaps')

        else:
            self.save_to_file(f'/beatmaps/{id}', content)

        self.save_to_cache(
            name=f'osu:{id}',
            content=content,
            expiry=timedelta(days=1)
        )

    def cache_replay(self, id: int, content: bytes, time=timedelta(hours=1)):
        self.save_to_cache(
            name=f'osr:{id}',
            content=content,
            expiry=time
        )

    def remove_replay(self, id: int):
        self.logger.debug(f'Removing replay with id "{id}"...')

        if not config.S3_ENABLED:
            return self.remove_file(f'/replays/{id}')
        else:
            return self.remove_from_s3('replays', str(id))

    def get_presigned_url(self, bucket: str, key: str, expiration: int = 900) -> Optional[str]:
        if not config.S3_ENABLED:
            return

        try:
            return self.s3.generate_presigned_url(
                ClientMethod='get_object',
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expiration,
            )
        except ClientError as e:
            self.logger.error(f'Failed to generate presigned url: {e}')
            return

    def save_to_cache(self, name: str, content: bytes, expiry=timedelta(weeks=1), override=True) -> bool:
        return self.cache.set(name, content, expiry, nx=(not override))

    def save_to_file(self, filepath: str, content: bytes) -> bool:
        try:
            with open(f'{config.DATA_PATH}/{filepath}', 'wb') as f:
                f.write(content)
        except Exception as e:
            self.logger.error(f'Failed to save file "{filepath}": {e}')
            return False

        return True

    def save_to_s3(self, content: bytes, key: str, bucket: str) -> bool:
        try:
            self.s3.upload_fileobj(
                io.BytesIO(content),
                bucket,
                key
            )
        except Exception as e:
            self.logger.error(f'Failed to upload "{key}" to s3: "{e}"')
            return False

        return True

    def remove_from_s3(self, bucket: str, key: str) -> bool:
        try:
            self.s3.delete_object(
                Bucket=bucket,
                Key=key
            )
        except Exception as e:
            self.logger.error(f'Failed to remove "{key}" from {bucket}: "{e}"')
            return False

        return True

    def get_from_cache(self, name: str) -> Optional[bytes]:
        return self.cache.get(name)

    def get_file_content(self, filepath: str) -> Optional[bytes]:
        try:
            with open(f'{config.DATA_PATH}/{filepath}', 'rb') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f'Failed to read file "{filepath}": {e}')

    def remove_file(self, filepath: str) -> bool:
        try:
            os.remove(f'{config.DATA_PATH}/{filepath}')
        except Exception as e:
            self.logger.error(f'Failed to file "{filepath}": "{e}"')
            return False

        return True

    def get_from_s3(self, key: str, bucket: str) -> Optional[bytes]:
        buffer = io.BytesIO()

        try:
            self.s3.download_fileobj(
                bucket,
                key,
                buffer
            )
        except ClientError:
            # Most likely not found
            return
        except Exception as e:
            self.logger.error(f'Failed to download "{key}" from s3: "{e}"')
            return

        return buffer.getvalue()

    def list(self, key: str) -> List[str]:
        """Get a list of filenames from the specified bucket/directory."""
        return self.list_bucket(key) if config.S3_ENABLED else self.list_directory(key)

    def list_directory(self, dir: str) -> List[str]:
        return os.listdir(f'{config.DATA_PATH}/{dir}')

    def list_bucket(self, bucket: str) -> List[str]:
        return [object['Key'] for object in self.s3.list_objects(Bucket=bucket)['Contents']]
