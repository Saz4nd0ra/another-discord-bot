import asyncio
import async_timeout
import copy
import datetime
import discord
import humanize
import math
import random
import re
import typing
import wavelink
import logging
import datetime
from enum import Enum
from .utils.embed import Embed
from .utils.context import Context
from discord.ext import commands, menus

URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
OPTIONS = {
    "1️⃣": 0,
    "2⃣": 1,
    "3⃣": 2,
    "4⃣": 3,
    "5⃣": 4,
}

log = logging.getLogger(__name__)


class RepeatMode(Enum):
    NONE = 0
    ONE = 1
    ALL = 2


class Queue:
    def __init__(self):
        self._queue = []
        self.position = 0
        self.repeat_mode = RepeatMode.NONE

    @property
    def is_empty(self):
        return not self._queue

    @property
    def current_track(self):
        if not self._queue:
            raise QueueIsEmpty

        if self.position <= len(self._queue) - 1:
            return self._queue[self.position]

    @property
    def upcoming(self):
        if not self._queue:
            raise QueueIsEmpty

        return self._queue[self.position + 1:]

    @property
    def history(self):
        if not self._queue:
            raise QueueIsEmpty

        return self._queue[:self.position]

    @property
    def length(self):
        return len(self._queue)

    def add(self, *args):
        self._queue.extend(args)

    def get_next_track(self):
        if not self._queue:
            raise QueueIsEmpty

        self.position += 1

        if self.position < 0:
            return None
        elif self.position > len(self._queue) - 1:
            if self.repeat_mode == RepeatMode.ALL:
                self.position = 0
            else:
                return None

        return self._queue[self.position]

    def shuffle(self):
        if not self._queue:
            raise QueueIsEmpty

        upcoming = self.upcoming
        random.shuffle(upcoming)
        self._queue = self._queue[:self.position + 1]
        self._queue.extend(upcoming)

    def set_repeat_mode(self, mode):
        if mode == "none":
            self.repeat_mode = RepeatMode.NONE
        elif mode == "1":
            self.repeat_mode = RepeatMode.ONE
        elif mode == "all":
            self.repeat_mode = RepeatMode.ALL

    def empty(self):
        self._queue.clear()
        self.position = 0


class Track(wavelink.Track):
    """Wavelink Track object with a requester attribute."""

    __slots__ = "requester"

    def __init__(self, *args, **kwargs):
        super().__init__(*args)

        self.requester = kwargs.get("requester")


class Player(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = Queue()

    async def connect(self, ctx, channel=None):
        if self.is_connected:
            raise AlreadyConnectedToChannel

        if (channel := getattr(ctx.author.voice, "channel", channel)) is None:
            raise NoVoiceChannel

        await super().connect(channel.id)
        return channel

    async def teardown(self):
        try:
            await self.destroy()
        except KeyError:
            pass

    async def add_tracks(self, ctx, tracks):
        if not tracks:
            raise NoTracksFound

        if isinstance(tracks, wavelink.TrackPlaylist):
            for track in tracks.tracks:
                track = Track(track.id, track.info, requester=ctx.author)
                await player.queue.put(track)
                await ctx.embed(
                f'`Added the playlist {tracks.data["playlistInfo"]["name"]}'
                f" with {len(tracks.tracks)} songs to the queue.\n`"
            )
        else:
            track = Track(tracks[0].id, tracks[0].info, requester=ctx.author)
            self.queue.add(track)
            await ctx.embed(f"Added {track.title} to the queue.")

        if not self.is_playing and not self.queue.is_empty:
            await self.start_playback()

    async def start_playback(self):
        await self.play(self.queue.current_track)

    async def advance(self):
        try:
            if (track := self.queue.get_next_track()) is not None:
                await self.play(track)
        except QueueIsEmpty:
            pass

    async def repeat_track(self):
        await self.play(self.queue.current_track)


class Music(commands.Cog, wavelink.WavelinkMixin):
    """The obligatory Music cog."""

    def __init__(self, bot):
        self.bot = bot
        self.config = self.bot.config
        self.wavelink = wavelink.Client(bot=bot)
        self.bot.loop.create_task(self.start_nodes())

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.bot and after.channel is None:
            if not [m for m in before.channel.members if not m.bot]:
                await self.get_player(member.guild).teardown()

    async def start_nodes(self):
        await self.bot.wait_until_ready()

        nodes = {
            "MAIN": {
                "host": self.config.ll_host,
                "port": self.config.ll_port,
                "rest_uri": f"http://{self.config.ll_host}:{self.config.ll_port}",
                "password": self.config.ll_passwd,
                "identifier": "ADB",
                "region": "eu",
            }
        }

        for node in nodes.values():
            await self.wavelink.initiate_node(**node)

    @wavelink.WavelinkMixin.listener()
    async def on_node_ready(self, node):
        log.info(f"Node {node.identifier} is ready!")

    @wavelink.WavelinkMixin.listener("on_track_stuck")
    @wavelink.WavelinkMixin.listener("on_track_end")
    @wavelink.WavelinkMixin.listener("on_track_exception")
    async def on_player_stop(self, node, payload):
        if payload.player.queue.repeat_mode == RepeatMode.ONE:
            await payload.player.repeat_track()
        else:
            await payload.player.advance()

    async def cog_check(self, ctx):
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("Music commands are not available in DMs.")
            return False

        return True

    def get_player(self, obj):
        if isinstance(obj, commands.Context):
            return self.wavelink.get_player(obj.guild.id, cls=Player, context=obj)
        elif isinstance(obj, discord.Guild):
            return self.wavelink.get_player(obj.id, cls=Player)

    @commands.command()
    async def connect(self, ctx, *, channel=None):
        """Connect to a voice channel."""
        player = self.get_player(ctx)

        if player.is_connected:
            return

        channel = getattr(ctx.author.voice, "channel", channel)
        if channel is None:
            return await ctx.error("No channel provided!", 10)

        await player.connect(channel.id)

    @commands.command(aliases=["p"])
    async def play(self, ctx, *, query):
        """Play or queue a song with the given query."""
        player = self.get_player(ctx)

        if not player.is_connected:
            await player.connect(ctx)

        
        query = query.strip("<>")
        if not re.match(URL_REGEX, query):
            query = f"ytsearch:{query}"
        await player.add_tracks(ctx, await self.wavelink.get_tracks(query))

    @commands.command()
    async def pause(self, ctx):
        """Pause the currently playing song."""
        player = self.get_player(ctx)

        if player.is_paused or not player.is_connected:
            return await ctx.error("The player is either not playing or already paused.", 10)

        await ctx.embed(f"**{ctx.author}** has paused the player.")
        await player.set_pause(True)

    @commands.command()
    async def resume(self, ctx):
        """Resume a currently paused player."""
        player = self.get_player(ctx)

        if not player.is_paused or not player.is_connected:
            return await ctx.error("The player isn't paused.", 10)

        await ctx.embed(f"**{ctx.author}** has resumed the player.")
        await player.set_pause(False)

    @commands.command()
    async def skip(self, ctx):
        """Skip the currently playing song."""
        player = self.get_player(ctx)

        if not player.queue.upcoming:
            raise NoMoreTracks

        await player.stop()
        await ctx.send("Skipping...")

    @commands.command()
    async def previous(self, ctx):
        """Play the previously played song."""
        player = self.get_player(ctx)

        if not player.queue.history:
            raise NoPreviousTracks

        player.queue.position -= 2
        await player.stop()
        await ctx.embed("Playing previous track in queue.")

    @commands.command()
    async def stop(self, ctx):
        """Stop the player and clear all internal states."""
        player = self.get_player(ctx)
        player.queue.empty()
        await player.stop()
        await ctx.embed("Player stopped.")

    @commands.command(aliases=["leave"])
    async def disconnect(self, ctx):
        player = self.get_player(ctx)
        await player.teardown()
        await ctx.embed("Disconnected.")

    @commands.command(name="repeat")
    async def repeat(self, ctx, mode: str):
        """Set the repeat to none, 1 and all."""

        player = self.get_player(ctx)
        player.queue.set_repeat_mode(mode)
        await ctx.embed(f"The repeat mode has been set to {mode}.")

    @commands.command(aliases=["v", "vol"])
    async def volume(self, ctx, *, vol):
        """Change the players volume, between 1 and 100."""
        player = self.get_player(ctx)

        if not player.is_connected:
            return

        if not self.is_privileged(ctx):
            return await ctx.error("Only the DJ or admins may change the volume.", 10)

        if not 0 < vol < 101:
            return await ctx.error("Please enter a value between 1 and 100.", 10)

        await player.set_volume(vol)
        await ctx.embed(f"Set the volume to **{vol}**%.")

    @commands.command(aliases=["mix"])
    async def shuffle(self, ctx):
        """Shuffle the players queue."""
        player = self.get_player(ctx)
        player.queue.shuffle()
        await ctx.embed("Queue shuffled.")

    @commands.group(name="queue", aliases=["q"], invoke_without_command=True)
    async def queue(self, ctx, show: int = 10):
        """Displays the current songs that are queued."""

        player = self.get_player(ctx)

        if not player.is_connected:
            return

        if player.queue.length == 0:
            return await ctx.embed("There are no more songs in the queue...")

        track = player.queue.current_track

        final_string = []
        titles = [track.title for track in player.queue.upcoming[:show]]
        uris = [track.uri for track in player.queue.upcoming[:show]]
        requester = [track.requester.name for track in player.queue.upcoming[:show]]

        if len(titles) <= 10:
            upper_limit = len(titles)
        else:
            upper_limit = 10

        for i in range(0, upper_limit):
            final_string.append(f"{i + 1}. [{titles[i]}]({uris[i]}) | Requested by: {requester[i]}\n")

        embed = Embed(ctx, title=f"Queue for {ctx.channel.name}")
        embed.add_field (name="Now Playing:\n", value=f"[{track.title}]({track.uri}) | Requested by: {track.requester.name}\n", inline=False)

        embed.add_field(name="Up next:\n", value="\n".join(
            f"{string}" for string in final_string), inline=False)

            # embed.add_field(name=f"{len(player.queue._queue)} songs in queue.", value="\u200b")
        await ctx.send(embed=embed)

    @queue.command(aliases=["m"])
    async def move(self, ctx, entry: int, new_position: int):
        """Move a queue entry to a new position."""

        player = self.get_player(ctx)

        if not player.is_connected:
            return

        if player.queue.qsize() == 0:
            return await ctx.error("There are no songs in the queue...", 10)

        if not player.queue.upcoming[entry - 1]:
            return await ctx.error("This entry doesn't exists...", 10)

        tmp = player.queue.upcoming[new_position - 1]

        player.queue.upcoming[new_position - 1] = player.queue.upcoming[entry - 1]

        player.queue.upcoming[entry - 1] = tmp

        await ctx.embed("Song successfully moved.")

    @commands.command(aliases=["eq"])
    async def equalizer(self, ctx, *, equalizer):
        """Change the players equalizer."""
        player = self.get_player(ctx)

        if not player.is_connected:
            return

        if not self.is_privileged(ctx):
            return await ctx.error("Only the DJ or admins may change the equalizer.", 10)

        eqs = {
            "flat": wavelink.Equalizer.flat(),
            "boost": wavelink.Equalizer.boost(),
            "metal": wavelink.Equalizer.metal(),
            "piano": wavelink.Equalizer.piano(),
        }

        eq = eqs.get(equalizer.lower(), None)

        if not eq:
            joined = "\n".join(eqs.keys())
            return await ctx.error(f"Invalid EQ provided. Valid EQs:\n\n{joined}", 10)

        await ctx.embed(f"Successfully changed equalizer to {equalizer}.")
        await player.set_eq(eq)

    @commands.command(aliases=["np", "now_playing", "current"])
    async def nowplaying(self, ctx):
        """Update the player controller."""
        player = self.get_player(ctx)

        if not player.is_connected:
            return

        track = player.queue.current_track
        if not track:
            return

        channel = ctx.message.channel

        embed = Embed(
            ctx=ctx,
            title=f"{channel.name}",
            description=f"Now Playing:\n**`{track.title}`**\n\n",
            thumbnail=track.thumb,
        )

        if track.is_stream:
            embed.add_field(name="Duration", value="🔴Streaming")
        else:
            embed.add_field(
                name="Duration",
                value=str(datetime.timedelta(milliseconds=int(track.length))),
            )
        embed.add_fields(
            ("Queue Length:", str(player.queue.length)),
            ("Volume:", str(player.volume)),
            ("Requested by:", track.requester.name),
            ("Video URL:", f"[Click Here!]({track.uri})"),
        )

        await ctx.send(embed=embed)

    @commands.command(aliases=["swap"])
    async def swapdj(self, ctx, *, member=None):
        """Swap the current DJ to another member in the voice channel."""
        player = self.get_player(ctx)

        if not player.is_connected:
            return

        if not self.is_privileged(ctx):
            return await ctx.error("Only admins and the DJ may use this command.", 10)

        members = self.bot.get_channel(int(player.channel_id)).members

        if member and member not in members:
            return await ctx.error(
                f"{member} != currently in voice, so can not be a DJ.", 10
            )

        if member and member == player.dj:
            return await ctx.error(f"**{member}** is already the DJ.", 10)

        if len(members) <= 2:
            return await ctx.error("There are no other members to swap DJ to.", 10)

        if member:
            player.dj = member
            return await ctx.embed(f"**{member}** is now the DJ.")

        for m in members:
            if m == player.dj or m.bot:
                continue
            else:
                player.dj = m
                return await ctx.embed(f"**{member}** is now the DJ.")

    @commands.command(name="wavelinkinfo", aliases=["wvi"])
    async def wavelinkinfo(self, ctx):
        """Retrieve various Music / WaveLink information."""
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass
        player = self.get_player(ctx)
        node = player.node

        used = humanize.naturalsize(node.stats.memory_used)
        total = humanize.naturalsize(node.stats.memory_allocated)
        free = humanize.naturalsize(node.stats.memory_free)
        cpu = node.stats.cpu_cores
        embed = Embed(
            ctx,
            title="Wavelink Info",
            description=f"Wavelink version: {wavelink.__version__}",
        )
        embed.add_fields(
            ("Connected Nodes:", str(len(self.wavelink.nodes))),
            ("Best available Node:", self.wavelink.get_best_node().__repr__()),
            ("Players on this server:", str(node.stats.playing_players)),
            ("Server Memory:", f"{used}/{total} | ({free} free)"),
            ("Server CPU Cores:", str(cpu)),
            ("Server Uptime:", str(datetime.timedelta(milliseconds=node.stats.uptime))),
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Music(bot))
