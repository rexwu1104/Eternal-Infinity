from ..Imports import *

from .Enum import MPlayMode, MPlayStatus
from .Song import MSong
from .Container import MContainer

import enum

from datetime import datetime
from typing import TypeVar
from discord.ext import commands
from discord.ui import Button, Select, View, button
from discord import Color, Embed, Interaction, Message, SelectOption

__all__ = (
    'MusicView',
)

MController = TypeVar('MController') # from .Controller import MController

class MusicView():
    
    class PagePosition(enum.Enum):
        Info = 0
        Queue = 1
        Now = 2
    
    class ControlBoard(View):
        controller: MController
        page_position: int = 0
        
        def __init__(self, controller: MController) -> None:
            super().__init__(timeout=None)
            
            self.controller = controller
            
        async def response(self, interaction: Interaction) -> None:
            if not interaction.response._responded:
                await interaction.response.defer()
                
        async def check_operate(self, interaction: Interaction):
            container = self.controller.containers[interaction.guild_id]
            if container.client is None:
                raise commands.CommandError('Client is not in channel.')
            
            if len(container.client.channel.members) == 2 or self.controller.check_dj(interaction.user):
                return True
            return False
            
        @button(custom_id='first', emoji='⏮️', row=0)
        async def _first(self, interaction: Interaction, button: Button) -> None:
            await self.response(interaction)
            if not await self.check_operate(interaction):
                raise commands.CommandError('Premission lost.')
            
            self.controller.jump_at(interaction.guild_id, 0)
            
        @button(custom_id='prev', emoji='⏪', row=0)
        async def _prev(self, interaction: Interaction, button: Button) -> None:
            await self.response(interaction)
            if not await self.check_operate(interaction):
                raise commands.CommandError('Premission lost.')
            
            self.controller.jump_at(interaction.guild_id,
                                    self.controller.containers[interaction.guild_id].now_pos - 1)

        @button(custom_id='play_or_pause', emoji='⏸️', row=0)
        async def _play_or_pause(self, interaction: Interaction, button: Button) -> None:
            await self.response(interaction)
            container = self.controller.containers[interaction.guild_id]
            
            if container.play_status == MPlayStatus.Play:
                container.play_status = MPlayStatus.Pause
                self.controller.pause(interaction.guild_id)
                button.emoji = '▶️'
            elif container.play_status == MPlayStatus.Pause:
                container.play_status = MPlayStatus.Play
                self.controller.resume(interaction.guild_id)
                button.emoji = '⏸️'
                
            await container.sent_message.edit(view=self)

        @button(custom_id='next', emoji='⏩', row=0)
        async def _next(self, interaction: Interaction, button: Button) -> None:
            await self.response(interaction)
            if not await self.check_operate(interaction):
                raise commands.CommandError('Premission lost.')
            
            self.controller.jump_at(interaction.guild_id,
                                    self.controller.containers[interaction.guild_id].now_pos + 1)

        @button(custom_id='last', emoji='⏭️', row=0)
        async def _last(self, interaction: Interaction, button: Button) -> None:
            await self.response(interaction)
            if not await self.check_operate(interaction):
                raise commands.CommandError('Premission lost.')
            
            self.controller.jump_at(interaction.guild_id,
                                    len(self.controller.containers[interaction.guild_id].data) - 1)

        @button(custom_id='whisper', emoji='🔉', row=1)
        async def _whisper(self, interaction: Interaction, button: Button) -> None:
            await self.response(interaction)
            container = self.controller.containers[interaction.guild_id]
            self.controller.set_volume(interaction.guild_id,
                                       self.controller.containers[interaction.guild_id].volume - 0.1)
                    
            container.view.page_position = MusicView.PagePosition.Info
            await container.sent_message.edit(embed=MusicView.information_embed(container), view=self)

        @button(custom_id='suffle', emoji='🔀', row=1)
        async def _suffle(self, interaction: Interaction, button: Button) -> None:
            await self.response(interaction)
            if not await self.check_operate(interaction):
                raise commands.CommandError('Premission lost.')
            
            container = self.controller.containers[interaction.guild_id]
            self.controller.change_play_mode(interaction.guild_id,
                                             MPlayMode.Shuffle if not self._loop.emoji == '➡️'
                                             or self.controller.containers[interaction.guild_id].loop_mode != MPlayMode.Shuffle
                                             else MPlayMode.Nothing)
            if not self._loop.emoji == '➡️':
                self._loop.emoji = '➡️'
                
            container.view.page_position = MusicView.PagePosition.Info
            await container.sent_message.edit(embed=MusicView.information_embed(container), view=self)

        @button(custom_id='stop', emoji='⏹️', row=1)
        async def _stop(self, interaction: Interaction, button: Button) -> None:
            await self.response(interaction)
            self.controller.stop(interaction.guild_id)

        @button(custom_id='loop', emoji='➡️', row=1)
        async def _loop(self, interaction: Interaction, button: Button) -> None:
            await self.response(interaction)
            if not await self.check_operate(interaction):
                raise commands.CommandError('Premission lost.')
            
            container = self.controller.containers[interaction.guild_id]
            
            match container.play_mode:
                case MPlayMode.Nothing | MPlayMode.Shuffle:
                    self.controller.change_play_mode(interaction.guild_id, MPlayMode.Odd)
                    button.emoji = '🔂'
                    
                case MPlayMode.Odd:
                    self.controller.change_play_mode(interaction.guild_id, MPlayMode.All)
                    button.emoji = '🔁'
                    
                case MPlayMode.All | MPlayMode.Plural:
                    self.controller.change_play_mode(interaction.guild_id, MPlayMode.Nothing)
                    button.emoji = '➡️'
            
            container.view.page_position = MusicView.PagePosition.Info
            await container.sent_message.edit(embed=MusicView.information_embed(container), view=self)

        @button(custom_id='lounder', emoji='🔊', row=1)
        async def _lounder(self, interaction: Interaction, button: Button) -> None:
            await self.response(interaction)
            container = self.controller.containers[interaction.guild_id]
            self.controller.set_volume(interaction.guild_id,
                                       self.controller.containers[interaction.guild_id].volume + 0.1)
                    
            container.view.page_position = MusicView.PagePosition.Info
            await container.sent_message.edit(embed=MusicView.information_embed(container), view=self)

        @button(custom_id='search', emoji='🔍', row=2)
        async def _list_search(self, interaction: Interaction, button: Button) -> None:
            await self.response(interaction)
            container = self.controller.containers[interaction.guild_id]
            
            question_message: Message = \
                await interaction.channel.send('**' + container.translater.translate('What do you want to search?') + '**')
            result: Message = await self.controller.bot.wait_for('message', check=lambda ctx: ctx.author == interaction.user)
            
            await question_message.delete()
            await result.delete()
            
            context = await self.controller.bot.get_context(result)
            await context.invoke(self.controller.bot.get_command('search'), query=result.content)

        @button(custom_id='queue', emoji='📜', row=2)
        async def _queue(self, interaction: Interaction, button: Button) -> None:
            container = self.controller.containers[interaction.guild_id]
            if self.page_position == MusicView.PagePosition.Queue:
                return
            
            self.page_position = MusicView.PagePosition.Queue
            await container.sent_message.edit(embed=MusicView.queue_embed(container))
            await self.response(interaction)

        @button(custom_id='home', label='🏠', row=2)
        async def _home(self, interaction: Interaction, button: Button) -> None:
            container = self.controller.containers[interaction.guild_id]
            if self.page_position == MusicView.PagePosition.Info:
                return
            
            self.page_position = MusicView.PagePosition.Info
            await container.sent_message.edit(embed=MusicView.information_embed(container))
            await self.response(interaction)

        @button(custom_id='info', emoji='📄', row=2)
        async def _info(self, interaction: Interaction, button: Button) -> None:
            container = self.controller.containers[interaction.guild_id]
            if self.page_position == MusicView.PagePosition.Now:
                return
            
            self.page_position = MusicView.PagePosition.Now
            await container.sent_message.edit(embed=MusicView.now_information_embed(container))
            await self.response(interaction)

        @button(custom_id='play', emoji='🔎', row=2)
        async def _play_search(self, interaction: Interaction, button: Button) -> None:
            await self.response(interaction)
            container = self.controller.containers[interaction.guild_id]
            
            question_message: Message = \
                await interaction.channel.send('**' + container.translater.translate('What do you want to search?') + '**')
            result: Message = await self.controller.bot.wait_for('message', check=lambda ctx: ctx.author == interaction.user)
            
            await question_message.delete()
            await result.delete()
            
            context = await self.controller.bot.get_context(result)
            await context.invoke(self.controller.bot.get_command('play'), url=result.content)
            
    class SelectView(View, AsyncObject):
        
        async def __init__(self, ctx: commands.Context, controller: MController, yet_url: str):
            super().__init__(timeout=None)
            self.add_item(await MusicView._MusicSelect(ctx, controller, yet_url))
            
    class _MusicSelect(Select, AsyncObject):
        controller: MController
        
        async def __init__(self, ctx: commands.Context, controller: MController, yet_url: str) -> None:
            self.controller = controller
            self.guild_id = ctx.guild.id
            
            Logger.log('guild[{0}] list search: {1}'.format(ctx.guild.name, yet_url))
            container = controller.containers[self.guild_id]
            options = [SelectOption(label=info['title'], value=info['url'], description=info['url'])
                       for info in (await process_url_structs(yet_url))[0]]
            
            super().__init__(placeholder=container.translater.translate('Choose a choice'), options=options)
            
        async def response(self, interaction: Interaction) -> None:
            if not interaction.response._responded:
                await interaction.response.defer()
            
        async def callback(self, interaction: Interaction):
            await self.response(interaction)
            container = self.controller.containers[interaction.guild_id]
            
            container.data.append(await MSong(self.values[0], interaction.user))
            container.info.append(container.data[-1].dict_info)
            
            container.view.page_position = MusicView.PagePosition.Info
            if container.play_status is MPlayStatus.UnStarted:
                await container.sent_message.edit('**' + container.translater.translate('loading') + '...**', view=None)
                self.controller.play(interaction.guild_id)
            else:
                await container.sent_message.edit(embed=MusicView.information_embed(container))
                
            self.view.stop()
            
    @staticmethod
    def information_embed(container: MContainer):
        data = container.data[container.now_pos]
        embed = Embed(color=Color.random(),
                      title=data.info.title,
                      url=data.url,
                      timestamp=datetime.now())
        
        def decorate(l: list):
            return str(l).replace('\'', '').replace('[', '').replace(']', '') if len(l) != 0 else 'Nothing'
        
        embed.add_field(name=container.translater.translate('title'),
                        value=f'```\n{data.info.title}\n```',
                        inline=True)
        embed.add_field(name=container.translater.translate('song author'),
                        value=f'```\n{data.info.author}\n```',
                        inline=True)
        embed.add_field(name=container.translater.translate('duration'),
                        value=f'```\n{data.info.length}\n```',
                        inline=True)
        
        
        embed.add_field(name=container.translater.translate('loop mode'),
                        value=f'```\n{container.play_mode.name}\n```',
                        inline=True)
        embed.add_field(name=container.translater.translate('volume'),
                        value=f'```\n{int(container.source.volume * 100)}%\n```',
                        inline=True)
        embed.add_field(name=container.translater.translate('streaming'),
                        value=f'```\n{data.info.living}\n```',
                        inline=True)
        
        
        embed.add_field(name=container.translater.translate('tags'),
                        value=f'```\n{decorate(data.info.tags)}\n```',
                        inline=False)
        
        
        embed.add_field(name=container.translater.translate('position'),
                        value=f'```\n{container.now_pos + 1}/{len(container)}\n```',
                        inline=True)
        embed.add_field(name=container.translater.translate('requester'),
                        value=f'```\n{data.author}\n```',
                        inline=True)
        
        embed.set_image(url=data.info.thumbnail)
        return embed
        
    @staticmethod
    def queue_embed(container: MContainer):
        embed = Embed(color=Color.random(),
                      title=container.translater.translate('Queue'),
                      timestamp=datetime.now())
        
        for idx in range(10):
            info = container.info[container.now_pos + idx] if container.now_pos + idx < len(container) else None
            if not info:
                break
            
            embed.add_field(name=str(container.now_pos + idx + 1) + '.', value=f'[{info["title"]}]({info["url"]})', inline=not idx % 2)
            
        return embed
        
    @staticmethod
    def now_information_embed(container: MContainer):
        progress = '▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬'
        description = f'''
        [{container.data[container.now_pos].info.title}]({container.data[container.now_pos].url})
        
        `{
            progress[:int(container.source.elapsed/(length_to_duration(container.data[container.now_pos].info.length)+.1)*29)]
        }🔘{
            progress[int(container.source.elapsed/(length_to_duration(container.data[container.now_pos].info.length)+.1)*29):]
        }`
        
        `{duration_to_length(int(container.source.elapsed))}/{container.data[container.now_pos].info.length}`
        '''
        embed = Embed(color=Color.random(),
                      description=description,
                      title=container.translater.translate('Now Playing'),
                      timestamp=datetime.now())
        
        data = container.data[container.now_pos]
        embed.add_field(name=container.translater.translate('song author'),
                        value=f'```\n{data.info.author}\n```',
                        inline=True)
        embed.add_field(name=container.translater.translate('view counts'),
                        value=f'```\n{data.info.counts}\n```',
                        inline=True)
        embed.add_field(name=container.translater.translate('likes'),
                        value=f'```\n{data.info.likes}\n```',
                        inline=True)
        
        embed.set_thumbnail(url=container.data[container.now_pos].info.thumbnail)
        return embed