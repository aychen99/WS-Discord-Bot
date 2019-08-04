# to be run locally

from discord.ext import commands, tasks
import discord
import asyncio
import time
from datetime import datetime
from datetime import timedelta
from datetime import date
import math
import os
from inspect import getsourcefile
from os.path import abspath

bot = commands.Bot(command_prefix='!')

@tasks.loop(minutes=1.0)
async def send_reminders():
    with open('reminders.txt', 'r+') as reminder_file:
        remaining_reminders = reminder_file.readlines()
    original_reminder_count = len(remaining_reminders)
    for reminder in remaining_reminders:
        reminder_parts = reminder.split(' ')
        date = reminder_parts[0]
        time = reminder_parts[1]
        author = bot.get_user(int(reminder_parts[2]))
        channel = bot.get_channel(int(reminder_parts[3]))
        reminder_message = ' '.join(reminder_parts[4:])

        reminder_dt = datetime(year=int(date[0:4]), month=int(date[5:7]), 
                                day=int(date[8:10]), hour=int(time[0:2]),
                                minute=int(time[3:5]))
        reminder_timedelta = reminder_dt - datetime.today()
        second_diff = reminder_timedelta.total_seconds()
        if second_diff < -30:
            # Reminder is overdue
            await channel.send('{0}, you have a **late** reminder: \n'
                                .format(author.mention) 
                                + '```' + reminder_message + '```')
            remaining_reminders.remove(reminder)
        elif abs(second_diff) <= 30:
            # Reminder should be sent at the current minute, so send it
            await channel.send('{0}, you have a reminder: \n'
                                .format(author.mention) 
                                + '```' + reminder_message + '```')
            remaining_reminders.remove(reminder)
        else:
            # No more reminders to send in the sorted list
            break

    if len(remaining_reminders) == original_reminder_count:
        pass
    else:
        with open('reminders.txt', 'w') as reminder_file:
            for reminder in remaining_reminders:
                reminder_file.write(reminder)


@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    await bot.change_presence(
        activity=discord.Game(name='Type "!help" for info on commands!'))
    # Ensure that a file for reminders exists in the main .py file directory
    if os.getcwd() != str(abspath(getsourcefile(lambda:0))):
        os.chdir(os.path.dirname(abspath(getsourcefile(lambda:0))))
    reminder_file = open('reminders.txt', 'a')
    reminder_file.close()
    # Ensure that there is a channel and category specifically for using bots
    for guild in bot.guilds:
        if not any('bot-reminders' in channel_name.name 
                   for channel_name in guild.text_channels):
            botstuff_category = await guild.create_category('bot-stuff')
            await guild.create_text_channel('bot-reminders', 
                                            category=botstuff_category)
    send_reminders.start()


@bot.command()
async def reminder(ctx, subcommand='help', *args):
    """Set and remove reminders for yourself. Supports multiple formats.

    Accepts three subcommands: 'add', 'remove', and 'list'. Specific 
    instructions are provided when the user types '!reminder' in Discord.
    """
    if (subcommand == 'help'):
        # Default behavior if user simply types '!reminder'
        await ctx.send('Set a reminder for yourself with the '
                       'following supported formats: \n'
                       '```!reminder add [#] [days] [time] [message] \n'
                       '!reminder add [#] [weeks] [time] [message] \n'
                       '!reminder add [day of week] [time] [message] \n'
                       '!reminder add [month] [day] [time] [message] \n'
                       '!reminder add [#] [hours] [message] \n'
                       '!reminder add [#] [minutes] [message] \n'
                       '!reminder add [#] [hours] [#] [minutes] [message]```'
                       'Time will default to 8:00 AM if not '
                       'specified.\n'
                       'Additionally, supports removal of previously '
                       'added reminders and viewing of reminders by user '
                       'using the remove and list subcommands. \n'
                       'Note that apostrophe and quote symbols '
                       'cannot be used in the reminder message.')
    elif (subcommand == 'add'):
        # Assumes users of the bot are in the same timezone as the bot.
        try:
            if len(args) < 2:
                raise SyntaxError('Too few arguments to add a reminder')
            number_of_days = 0
            split_index = 0
            time_now = datetime.today()
            indicator = args[0].lower() # used in reminder by month or weekday
            reminder_hour = 8
            reminder_minute = 0

            # Handle !reminder [#] days
            if 'day' in args[1]:
                if (4 < len(args)) and 'week' in args[3]:
                    number_of_days += int(args[2]) * 7
                    split_index += 2
                number_of_days += int(args[0])
                split_index += 2
            # Handle !reminder [#] weeks
            elif 'week' in args[1]:
                if (4 < len(args)) and 'day' in args[3]:
                    number_of_days += int(args[2])
                    split_index += 2
                number_of_days += int(args[0]) * 7
                split_index += 2
            # Handle !reminder [#] hours
            elif 'hour' in args[1]:
                reminder_hour = time_now.hour + int(args[0])
                reminder_minute = time_now.minute
                split_index += 2
                if (4 < len(args)) and 'min' in args[3]:
                    reminder_minute += int(args[2])
                    while (reminder_minute >= 60):
                        reminder_minute -= 60
                        reminder_hour += 1
                    split_index += 2
                while (reminder_hour >= 24):
                    number_of_days += 1
                    reminder_hour -= 24
            # Handle !reminder [#] minutes
            elif 'min' in args[1]:
                reminder_minute = time_now.minute + int(args[0])
                reminder_hour = time_now.hour
                split_index += 2
                while (reminder_minute >= 60):
                    reminder_minute -= 60
                    reminder_hour += 1
                while (reminder_hour >= 24):
                    number_of_days += 1
                    reminder_hour -= 24
            # Handle !reminder [weekday]
            elif any(weekday in indicator for weekday in ['sun', 
                     'mon', 'tue', 'wed', 'thu', 'fri', 'sat']):
                # case insensitive comparison
                split_index += 1
                if 'sun' in indicator:
                    number_of_days += (6 - time_now.weekday())
                elif 'mon' in indicator:
                    number_of_days += (0 - time_now.weekday())%7
                elif 'tue' in indicator:
                    number_of_days += (1 - time_now.weekday())%7
                elif 'wed' in indicator:
                    number_of_days += (2 - time_now.weekday())%7
                elif 'thu' in indicator:
                    number_of_days += (3 - time_now.weekday())%7
                elif 'fri' in indicator:
                    number_of_days += (4 - time_now.weekday())%7
                elif 'sat' in indicator:
                    number_of_days += (5 - time_now.weekday())%7
            # Handle !reminder [month] [day]
            elif any(month in indicator for month in ['jan', 'feb',
                     'mar', 'apr', 'may', 'jun', 'jul', 'aug', 
                     'sep', 'oct', 'nov', 'dec']):
                split_index += 2
                newmonth = 0
                addyear = 0
                newday = int(args[1])
                if 'jan' in indicator:
                    newmonth = 1
                elif 'feb' in indicator:
                    newmonth = 2
                elif 'mar' in indicator:
                    newmonth = 3
                elif 'apr' in indicator:
                    newmonth = 4
                elif 'may' in indicator:
                    newmonth = 5
                elif 'jun' in indicator:
                    newmonth = 6
                elif 'jul' in indicator:
                    newmonth = 7
                elif 'aug' in indicator:
                    newmonth = 8
                elif 'sep' in indicator:
                    newmonth = 9
                elif 'oct' in indicator:
                    newmonth = 10
                elif 'nov' in indicator:
                    newmonth = 11
                else:
                    newmonth = 12
                if time_now.month > newmonth:
                    addyear += 1
                elif time_now.month == newmonth and newday < time_now.day:
                    addyear += 1
                new_date = time_now.replace(year=time_now.year + addyear, 
                                            month=newmonth, day=newday)
                number_of_days += math.ceil((new_date - time_now).days)

            # Handle the time of day for the reminder, if specified
            if ':' in args[split_index]:
                hours_and_mins = args[split_index].split(':')
                reminder_hour = int(hours_and_mins[0])
                reminder_minute = (int(hours_and_mins[1][1]) 
                                   + 10*int(hours_and_mins[1][0]))
                split_index += 1
                # Assumes users will not set times like 13:00 am/pm TODO
                if len(hours_and_mins[1]) > 2:
                    if hours_and_mins[1][2].lower() == 'p':
                        if reminder_hour != 12:
                            reminder_hour += 12
                elif args[split_index].lower() == 'pm':
                    if reminder_hour != 12:
                        reminder_hour += 12
                    split_index += 1
                elif args[split_index].lower() == 'am':
                    split_index += 1

            if len(args) < split_index + 1:
                raise SyntaxError('Missing reminder message')

            # Create and store the reminder
            message = ' '.join(args[split_index:])
            days_until_reminder = timedelta(days=number_of_days)
            reminder_time = time_now + days_until_reminder
            reminder_time = reminder_time.replace(hour=reminder_hour, 
                                                  minute=reminder_minute, 
                                                  second=0, 
                                                  microsecond=0)
            author_id = ctx.message.author.id
            channel_id = 0
            for channel in ctx.guild.text_channels:
                if channel.name == 'bot-reminders':
                    channel_id = channel.id
                    break
            new_reminder = (' '.join([str(reminder_time), str(author_id), 
                            str(channel_id), message]) 
                            + '\n')
            with open('reminders.txt', 'r') as reminder_file:
                active_reminders = reminder_file.readlines()
            active_reminders.append(new_reminder)
            active_reminders.sort()
            with open('reminders.txt', 'w') as reminder_file:
                for reminder in active_reminders:
                    reminder_file.write(reminder)
            await ctx.send('Reminder set for ' + str(reminder_time))

        except (IndexError, SyntaxError, TypeError, ValueError, 
                commands.errors.UnexpectedQuoteError):
            await ctx.send('Invalid reminder format! Type "!reminder" to see '
                           'supported formats.')

    elif (subcommand == 'remove'):
        # Find all active reminders for whoever sent the command
        author_id = ctx.message.author.id
        with open('reminders.txt', 'r') as reminder_file:
            active_reminders = []
            next_reminder = reminder_file.readline()
            while next_reminder:
                if str(author_id) in next_reminder:
                    reminder_components = next_reminder.split()
                    # Remove member and channel IDs
                    formatted_reminder = ' '.join(reminder_components[0:2] 
                                                + reminder_components[4:])
                    active_reminders.append(formatted_reminder)
                next_reminder = reminder_file.readline()

        if len(active_reminders) == 0:
            await ctx.send('No reminders scheduled, nothing to remove.')
        else:
            await ctx.send('Which of the following reminders would you like '
                    'to remove?\n```' 
                    + '\n'.join(('{0}. {1}').format(i, str(reminder)) 
                    for i, reminder in enumerate(active_reminders, 1)) 
                    + '```')

            try:
                def check(m):
                    return (m.channel == ctx.message.channel
                            and m.author == ctx.message.author
                            and int(m.content) <= len(active_reminders))
                reply = await bot.wait_for('message', timeout=60, check=check)
            except (asyncio.TimeoutError, ValueError, IndexError):
                await ctx.channel.send('Invalid input, canceling reminder '
                                       'removal. Please try again!')
                return

            reminder_number = int(reply.content)
            chosen_reminder = active_reminders[reminder_number - 1]
            chosen_reminder_time = chosen_reminder[:19]
            chosen_reminder_message = chosen_reminder[20:]
            with open('reminders.txt', 'r+') as reminder_file:
                active_reminders = reminder_file.readlines()
                reminder_file.seek(0)
                for i in active_reminders:
                    if not (chosen_reminder_time in i 
                            and chosen_reminder_message in i):
                        reminder_file.write(i)
                reminder_file.truncate()
            await ctx.channel.send('Reminder #' + str(reminder_number) 
                                + ': \n' 
                                + '```' + chosen_reminder + '```' +
                                'successfully removed!')

    elif (subcommand == 'list'):
        if not ctx.message.mentions:
            # Require the user to mention someone
            await ctx.send('You must mention (@) someone!')
        elif bot.user in ctx.message.mentions:
            await ctx.send('Cannot mention (@) the bot!')
        else:
            author_id = ctx.message.mentions[0].id
            reminder_file = open('reminders.txt', 'r')
            active_reminders = []
            next_reminder = reminder_file.readline()
            while next_reminder:
                if str(author_id) in next_reminder:
                    reminder_components = next_reminder.split()
                    # Remove member and channel IDs
                    formatted_reminder = ' '.join(reminder_components[0:2] 
                                                  + reminder_components[4:])
                    active_reminders.append(formatted_reminder)
                next_reminder = reminder_file.readline()
            if len(active_reminders) == 0:
                await ctx.send('No reminders scheduled.')
            else:
                await ctx.send('Here are all active reminders for {0}:\n' 
                                   .format(ctx.message.mentions[0].mention) 
                               + '```' 
                               + '\n'.join(('{0}. {1}')
                                   .format(i, str(reminder)) 
                                       for i, reminder 
                                       in enumerate(active_reminders, 1)) 
                               + '```')

    else:
        await ctx.send('Invalid subcommand! Valid subcommands are '
                       'add, remove, list, and help.')

if __name__ == "__main__":
    bot.run('NTc1ODI5NDg0OTE4NTM4MjUw.XPK-5A.VwYwIvf0-kJvlu_w0IXIT9Olj-o') # Add bot token here to run the bot