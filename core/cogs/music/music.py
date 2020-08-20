import asyncio
import datetime
import discord
import itertools
import math
import random
import re
import wavelink
from discord.ext import commands
from typing import Union
import humanize
from ...utils.embed import Embed

RURL = re.compile(r"https?:\/\/(?:www\.)?.+")


class Track(wavelink.Track):
    __slots__ = ("requester", "channel", "message")

    def __init__(self, id_, info, *, ctx=None):
        super(Track, self).__init__(id_, info)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.message = ctx.message

    @property
    def is_dead(self):
        return self.dead


class Queue(asyncio.Queue):
    def queue(self):
        if hasattr(self, "_queue"):
            return self._queue
        else:
            return []


class Player(wavelink.Player):
    def __init__(self, bot, guild_id: int, node: wavelink.Node):
        super(Player, self).__init__(bot, guild_id, node)

        self.queue = Queue()
        self.next_event = asyncio.Event()

        self.volume = 50
        self.dj = None
        self.controller_message = None
        self.reaction_task = None
        self.update = False
        self.updating = False
        self.inactive = False

        self.controls = {
            "⏯": "rp",
            "⏹": "stop",
            "⏭": "skip",
            "🔀": "shuffle",
            "🔂": "repeat",
            "➕": "vol_up",
            "➖": "vol_down",
            "ℹ": "queue",
        }

        bot.loop.create_task(self.player_loop())
        bot.loop.create_task(self.updater())

    @property
    def entries(self):
        return list(self.queue.queue())

    async def updater(self):
        while not self.bot.is_closed():
            if self.update and not self.updating:
                self.update = False
                await self.invoke_controller()

            await asyncio.sleep(10)

    async def player_loop(self):
        await self.bot.wait_until_ready()

        await self.set_eq(wavelink.Equalizer.flat())
        # We can do any pre loop prep here..
        await self.set_volume(self.volume)

        while True:
            self.next_event.clear()

            self.inactive = False

            song = await self.queue.get()
            if not song:
                continue

            self.current = song
            self.paused = False

            await self.play(song)

            # Invoke our controller if we aren't already..
            if not self.update:
                await self.invoke_controller()

            # Wait for TrackEnd event to set our event..
            await self.next_event.wait()

    async def invoke_controller(self, track: wavelink.Track = None):
        """Invoke our controller message, and spawn a reaction controller if one isn't alive."""
        if not track:
            track = self.current

        self.updating = True

        embed = Embed(
            title="Music Controller",
            description=f"Now Playing:\n[{track.title}]({track.uri})",
        )
        embed.set_thumbnail(url=track.thumb)

        if track.is_stream:
            embed.add_field(name="Duration", value="🔴`Streaming`")
        else:
            embed.add_field(
                name="Duration",
                value=str(datetime.timedelta(milliseconds=int(track.length))),
            )
        embed.add_field(name="Queue Length", value=str(len(self.entries)))
        embed.add_field(name="Volume", value=f"{self.volume}%")

        if len(self.entries) > 0:
            data = "\n".join(
                f'**-** `{t.title[0:45]}{".." if len(t.title) > 45 else ""}`\n{"-"*10}'
                for t in itertools.islice(
                    [e for e in self.entries if not e.is_dead], 0, 3, None
                )
            )
            embed.add_field(name="Coming Up:", value=data, inline=False)

        if not await self.is_current_fresh(track.channel) and self.controller_message:
            try:
                await self.controller_message.delete()
            except discord.HTTPException:
                pass

            self.controller_message = await track.channel.send(embed=embed)
        elif not self.controller_message:
            self.controller_message = await track.channel.send(embed=embed)
        else:
            self.updating = False
            return await self.controller_message.edit(embed=embed, content=None)

        try:
            self.reaction_task.cancel()
        except Exception:
            pass

        self.reaction_task = self.bot.loop.create_task(self.reaction_controller())
        self.updating = False

    async def add_reactions(self):
        """Add reactions to our controller."""
        for reaction in self.controls:
            try:
                await self.controller_message.add_reaction(str(reaction))
            except discord.HTTPException:
                return

    async def reaction_controller(self):
        """Our reaction controller, attached to our controller.
        This handles the reaction buttons and it's controls.
        """
        self.bot.loop.create_task(self.add_reactions())

        def check(r, u):
            if not self.controller_message:
                return False
            elif str(r) not in self.controls.keys():
                return False
            elif u.id == self.bot.user.id or r.message.id != self.controller_message.id:
                return False
            elif u not in self.bot.get_channel(int(self.channel_id)).members:
                return False
            return True

        while self.controller_message:
            if self.channel_id is None:
                return self.reaction_task.cancel()

            react, user = await self.bot.wait_for("reaction_add", check=check)
            control = self.controls.get(str(react))

            if control == "rp":
                if self.paused:
                    control = "resume"
                else:
                    control = "pause"

            try:
                await self.controller_message.remove_reaction(react, user)
            except discord.HTTPException:
                pass
            cmd = self.bot.get_command(control)

            ctx = await self.bot.get_context(react.message)
            ctx.author = user

            try:
                if cmd.is_on_cooldown(ctx):
                    pass
                if not await self.invoke_react(cmd, ctx):
                    pass
                else:
                    self.bot.loop.create_task(ctx.invoke(cmd))
            except Exception as e:
                ctx.command = self.bot.get_command("reactcontrol")
                await cmd.dispatch_error(ctx=ctx, error=e)

        await self.destroy_controller()

    async def destroy_controller(self):
        """Destroy both the main controller and it's reaction controller."""
        try:
            await self.controller_message.delete()
            self.controller_message = None
        except (AttributeError, discord.HTTPException):
            pass

        try:
            self.reaction_task.cancel()
        except Exception:
            pass

    async def invoke_react(self, cmd, ctx):
        if not cmd._buckets.valid:
            return True

        if not (await cmd.can_run(ctx)):
            return False

        bucket = cmd._buckets.get_bucket(ctx)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            return False
        return True

    async def is_current_fresh(self, chan):
        """Check whether our controller is fresh in message history."""
        try:
            async for m in chan.history(limit=8):
                if m.id == self.controller_message.id:
                    return True
        except (discord.HTTPException, AttributeError):
            return False
        return False


# TODO implement spotify integration


class Spotify:
    def __init__(self):
        pass


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        if not hasattr(bot, "wavelink"):
            self.bot.wavelink = wavelink.Client(bot=bot)

        bot.loop.create_task(self.initiate_nodes())

    async def initiate_nodes(self):
        nodes = {
            "MAIN": {
                "host": self.bot.config.ll_host,
                "port": self.bot.config.ll_port,
                "rest_url": f"http://{self.bot.config.ll_host}:{self.bot.config.ll_port}",
                "password": self.bot.config.ll_passwd,
                "identifier": "MAIN",
                "region": "europe",
            }
        }

        for n in nodes.values():
            node = await self.bot.wavelink.initiate_node(
                host=n["host"],
                port=n["port"],
                rest_uri=n["rest_url"],
                password=n["password"],
                identifier=n["identifier"],
                region=n["region"],
                secure=False,
            )

            node.set_hook(self.event_hook)

    def event_hook(self, event):
        """Our event hook. Dispatched when an event occurs on our Node."""
        if isinstance(event, wavelink.TrackEnd):
            event.player.next_event.set()
        elif isinstance(event, wavelink.TrackException):
            print(event.error)

    @commands.command()
    async def connect(self, ctx, *, channel: discord.VoiceChannel = None):
        """Connect to voice.
        """
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                raise modules.errors.MissingChannel

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if player.is_connected:
            if ctx.author.voice.channel == ctx.guild.me.voice.channel:
                return

        await player.connect(channel.id)

    @commands.command(name="play")
    async def play(self, ctx, *, query: str):
        """Queue a song or playlist for playback.
        """
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

        await ctx.trigger_typing()

        await ctx.invoke(self.connect)
        query = query.strip("<>")

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            await ctx.invoke(self.connect)

        if not player.dj:
            player.dj = ctx.author

        if not RURL.match(query):
            query = f"ytsearch:{query}"

        tracks = await self.bot.wavelink.get_tracks(query)
        if not tracks:
            return await ctx.send(
                "No songs were found with that query. Please try again."
            )

        if isinstance(tracks, wavelink.TrackPlaylist):
            for t in tracks.tracks:
                await player.queue.put(Track(t.id, t.info, ctx=ctx))

            await ctx.send(
                f'```ini\nAdded the playlist \'{tracks.data["playlistInfo"]["name"]}\''
                f" with {len(tracks.tracks)} songs to the queue.\n```"
            )
        else:
            track = tracks[0]
            await ctx.send(
                f"```ini\nAdded '{track.title}' to the Queue\n```", delete_after=10
            )
            await player.queue.put(Track(track.id, track.info, ctx=ctx))

        if player.controller_message and player.is_playing:
            await player.invoke_controller()

    @commands.command(name="now_playing", aliases=["np", "now"])
    async def now_playing(self, ctx):
        """Invoke the player controller.
        """
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)
        if not player:
            return

        if not player.is_connected:
            return

        if player.updating or player.update:
            return

        await player.invoke_controller()

    @commands.command(name="pause")
    async def pause(self, ctx):
        """Pause the currently playing song.
        """
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)
        if not player:
            return

        if not player.is_connected:
            raise modules.errors.NotConnected

        if player.paused:
            return

        await ctx.send(f"{ctx.author.mention} has paused the song!", delete_after=10)
        return await self.do_pause(ctx)

    async def do_pause(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)
        player.paused = True
        await player.set_pause(True)

    @commands.command(name="resume")
    async def resume(self, ctx):
        """Resume a currently paused song.
        """
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            raise modules.errors.NotConnected

        if not player.paused:
            return

        await ctx.send(f"{ctx.author.mention} has resumed the song!", delete_after=10)
        return await self.do_resume(ctx)

    async def do_resume(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)
        await player.set_pause(False)

    @commands.command(name="skip")
    async def skip(self, ctx):
        """Skip the current song.
        """
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            raise modules.errors.NotConnected

        await ctx.send(f"{ctx.author.mention} has skipped the song!", delete_after=10)
        return await self.do_skip(ctx)

    async def do_skip(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        await player.stop()

    @commands.command(name="stop", aliases=["leave"])
    async def stop(self, ctx):
        """Stop the player, disconnect and clear the queue.
        """
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            raise modules.errors.NotConnected

        await ctx.send(f"{ctx.author.mention} has stopped the player.", delete_after=10)
        return await self.do_stop(ctx)

    async def do_stop(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        await player.destroy_controller()
        await player.disconnect()

    @commands.command(name="seek")
    async def seek(self, ctx, *, position: str):
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            raise modules.errors.NotConnected

        try:
            h, m, s = position.split(":")
        except ValueError:
            try:
                h = 0
                m, s = position.split(":")
            except ValueError:
                h, m = 0, 0
                s = position

        sec = int(h) * 3600 + int(m) * 60 + int(s)

        await player.seek(sec)
        await ctx.send(f"Set the position to **{h}:{m}:{s}**.")

    @commands.command(name="volume", aliases=["vol", "v"])
    async def volume(self, ctx, *, volume: int):
        """Change the player volume.
        """
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            raise modules.errors.NotConnected

        if not 0 <= volume <= 100:
            return await ctx.send("Please enter a value between 0 and 100.")

        await player.set_volume(volume)
        await ctx.send(f"Volume set to **{volume}**%!", delete_after=10)

        if not player.updating and not player.update:
            await player.invoke_controller()

    @commands.command(name="queue", aliases=["q"])
    async def queue(self, ctx):
        """Retrieve a list of currently queued songs.
        """
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            raise modules.errors.NotConnected

        upcoming = list(itertools.islice(player.entries, 0, 10))

        if not upcoming:
            return await ctx.send(
                "```\nNo more songs in the Queue!\n```", delete_after=10
            )

        fmt = "\n".join(f"**`{str(song)}`**" for song in upcoming)
        embed = Embed(title=f"Upcoming - Next {len(upcoming)}", description=fmt)

        await ctx.send(embed=embed)

    @commands.command(name="shuffle", aliases=["mix"])
    async def shuffle(self, ctx):
        """Shuffle the current queue.
        """
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            raise modules.errors.NotConnected

        if len(player.entries) < 3:
            return await ctx.send(
                "Please add more songs to the queue before trying to shuffle.",
                delete_after=10,
            )

        await ctx.send(
            f"{ctx.author.mention} has shuffled the playlist!", delete_after=10
        )
        return await self.do_shuffle(ctx)

    async def do_shuffle(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)
        random.shuffle(player.queue._queue)

        player.update = True

    @commands.command(name="repeat", aliases=["loop"])
    async def repeat(self, ctx):
        """Repeat the currently playing song.
        """
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            return

        await ctx.send(f"{ctx.author.mention} set the song on repeat!", delete_after=10)
        return await self.do_repeat(ctx)

    async def do_repeat(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.entries:
            await player.queue.put(player.current)
        else:
            player.queue._queue.appendleft(player.current)

        player.update = True

    @commands.command(name="vol_up", hidden=True)
    async def volume_up(self, ctx):
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            return

        vol = int(math.ceil((player.volume + 10) / 10)) * 10

        if vol > 100:
            vol = 100
            await ctx.send("Maximum volume reached!", delete_after=10)

        await player.set_volume(vol)
        await ctx.send(f"Volume set to **{vol}%**!")
        player.update = True

    @commands.command(name="vol_down", hidden=True)
    async def volume_down(self, ctx):
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            return

        vol = int(math.ceil((player.volume - 10) / 10)) * 10

        if vol < 0:
            vol = 0
            await ctx.send("Player is currently muted.", delete_after=10)

        await player.set_volume(vol)
        await ctx.send(f"Volume set to **{vol}%**!")
        player.update = True

    @commands.command()
    async def llinfo(self, ctx):
        """Retrieve various Music / WaveLink information.
        """
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

        fmt = (
            f"**WaveLink:** `{wavelink.__version__}`\n\n"
            f"Connected to `{len(self.bot.wavelink.nodes)}` nodes.\n"
            f"Best available Node `{self.bot.wavelink.get_best_node().__repr__()}`\n"
            f"`{len(self.bot.wavelink.players)}` players are distributed on nodes.\n"
            f"`{node.stats.players}` players are distributed on server.\n"
            f"`{node.stats.playing_players}` players are playing on server.\n\n"
            f"Server Memory: `{used}/{total}` | `({free} free)`\n"
            f"Server CPU: `{cpu}`\n\n"
            f"Server Uptime: `{datetime.timedelta(milliseconds=node.stats.uptime)}`\n"
        )
        await ctx.send(fmt, delete_after=10)


def setup(bot):
    bot.add_cog(Music(bot))
