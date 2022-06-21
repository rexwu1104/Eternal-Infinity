from Classes import *

from time import time
from typing import Optional, Union
from discord import Guild, NotFound, StageChannel, VoiceChannel
from discord.ext import commands

__all__ = (
    'Music',
)

group = commands.group
command = commands.command
event = commands.Cog.listener()

class ModeConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, arguments: str):
        if arguments.isdigit():
            return int(arguments) - 1
        elif arguments.lower() == 'all':
            return 'all'
        elif len(rang := arguments.split('~')) == 2 or len(rang := arguments.split('-')) == 2:
            if rang[0].isdigit() and rang[1].isdigit():
                return [int(rang[0]) - 1, int(rang[1]) - 1]
        else:
            raise commands.BadArgument('Not match mode.')

class Music(commands.Cog):
    'The function relate to music.'
    
    bot: commands.AutoShardedBot
    controller: MController
    
    def __init__(self, bot: commands.AutoShardedBot):
        super().__init__()
        
        self.bot = bot
        
    async def init(self):
        await self.bot.wait_until_ready()
        self.controller = await MController.create(self.bot)
        
    @event
    async def on_command_error(self, ctx: commands.Context, *args, **kwargs):
        try:
            await ctx.message.delete()
        except: pass
        
        for arg in args:
            Logger.error(arg)
        for k, v in kwargs.items():
            Logger.error(k + ': ' + str(v))
        
    @event
    async def on_ready(self):
        await self.init()
        
    @event
    async def on_guild_join(self, guild: Guild):
        try:
            dj_role = await guild.create_role(name='dj')
        except PermissionError:
            return await guild.leave()
            
        self.controller.containers[guild.id] = MContainer(guild.id, MTranslator(self.controller.translate_data[guild.id]))
        self.controller.containers[guild.id].view = MusicView.ControlBoard(self.controller)
        
        self.controller.db.write('classes/translate.json', self.controller.translate_data)
        self.controller.add_dj(guild.id, dj_role.id)
        
    @command(aliases=['p'])
    async def play(self, ctx: commands.Context, *, url: str = None):
        '''
        {2.command_prefix}play {0} {2.command_prefix}p [url {0} query]
        
        {1}:
        {2.command_prefix}p
        {2.command_prefix}p https://www.youtube.com/watch?v=nCQ_zZIiGLA
        {2.command_prefix}play king kanaria
        '''
        
        await self.check_premission(ctx)
        container: MContainer = self.controller.containers[ctx.guild.id]
        if not url and container.view is not None:
            view = container.view
            view._play_or_pause.emoji = '▶️'
            
            self.controller.resume(ctx.guild.id)
            return await container.sent_message.edit(view=view)
        elif not url:
            raise commands.CommandError('Invalied arguments.')
        elif url.find('list=') != -1:
            return await (await ctx.send('We don\'t support list now.')).delete(delay=5)
            
        Logger.log('guild[{0}] search: {1}'.format(ctx.guild.name, url))
        message = await ctx.send('**' + container.translater.translate('searching') + '...**')
        if container.client is None:
            container.client = await ctx.author.voice.channel.connect()
        if ctx.author in self.controller.youtube_enable_users:
            can_list = True
        else:
            can_list = False
            
        first_time = time()
        async with ctx.typing():
            container.data.append(await MSong(url, ctx.author))
            Logger.debug('data get {0}s'.format(time() - first_time))
            
        if hasattr(container.data[-1], 'songs'):
            if not can_list:
                return await (await ctx.send('**' + container.translater.translate('You do not enable youtube function.') + '**')).delete(delay=5)
            
            data = container.data.pop(len(container) - 1)
            for song in data.songs:
                container.data.append(MSong(song, ctx.author, search=False))
                container.info.append(container.data[-1].dict_info)
        else:
            container.info.append(container.data[-1].dict_info)
            
        if container.play_status is MPlayStatus.UnStarted:
            await message.edit('**' + container.translater.translate('loading') + '...**')
            container.sent_message = message
            self.controller.play(ctx.guild.id)
        else:
            container.view.page_position = MusicView.PagePosition.Info
            await container.sent_message.edit(embed=MusicView.information_embed(container))
            await message.delete()
            
    @command()
    async def search(self, ctx: commands.Context, *, query: str):
        '''
        {2.command_prefix}search <query>
        
        {1}:
        {2.command_prefix}search honeyworks
        '''
        
        await self.check_premission(ctx)
        container: MContainer = self.controller.containers[ctx.guild.id]
        if container.client is None:
            container.client = ctx.voice_client or await ctx.author.voice.channel.connect()
            
        view = await MusicView.SelectView(ctx, self.controller, query)
        select_message = await ctx.send('**' + container.translater.translate('list of search:') + '**', view=view)
        
        if container.sent_message is None:
            container.sent_message = select_message
        elif not await view.wait():
            await select_message.delete()
            
    @command(aliases=['j', 'connect'])
    async def join(self, ctx: commands.Context, channel: Optional[Union[VoiceChannel, StageChannel]] = None):
        '''
        {2.command_prefix}j, {2.command_prefix}join {0} {2.command_prefix}connect [channel]
        
        {1}:
        {2.command_prefix}j
        {2.command_prefix}join 747454095643639858
        {2.command_prefix}connect <#747454095643639858>
        '''
        
        await self.check_premission(ctx)
        container: MContainer = self.controller.containers[ctx.guild.id]
        if container.client is None:
            if channel is None:
                container.client = ctx.voice_client or await ctx.author.voice.channel.connect()
            else:
                container.client = await channel.connect()
                
    @command(aliases=['dc', 'disconnect'])
    async def leave(self, ctx: commands.Context):
        '''
        {2.command_prefix}dc, {2.command_prefix}leave {0} {2.command_prefix}disconnect
        
        {1}:
        {2.command_prefix}dc
        {2.command_prefix}leave
        {2.command_prefix}disconnect
        '''
        
        await self.check_premission(ctx)
        container: MContainer = self.controller.containers[ctx.guild.id]
        if container.client is None:
            raise commands.CommandError('Client is not in the channel.')
        
        self.controller.stop(ctx.guild.id)
        
    @command(aliases=['l'])
    async def loop(self, ctx: commands.Context, rang: ModeConverter = None):
        '''
        {2.command_prefix}l {0} {2.command_prefix}loop [rang]
        
        {1}:
        {2.command_prefix}l
        {2.command_prefix}l 1-10
        {2.command_prefix}loop 3~7
        {2.command_prefix}loop all
        '''
        
        await self.check_premission(ctx)
        if not await self.check_operate(ctx):
            raise commands.CommandError('Premission lost.')
        
        container: MContainer = self.controller.containers[ctx.guild.id]
        if container.client is None:
            raise commands.CommandError('Client is not in the channel.')
        
        view = container.view
        rang = container.now_pos if rang is None else rang
        if isinstance(rang, int):
            self.controller.change_play_mode(ctx.guild.id, MPlayMode.Odd)
            view._loop.emoji = '🔂'
        elif isinstance(rang, list):
            self.controller.change_play_mode(ctx.guild.id, MPlayMode.Plural)
            view._loop.emoji = '🔁'
        elif isinstance(rang, str):
            self.controller.change_play_mode(ctx.guild.id, MPlayMode.All)
            view._loop.emoji = '🔁'
            
        match container.play_mode:
            case MPlayMode.Plural:
                if rang[0] < 0 or rang[1] >= len(container):
                    raise commands.CommandError('Out of range.')
            case MPlayMode.Odd:
                if rang != container.now_pos:
                    raise commands.CommandError('Out of range.')
            case _: pass
            
        container.range = rang
        await container.sent_message.edit(embed=MusicView.information_embed(container), view=view)
        
    @command()
    async def shuffle(self, ctx: commands.Context):
        '''
        {2.command_prefix}shffle
        
        {1}:
        {2.command_prefix}shffle
        '''
        
        await self.check_premission(ctx)
        if not await self.check_operate(ctx):
            raise commands.CommandError('Premission lost.')
        
        container: MContainer = self.controller.containers[ctx.guild.id]
        if container.client is None:
            raise commands.CommandError('Client is not in the channel.')
        
        view = container.view
        self.controller.change_play_mode(ctx.guild.id, MPlayMode.Shuffle)
        view._loop.emoji = '➡️'
            
        container.range = None
        await container.sent_message.edit(embed=MusicView.information_embed(container), view=view)
        
    @command(aliases=['s'])
    async def skip(self, ctx: commands.Context, position: int = None):
        '''
        {2.command_prefix}s {0} {2.command_prefix}skip [position]
        
        {1}:
        {2.command_prefix}s
        {2.command_prefix}skip 2
        '''
        
        await self.check_premission(ctx)
        if not await self.check_operate(ctx):
            raise commands.CommandError('Premission lost.')
        
        container: MContainer = self.controller.containers[ctx.guild.id]
        if position is None:
            return self.controller.stop(ctx.guild.id)
            
        match container.play_mode:
            case MPlayMode.Nothing | MPlayMode.All | MPlayMode.Shuffle:
                if not 0 < position <= len(container):
                    raise commands.CommandError('Out of range.')
            case MPlayMode.Plural:
                if not container.range[0] < position <= container.range[1]:
                    raise commands.CommandError('Out of range.')
            case MPlayMode.Odd:
                if position != container.range:
                    raise commands.CommandError('Out of range.')
                
        self.controller.jump_at(ctx.guild.id, position - 1)
        
    @command(aliases=['stop'])
    async def pause(self, ctx: commands.Context):
        '''
        {2.command_prefix}stop {0} {2.command_prefix}pause
        
        {1}:
        {2.command_prefix}stop
        {2.command_prefix}pause
        '''
        
        await self.check_premission(ctx)
        container: MContainer = self.controller.containers[ctx.guild.id]
        view = container.view
        view._play_or_pause.emoji = '▶️'
        
        self.controller.pause(ctx.guild.id)
        await container.sent_message.edit(view=view)
        
    @command(aliases=['vol'])
    async def volume(self, ctx: commands.Context, volume: float):
        '''
        {2.command_prefix}vol {0} {2.command_prefix}volume <volume>
        
        {1}:
        {2.command_prefix}vol 1
        {2.command_prefix}volume 1.4
        '''
        
        await self.check_premission(ctx)
        container: MContainer = self.controller.containers[ctx.guild.id]
        
        self.controller.set_volume(ctx.guild.id, volume)
        await container.sent_message.edit(embed=MusicView.information_embed(container))
        
    @command(aliases=['nowplay', 'np'])
    async def nowinfo(self, ctx: commands.Context):
        '''
        {2.command_prefix}np, {2.command_prefix}nowplay {0} {2.command_prefix}nowinfo
        
        {1}:
        {2.command_prefix}np
        {2.command_prefix}nowplay
        {2.command_prefix}nowinfo
        '''
        
        await self.check_premission(ctx)
        container: MContainer = self.controller.containers[ctx.guild.id]
        if container.client is None:
            return Logger.error('Client is not joined the channel.')
        
        await container.sent_message.edit(embed=MusicView.now_information_embed(container))
        
    @command(aliases=['q'])
    async def queue(self, ctx: commands.Context):
        '''
        {2.command_prefix}q {0} {2.command_prefix}queue
        
        {1}:
        {2.command_prefix}q
        {2.command_prefix}queue
        '''
        
        await self.check_premission(ctx)
        container: MContainer = self.controller.containers[ctx.guild.id]
        if container.client is None:
            return Logger.error('Client is not joined the channel.')
        
        await container.sent_message.edit(embed=MusicView.queue_embed(container))
        
    @command()
    async def remove(self, ctx: commands.Context, position: int):
        '''
        {2.command_prefix}remove <position>
        
        {1}:
        {2.command_prefix}remove 4
        '''
        
        await self.check_premission(ctx)
        if not await self.check_operate(ctx):
            raise commands.CommandError('Premission lost.')
        
        container: MContainer = self.controller.containers[ctx.guild.id]
        if not 0 < position <= len(container):
            raise commands.CommandError('Out of range.')
        
        self.controller.remove_music(ctx.guild.id, position - 1)
        await container.sent_message.edit(embed=MusicView.information_embed(container))
        
    @command()
    async def together(self, ctx: commands.Context):
        '''
        {2.command_prefix}together
        
        {1}:
        {2.command_prefix}together
        '''
        
        await self.check_premission(ctx)
        link = await self.bot.togetherControl.create_link(ctx.author.voice.channel.id, 'youtube')
        await ctx.send("__click this!!!__\n{}".format(link))
        
    @group()
    async def youtube(self, ctx: commands.Context):
        '''
        {2.command_prefix}youtube [sub_command]
        
        {1}:
        {2.command_prefix}youtube enable
        {2.command_prefix}youtube disable
        '''
        
        await self.check_premission(ctx)
        if ctx.invoked_subcommand is None:
            ...
            
    @youtube.command()
    async def enable(self, ctx: commands.Context):
        container = self.controller.containers[ctx.guild.id]
        if self.controller.add_youtube_enable(ctx.author):
            await (await ctx.send('**' + container.translater.translate('You already enable youtube function.') + '**')).delete(delay=5)
        else:
            await (await ctx.send('**' + container.translater.translate('Youtube function enabled.') + '**')).delete(delay=5)
            
    @youtube.command()
    async def disable(self, ctx: commands.Context):
        container = self.controller.containers[ctx.guild.id]
        if self.controller.remove_youtube_enable(ctx.author):
            await (await ctx.send('**' + container.translater.translate('You already disable youtube function.') + '**')).delete(delay=5)
        else:
            await (await ctx.send('**' + container.translater.translate('Youtube function disabled.') + '**')).delete(delay=5)
            
    @play.before_invoke
    @search.before_invoke
    @join.before_invoke
    @together.before_invoke
    async def check_voice_vlient(self, ctx: commands.Context):
        container: MContainer = self.controller.containers[ctx.guild.id]
        if container.client is None:
            if ctx.author.voice is None:
                await (await ctx.send('**' + container.translater.translate('Please join a channel before you use the command') + '**')).delete(delay=5)
                raise commands.CommandError('User doesn\'t join a channel.')
        elif container.client.channel != ctx.author.voice.channel and len(container.client.channel.members) > 1:
            await (await ctx.send('**' + container.translater.translate('I can\'t join another channel when my channel has other people') + '**')).delete(delay=5)
            raise commands.CommandError('User doesn\'t in the same channel.')
        
    async def check_operate(self, ctx: commands.Context):
        container = self.controller.containers[ctx.guild.id]
        if container.client is None:
            raise commands.CommandError('Client is not in channel.')
        
        if len(container.client.channel.members) == 2 or self.controller.check_dj(ctx.author):
            return True
        return False
            
    async def check_premission(self, ctx: commands.Context):
        try:
            await ctx.message.delete()
        except NotFound:
            return
        except:
            raise commands.CommandError('No message premission')