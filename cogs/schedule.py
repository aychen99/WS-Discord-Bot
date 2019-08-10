import discord
from discord.ext import commands, tasks
import json

class Schedule(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener
    async def on_ready(self):
        self.update_scheduled_roles.start()
    
    @commands.command
    async def schedule(self, ctx, subcommand='help', *args):
        """Store scheduled availability and dynamically assign roles to users.

        Scheduling is opt-in and adding, removing, and changing scheduling is 
        entirely dependent on Discord users themselves. Implemented by storing 
        user scheduling information in a local JSON file.
        """
        if subcommand.lower() not in ('help', 'set', 'change', 
                                      'view', 'clear'):
            await ctx.send('Invalid subcommand! Valid subcommands are ' 
                        '*help*, *set*, *change*, *view*, and *clear*.')
            return
        if (subcommand == 'help'):
            await ctx.send('The "!schedule" bot command allows you to set '
                           'your availability on Discord. Currently it only '
                           'supports regular scheduling by days of the '
                           'week.\n'
                           'Available subcommands are *set*, *change*, '
                           '*view*, and *clear*. \n'
                           'To see specific instructions on how to use each '
                           'of the subcommands, type "!schedule" followed by '
                           'the name of subcommand you are using.')
            return

        if (subcommand == 'set'):
            if len(args) == 0:
                await ctx.send('Detailed help message in development! '
                               'In the meantime, here are some examples '
                               'of supported syntax: \n'
                               '```'
                               '!schedule set Monday 8 AM - 12 PM\n'
                               '!schedule set Monday 8:00 - 12:00\n'
                               '!schedule set Thursday 1 PM - 5:30 PM\n'
                               '!schedule set Tue 12:00 - 20:00, Wed '
                               '10:00 - 20:00'
                               '```')
                return
            await ctx.send('TODO')
        elif (subcommand == 'change'):
            await ctx.send('TODO') #TODO
        elif (subcommand == 'view'):
            await ctx.send('TODO') # TODO
        elif (subcommand == 'clear'):
            await ctx.send('TODO') # TODO


    @tasks.loop(minutes=1.0)
    async def update_scheduled_roles(self):
        pass #TODO

def setup(bot):
    bot.add_cog(Schedule(bot))