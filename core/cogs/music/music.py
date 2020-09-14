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
from ...utils.exceptions import *
from ...utils.embed import Embed
from ...utils.context import Context
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
            with async_timeout.timeout(300):
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
            ("Requested by:", track.requester.mention),
            ("Current DJ:", self.dj.mention),
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

    def update_context(self, payload: discord.RawReactionActionEvent):
        """Update our context with the user who reacted."""
        ctx = copy.copy(self.ctx)
        ctx.author = payload.member

        return ctx

    def reaction_check(self, payload: discord.RawReactionActionEvent):
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

    async def send_initial_message(self, ctx, channel: discord.TextChannel):
        return await channel.send(embed=self.embed)

    @menus.button(emoji="\u25B6")
    async def resume_command(self, payload: discord.RawReactionActionEvent):
        """Resume button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command("resume")
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji="\u23F8")
    async def pause_command(self, payload: discord.RawReactionActionEvent):
        """Pause button"""
        ctx = self.update_context(payload)

        command = self.bot.get_command("pause")
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji="\u23F9")
    async def stop_command(self, payload: discord.RawReactionActionEvent):
        """Stop button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command("stop")
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji="\u23ED")
    async def skip_command(self, payload: discord.RawReactionActionEvent):
        """Skip button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command("skip")
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji="\U0001F500")
    async def shuffle_command(self, payload: discord.RawReactionActionEvent):
        """Shuffle button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command("shuffle")
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji="\u2795")
    async def volup_command(self, payload: discord.RawReactionActionEvent):
        """Volume up button"""
        ctx = self.update_context(payload)

        command = self.bot.get_command("vol_up")
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji="\u2796")
    async def voldown_command(self, payload: discord.RawReactionActionEvent):
        """Volume down button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command("vol_down")
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji="\U0001F1F6")
    async def queue_command(self, payload: discord.RawReactionActionEvent):
        """Player queue button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command("queue")
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji="\U0001F501")
    async def repeat_command(self, payload: discord.RawReactionActionEvent):
        """Player queue button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command("repeat")
        ctx.command = command

        await self.bot.invoke(ctx)


class PaginatorSource(menus.ListPageSource):
    """Player queue paginator class."""

    def __init__(self, entries, *, per_page=8):
        super().__init__(entries, per_page=per_page)

    async def format_page(self, menu: menus.Menu, page):
        embed = discord.Embed(title="Coming Up...", colour=0x4F0321)
        embed.description = "\n".join(
            f"`{index}. {title}`" for index, title in enumerate(page, 1)
        )

        return embed

    def is_paginating(self):
        # We always want to embed even on 1 page of results...
        return True


class Music(commands.Cog, wavelink.WavelinkMixin):
    """Listen to Music with friends."""

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
                "identifier": "MAIN",
                "region": "eu",
            }
        }

        for n in nodes.values():
            await self.bot.wavelink.initiate_node(**n)

    @wavelink.WavelinkMixin.listener()
    async def on_node_ready(self, node: wavelink.Node):
        log.info(f"Node {node.identifier} is ready!")

    @wavelink.WavelinkMixin.listener("on_track_stuck")
    @wavelink.WavelinkMixin.listener("on_track_end")
    @wavelink.WavelinkMixin.listener("on_track_exception")
    async def on_player_stop(self, node: wavelink.Node, payload):
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

        player = self.bot.wavelink.get_player(member.guild.id, cls=Player)

        if not player.channel_id or not player.context:
            player.node.players.pop(member.guild.id)
            return

        channel = self.bot.get_channel(int(player.channel_id))

        if member == player.dj and after.channel == None:
            for m in channel.members:
                if m.bot:
                    continue
                else:
                    player.dj = m
                    return

        elif after.channel == channel and player.dj not in channel.members:
            player.dj = member

    async def cog_command_error(self, ctx, error: Exception):
        """Cog wide error handler."""
        if isinstance(error, IncorrectChannelError):
            return

        if isinstance(error, NoChannelProvided):
            return await ctx.error(
                "You must be in a voice channel or provide one to connect to.", 10
            )

    async def cog_check(self, ctx):
        """Cog wide check, which disallows commands in DMs."""
        if not ctx.guild:
            await ctx.error("Music commands are not available in Private Messages.", 10)
            return False

        return True

    async def cog_before_invoke(self, ctx):
        """Coroutine called before command invocation."""
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player, context=ctx)

        if player.context:
            if player.context.channel != ctx.channel:
                await ctx.error(
                    f"{ctx.author.mention}, you must be in {player.context.channel.mention} for this session.",
                    10,
                )
                raise IncorrectChannelError

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
                    f"{ctx.author.mention}, you must be in `{channel.name}` to use voice commands.",
                    10,
                )
                raise IncorrectChannelError

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
    async def connect(self, ctx, *, channel: discord.VoiceChannel = None):
        """Connect to a voice channel."""
        player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if player.is_connected:
            return

        channel = getattr(ctx.author.voice, "channel", channel)
        if channel == None:
            raise NoChannelProvided

        await player.connect(channel.id)

    @commands.command()
    async def play(self, ctx, *, query: str):
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
                "No songs were found with that query. Please try again.",
                15,
            )

        if isinstance(tracks, wavelink.TrackPlaylist):
            for track in tracks.tracks:
                track = Track(track.id, track.info, requester=ctx.author)
                await player.queue.put(track)

            await ctx.embed(
                f'```ini\nAdded the playlist {tracks.data["playlistInfo"]["name"]}'
                f" with {len(tracks.tracks)} songs to the queue.\n```",
                15,
            )
        else:
            track = Track(tracks[0].id, tracks[0].info, requester=ctx.author)
            await ctx.embed(f"```ini\nAdded {track.title} to the Queue\n```", 15)
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

        await ctx.embed(f"{ctx.author.mention} has resumed the player.", 15)
        await player.set_pause(True)

    @commands.command()
    async def resume(self, ctx):
        """Resume a currently paused player."""
        player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if not player.is_paused or not player.is_connected:
            return

        await ctx.embed(f"{ctx.author.mention} has resumed the player.", 15)
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
            await ctx.embed("An admin or DJ has skipped the song.", delete_after=10)
            player.skip_votes.clear()

            return await player.stop()

        if ctx.author == player.current.requester:
            await ctx.embed("The song requester has skipped the song.", delete_after=10)
            player.skip_votes.clear()

            return await player.stop()

        required = self.required(ctx)
        player.skip_votes.add(ctx.author)

        if len(player.skip_votes) >= required:
            await ctx.embed("Vote to skip passed. Skipping song.", delete_after=10)
            player.skip_votes.clear()
            await player.stop()
        else:
            await ctx.embed(
                f"{ctx.author.mention} has voted to skip the song.", delete_after=15
            )

    @commands.command()
    async def stop(self, ctx):
        """Stop the player and clear all internal states."""
        player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if not player.is_connected:
            return

        await ctx.embed(f"{ctx.author.mention} stopped the player.", 10)
        return await player.teardown()

    @commands.command(aliases=["v", "vol"])
    async def volume(self, ctx, *, vol: int):
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
        await ctx.embed(f"Set the volume to **{vol}**%", delete_after=7)

    @commands.command(aliases=["mix"])
    async def shuffle(self, ctx):
        """Shuffle the players queue."""
        player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if not player.is_connected:
            return

        if player.queue.qsize() < 3:
            return await ctx.error("Add more songs to the queue before shuffling.", 15)

        await ctx.embed(f"{ctx.author.mention} has shuffled the playlist.", 10)
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
            await ctx.error("Maximum volume reached", delete_after=7)

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
            await ctx.error("Player is currently muted", 10)

        await player.set_volume(vol)

    @commands.command(aliases=["eq"])
    async def equalizer(self, ctx, *, equalizer: str):
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

        await ctx.embed(f"Successfully changed equalizer to {equalizer}", 15)
        await player.set_eq(eq)

    @commands.command(aliases=["q"])
    async def queue(self, ctx):
        """Display the players queued songs."""
        player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if not player.is_connected:
            return

        if player.queue.qsize() == 0:
            return await ctx.error("There are no more songs in the queue.", 15)

        entries = [track.title for track in player.queue._queue]
        pages = PaginatorSource(entries=entries)
        paginator = menus.MenuPages(
            source=pages, timeout=None, delete_message_after=True
        )

        await paginator.start(ctx)

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
    async def swap_dj(self, ctx, *, member: discord.Member = None):
        """Swap the current DJ to another member in the voice channel."""
        player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if not player.is_connected:
            return

        if not self.is_privileged(ctx):
            return await ctx.error("Only admins and the DJ may use this command.", 15)

        members = self.bot.get_channel(int(player.channel_id)).members

        if member and member not in members:
            return await ctx.error(
                f"{member} != currently in voice, so can not be a DJ.", 15
            )

        if member and member == player.dj:
            return await ctx.error("Cannot swap DJ to the current DJ... :)", 15)

        if len(members) <= 2:
            return await ctx.error("No more members to swap to.", 15)

        if member:
            player.dj = member
            return await ctx.embed(f"{member.mention} is now the DJ.")

        for m in members:
            if m == player.dj or m.bot:
                continue
            else:
                player.dj = m
                return await ctx.embed(f"{member.mention} is now the DJ.")

    @commands.command(name="repeat", aliases=["replay"])
    async def repeat_(self, ctx):
        """Repeat the currently playing song."""
        player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )
        if not player.is_connected:
            return

        return await self.do_repeat(ctx)

    async def do_repeat(self, ctx):
        player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )
        if not player.queue.entries:
            player.queue.put(player.current)
        else:
            player.queue.put_left(player.current)

        player.update = True

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
        e = Embed(
            ctx,
            title="Wavelink Info",
            description=f"Wavelink version: {wavelink.__version__}",
        )
        e.add_fields(
            ("Connected Nodes:", str(len(self.bot.wavelink.nodes))),
            ("Best available Node:", self.bot.wavelink.get_best_node().__repr__()),
            ("Players on this server:", str(node.stats.playing_players)),
            ("Server Memory:", f"{used}/{total} | ({free} free)"),
            ("Server CPU Cores:", str(cpu)),
            ("Server Uptime:", str(datetime.timedelta(milliseconds=node.stats.uptime))),
        )
        await ctx.send(embed=e, delete_after=10)


def setup(bot: commands.Bot):
    bot.add_cog(Music(bot))
