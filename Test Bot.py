# to be run locally

from discord.ext import commands
import discord
import os
from inspect import getsourcefile
from os.path import abspath

class WSDiscordBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!')

        try:
            self.load_extension('cogs.reminder')
        except Exception as e:
            print('Reminder cog loading failed.' + str(e))

    async def on_ready(self):
        print('We have logged in as {0.user}'.format(bot))
        await bot.change_presence(
            activity=discord.Game(name='Type "!help" for info on commands!'))
        # Ensure that a file for reminders exists in the main .py file directory
        if os.getcwd() != str(abspath(getsourcefile(lambda:0))):
            os.chdir(os.path.dirname(abspath(getsourcefile(lambda:0))))
        reminder_file = open('cogs/reminders.txt', 'a')
        reminder_file.close()
        # Ensure that there is a specific channel and category for using bots
        for guild in bot.guilds:
            if not any('bot-reminders' in channel_name.name 
                    for channel_name in guild.text_channels):
                botstuff_category = await guild.create_category('bot-stuff')
                await guild.create_text_channel('bot-reminders', 
                                                category=botstuff_category)


if __name__ == "__main__":
    bot = WSDiscordBot()
    bot.run('bot-token') # Add bot token here to run the bot