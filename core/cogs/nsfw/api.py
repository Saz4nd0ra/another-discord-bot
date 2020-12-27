import rule34
import pybooru as danbooru
import asyncio
import random


VIDEO_FORMATS = [
    "mp4",
    "webm",
    # and so on, I don't really know which formats r34 uses
]


class Rule34:

    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.rule34 = rule34.Rule34(self.loop)

    async def get_random_post_url(self, search):

        images = await self.rule34.getImages(tags=search)
        try:
            file = images[random.randint(0, len(images) - 1)]
        except TypeError:
            return

        if any(x in file.file_url for x in VIDEO_FORMATS):
            is_video = True
        else:
            is_video = False

        if file.source:
            has_source = True
        else:
            has_source = False

        return file, is_video, has_source
