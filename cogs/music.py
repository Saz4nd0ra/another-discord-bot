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
from .utils.embed import Embed
from .utils.context import Context
from discord.ext import commands, menus

# URL matching REGEX...
URL_REG = re.compile(r"https?://(?:www\.)?.+")

log = logging.getLogger(__name__)


class Track(wavelink.Track):
    """Wavelink Track object with a requester attribute."""

    __slots__ = "requester"

    def __init__(self, *args, **kwargs):
        super().__init__(*args)

        self.requester = kwargs.get("requester")


class Player(wavelink.Player):
    """Custom wavelink Player class."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.context = kwargs.get("context", None)
        if self.context:
            self.dj = self.context.author

        self.queue = asyncio.Queue()
        self.controller = None

        self.waiting = False
        self.updating = False

        self.skip_votes = set()

    async def do_next(self):
        if self.is_playing or self.waiting:
            return

        # Clear the votes for a new song...
        self.skip_votes.clear()

        try:
            self.waiting = True
            with async_timeout.timeout(60):
                track = await self.queue.get()
        except asyncio.TimeoutError:
            # No music has been played for 5 minutes, cleanup and disconnect...
            return await self.teardown()

        await self.play(track)
        self.waiting = False

        # Invoke our players controller...
        await self.invoke_controller()

    async def invoke_controller(self):
        """Method which updates or sends a new player controller."""
        if self.updating:
            return

        self.updating = True

        if not self.controller:
            self.controller = InteractiveMessage(embed=self.build_embed(), player=self)
            await self.controller.start(self.context)

        elif not await self.is_position_fresh():
            try:
                await self.controller.message.delete()
            except discord.HTTPException:
                pass

            self.controller.stop()

            self.controller = InteractiveMessage(embed=self.build_embed(), player=self)
            await self.controller.start(self.context)

        else:
            embed = self.build_embed()
            await self.controller.message.edit(content=None, embed=embed)

        self.updating = False

    def build_embed(self):
        """Method which builds our players controller embed."""
        track = self.current
        if not track:
            return

        channel = self.bot.get_channel(int(self.channel_id))
        qsize = self.queue.qsize()

        embed = Embed(
            ctx=self.context,
            title=f"Music Controller | {channel.name}",
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
            ("Queue Length:", str(qsize)),
            ("Volume:", str(self.volume)),
            ("Requested by:", track.requester.name),
            ("Current DJ:", self.dj.name),
            ("Video URL:", f"[Click Here!]({track.uri})"),
        )

        return embed

    async def is_position_fresh(self):
        """Method which checks whether the player controller should be remade or updated."""
        try:
            async for message in self.context.channel.history(limit=5):
                if message.id == self.controller.message.id:
                    return True
        except (discord.HTTPException, AttributeError):
            return False

        return False

    async def teardown(self):
        """Clear internal states, remove player controller and disconnect."""
        try:
            await self.controller.message.delete()
        except discord.HTTPException:
            pass

        self.controller.stop()

        try:
            await self.destroy()
        except KeyError:
            pass


class InteractiveMessage(menus.Menu):
    """The Players interactive controller menu class."""

    def __init__(self, *, embed, player):
        super().__init__(timeout=None)

        self.embed = embed
        self.player = player

    def update_context(self, payload):
        """Update our context with the user who reacted."""
        ctx = copy.copy(self.ctx)
        ctx.author = payload.member

        return ctx

    def reaction_check(self, payload):
        if payload.event_type == "REACTION_REMOVE":
            return False

        if not payload.member:
            return False
        if payload.member.bot:
            return False
        if payload.message_id != self.message.id:
            return False
        if (
            payload.member
            not in self.bot.get_channel(int(self.player.channel_id)).members
        ):
            return False

        return payload.emoji in self.buttons

    async def send_initial_message(self, ctx, channel):
        return await channel.send(embed=self.embed)

    @menus.button(emoji="\u25B6")
    async def resume_command(self, payload):
        """Resume button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command("resume")
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji="\u23F8")
    async def pause_command(self, payload):
        """Pause button"""
        ctx = self.update_context(payload)

        command = self.bot.get_command("pause")
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji="\u23F9")
    async def stop_command(self, payload):
        """Stop button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command("stop")
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji="\u23ED")
    async def skip_command(self, payload):
        """Skip button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command("skip")
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji="\U0001F500")
    async def shuffle_command(self, payload):
        """Shuffle button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command("shuffle")
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji="\u2795")
    async def volup_command(self, payload):
        """Volume up button"""
        ctx = self.update_context(payload)

        command = self.bot.get_command("vol_up")
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji="\u2796")
    async def voldown_command(self, payload):
        """Volume down button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command("vol_down")
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji="\U0001F1F6")
    async def queue_command(self, payload):
        """Player queue button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command("queue")
        ctx.command = command

        await self.bot.invoke(ctx)


class Music(commands.Cog, wavelink.WavelinkMixin):
    """The obligatory Music cog."""

    def __init__(self, bot):
        self.bot = bot
        self.config = self.bot.config

        if not hasattr(bot, "wavelink"):
            bot.wavelink = wavelink.Client(bot=bot)

        bot.loop.create_task(self.start_nodes())

    async def start_nodes(self):
        """Connect and intiate nodes."""
        await self.bot.wait_until_ready()

        if self.bot.wavelink.nodes:
            previous = self.bot.wavelink.nodes.copy()

            for node in previous.values():
                await node.destroy()

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

        for n in nodes.values():
            await self.bot.wavelink.initiate_node(**n)

    @wavelink.WavelinkMixin.listener()
    async def on_node_ready(self, node):
        log.info(f"Node {node.identifier} is ready!")

    @wavelink.WavelinkMixin.listener("on_track_stuck")
    @wavelink.WavelinkMixin.listener("on_track_end")
    @wavelink.WavelinkMixin.listener("on_track_exception")
    async def on_player_stop(self, node, payload):
        await payload.player.do_next()

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if member.bot:
            return

        player: Player = self.bot.wavelink.get_player(member.guild.id, cls=Player)

        if not player.channel_id or not player.context:
            player.node.players.pop(member.guild.id)
            return

        channel = self.bot.get_channel(int(player.channel_id))

        if len(channel.members) == 1:
            return await player.teardown()

        if member == player.dj and after.channel is None:
            for m in channel.members:
                if m.bot:
                    continue
                else:
                    player.dj = m
                    return

        elif after.channel == channel and player.dj not in channel.members:
            player.dj = member

    async def cog_check(self, ctx):
        """Cog wide check, which disallows commands in DMs."""
        if not ctx.guild:
            await ctx.error("Music commands are not available in Private Messages.")
            return False

        return True

    async def cog_before_invoke(self, ctx):
        """Coroutine called before command invocation."""
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player, context=ctx)

        if player.context:
            if player.context.channel != ctx.channel:
                await ctx.error(
                    f"**{ctx.author}**, you must be in {player.context.channel} for this session.",
                    10,
                )

        if ctx.command.name == "connect" and not player.context:
            return
        elif self.is_privileged(ctx):
            return

        if not player.channel_id:
            return

        channel = self.bot.get_channel(int(player.channel_id))
        if not channel:
            return

        if player.is_connected:
            if ctx.author not in channel.members:
                await ctx.error(
                    f"**{ctx.author}**, you must be in `{channel.name}` to use voice commands.",
                    10,
                )

    def required(self, ctx):
        """Method which returns required votes based on amount of members in a channel."""
        player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )
        channel = self.bot.get_channel(int(player.channel_id))
        required = math.ceil((len(channel.members) - 1) / 2.5)

        if ctx.command.name == "stop":
            if len(channel.members) - 1 == 2:
                required = 2

        return required

    def is_privileged(self, ctx):
        """Check whether the user is an Admin or DJ."""
        player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        return player.dj == ctx.author or ctx.author.guild_permissions.kick_members

    @commands.command()
    async def connect(self, ctx, *, channel=None):
        """Connect to a voice channel."""
        player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if player.is_connected:
            return

        channel = getattr(ctx.author.voice, "channel", channel)
        if channel is None:
            return await ctx.error("No channel provided!")

        await player.connect(channel.id)

    @commands.command(aliases=["p"])
    async def play(self, ctx, *, query):
        """Play or queue a song with the given query."""
        player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if not player.is_connected:
            await ctx.invoke(self.connect)

        query = query.strip("<>")
        if not URL_REG.match(query):
            query = f"ytsearch:{query}"

        tracks = await self.bot.wavelink.get_tracks(query)
        if not tracks:
            return await ctx.error(
                "No songs were found with that query. Please try again."
            )

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
            await ctx.embed(f"`Added {track.title} to the Queue\n`")
            await player.queue.put(track)

        if not player.is_playing:
            await player.do_next()

    @commands.command()
    async def pause(self, ctx):
        """Pause the currently playing song."""
        player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if player.is_paused or not player.is_connected:
            return

        await ctx.embed(f"**{ctx.author}** has paused the player.")
        await player.set_pause(True)

    @commands.command()
    async def resume(self, ctx):
        """Resume a currently paused player."""
        player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if not player.is_paused or not player.is_connected:
            return

        await ctx.embed(f"**{ctx.author}** has resumed the player.")
        return await player.set_pause(False)

    @commands.command()
    async def skip(self, ctx):
        """Skip the currently playing song."""
        player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if not player.is_connected:
            return

        if self.is_privileged(ctx):
            await ctx.embed("A priviliged user skipped the song.")
            player.skip_votes.clear()

            return await player.stop()

        if ctx.author == player.current.requester:
            await ctx.embed("The song requester has skipped the song.")
            player.skip_votes.clear()

            return await player.stop()

        required = self.required(ctx)
        player.skip_votes.add(ctx.author)

        if len(player.skip_votes) >= required:
            await ctx.embed("Vote to skip passed. Skipping song.")
            player.skip_votes.clear()
            await player.stop()
        else:
            await ctx.embed(f"**{ctx.author}** has voted to skip the song.")

    @commands.command()
    async def stop(self, ctx):
        """Stop the player and clear all internal states."""
        player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if not player.is_connected:
            return

        await ctx.embed(f"**{ctx.author}** stopped the player.")
        return await player.teardown()

    @commands.command(aliases=["v", "vol"])
    async def volume(self, ctx, *, vol):
        """Change the players volume, between 1 and 100."""
        player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if not player.is_connected:
            return

        if not self.is_privileged(ctx):
            return await ctx.error("Only the DJ or admins may change the volume.")

        if not 0 < vol < 101:
            return await ctx.error("Please enter a value between 1 and 100.")

        await player.set_volume(vol)
        await ctx.embed(f"Set the volume to **{vol}**%.")

    @commands.command(aliases=["mix"])
    async def shuffle(self, ctx):
        """Shuffle the players queue."""
        player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if not player.is_connected:
            return

        if player.queue.qsize() < 3:
            return await ctx.error("Add more songs to the queue before shuffling.")

        await ctx.embed(f"**{ctx.author}** has shuffled the playlist.")
        return random.shuffle(player.queue._queue)

    @commands.command(hidden=True)
    async def vol_up(self, ctx):
        """Command used for volume up button."""
        player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if not player.is_connected or not self.is_privileged(ctx):
            return

        vol = int(math.ceil((player.volume + 10) / 10)) * 10

        if vol > 100:
            vol = 100
            await ctx.error("Maximum volume reached")

        await player.set_volume(vol)

    @commands.command(hidden=True)
    async def vol_down(self, ctx):
        """Command used for volume down button."""
        player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if not player.is_connected or not self.is_privileged(ctx):
            return

        vol = int(math.ceil((player.volume - 10) / 10)) * 10

        if vol < 0:
            vol = 0
            await ctx.error("Player is currently muted.")

        await player.set_volume(vol)

    @commands.command(aliases=["eq"])
    async def equalizer(self, ctx, *, equalizer):
        """Change the players equalizer."""
        player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if not player.is_connected:
            return

        if not self.is_privileged(ctx):
            return await ctx.error("Only the DJ or admins may change the equalizer.")

        eqs = {
            "flat": wavelink.Equalizer.flat(),
            "boost": wavelink.Equalizer.boost(),
            "metal": wavelink.Equalizer.metal(),
            "piano": wavelink.Equalizer.piano(),
        }

        eq = eqs.get(equalizer.lower(), None)

        if not eq:
            joined = "\n".join(eqs.keys())
            return await ctx.error(f"Invalid EQ provided. Valid EQs:\n\n{joined}")

        await ctx.embed(f"Successfully changed equalizer to {equalizer}.")
        await player.set_eq(eq)

    @commands.group(name="queue", invoke_without_command=True)
    async def queue(self, ctx):
        """Displays the current songs that are queued."""

        player: Player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player, context=ctx)

        if not player.is_connected:
            return

        if player.queue.qsize() == 0:
            return await ctx.embed("There are no more songs in the queue...")

        track = player.current

        final_string = []
        titles = [track.title for track in player.queue._queue]
        uris = [track.uri for track in player.queue._queue]
        requester = [track.requester.name for track in player.queue._queue]

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

        player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_connected:
            return

        if player.queue.qsize() == 0:
            return await ctx.error("There are no songs in the queue...")

        if not player.queue._queue[entry - 1]:
            return await ctx.error("This entry doesn't exists...")

        tmp = player.queue._queue[new_position - 1]

        player.queue._queue[new_position - 1] = player.queue._queue[entry - 1]

        player.queue._queue[entry - 1] = tmp

        await ctx.embed("Song successfully moved.")

    @queue.command()
    async def clear(self, ctx):
        """Clear the queue."""

        player: Player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player, context=ctx)

        if player.queue.qsize() == 0:
            return await ctx.error("There are no songs in the queue...")

        player.queue._queue = []

        await ctx.embed("Queue successfully cleared.")

    @commands.command(aliases=["np", "now_playing", "current"])
    async def nowplaying(self, ctx):
        """Update the player controller."""
        player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if not player.is_connected:
            return

        await player.invoke_controller()

    @commands.command(aliases=["swap"])
    async def swapdj(self, ctx, *, member=None):
        """Swap the current DJ to another member in the voice channel."""
        player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if not player.is_connected:
            return

        if not self.is_privileged(ctx):
            return await ctx.error("Only admins and the DJ may use this command.")

        members = self.bot.get_channel(int(player.channel_id)).members

        if member and member not in members:
            return await ctx.error(
                f"{member} != currently in voice, so can not be a DJ."
            )

        if member and member == player.dj:
            return await ctx.error(f"**{member}** is already the DJ.")

        if len(members) <= 2:
            return await ctx.error("There are no other members to swap DJ to.")

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
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)
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
            ("Connected Nodes:", str(len(self.bot.wavelink.nodes))),
            ("Best available Node:", self.bot.wavelink.get_best_node().__repr__()),
            ("Players on this server:", str(node.stats.playing_players)),
            ("Server Memory:", f"{used}/{total} | ({free} free)"),
            ("Server CPU Cores:", str(cpu)),
            ("Server Uptime:", str(datetime.timedelta(milliseconds=node.stats.uptime))),
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Music(bot))
