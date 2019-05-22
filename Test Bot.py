# to be run locally

from discord.ext import commands
import discord
import time
from datetime import datetime
from datetime import timedelta
from datetime import date
import math

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

@bot.command()
async def reminder(ctx, subcommand='help', *args):
    '''Set reminders for yourself, supports multiple formats.'''
    if (subcommand == 'help'):
        await ctx.send('Set a reminder for yourself with the '
                       'following supported formats: \n    '
                       '!reminder add [#] [days] [time] [message] \n    '
                       '!reminder add [#] [weeks] [time] [message] \n    '
                       '!reminder add [day of week] [time] [message] \n    '
                       '!reminder add [month] [day] [time] [message] \n'
                       'Time will default to 8:00 AM if not '
                       'specified.\n'
                       'Additionally, supports removal of previously '
                       'added reminders and viewing of reminders by user '
                       'using the remove and list subcommands. \n'
                       'Note that apostrophe and quote symbols '
                       'cannot be used in the reminder message.')
    elif (subcommand == 'add'):
        # assumes users of the bot are in the same timezone as the bot
        try:
            if len(args) < 2:
                raise SyntaxError('Too few arguments to add a reminder')
            indicator = args[0]
            numberOfDays = 0
            splitArgsHere = 0
            now = datetime.today()
            indicator = args[0].lower()
            if 'day' in args[1]:
                if (4 < len(args)) and 'week' in args[3]:
                    numberOfDays += int(args[2]) * 7
                    splitArgsHere += 2
                numberOfDays += int(args[0])
                splitArgsHere += 2
            elif 'week' in args[1]:
                if (4 < len(args)) and 'day' in args[3]:
                    numberOfDays += int(args[2])
                    splitArgsHere += 2
                numberOfDays += int(args[0]) * 7
                splitArgsHere += 2
            elif any(weekday in indicator for weekday in ['sun', 
                     'mon', 'tue', 'wed', 'thu', 'fri', 'sat']):
                # case insensitive comparison
                splitArgsHere += 1
                if 'sun' in indicator:
                    numberOfDays += (6 - now.weekday())
                elif 'mon' in indicator:
                    numberOfDays += (0 - now.weekday())%7
                elif 'tue' in indicator:
                    numberOfDays += (1 - now.weekday())%7
                elif 'wed' in indicator:
                    numberOfDays += (2 - now.weekday())%7
                elif 'thu' in indicator:
                    numberOfDays += (3 - now.weekday())%7
                elif 'fri' in indicator:
                    numberOfDays += (4 - now.weekday())%7
                elif 'sat' in indicator:
                    numberOfDays += (5 - now.weekday())%7
            elif any(month in indicator for month in ['jan', 'feb',
                     'mar', 'apr', 'may', 'jun', 'jul', 'aug', 
                     'sep', 'oct', 'nov', 'dec']):
                splitArgsHere += 2
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
                if now.month > newmonth:
                    addyear += 1
                elif now.month == newmonth and newday < now.day:
                    addyear += 1
                newdate = now.replace(year=now.year + addyear, month=newmonth, day=newday)
                numberOfDays += math.ceil((newdate - now).days)
            
            hour = 8
            minute = 0
            if ':' in args[splitArgsHere]:
                hoursAndMins = args[splitArgsHere].split(':')
                hour = int(hoursAndMins[0])
                minute = int(hoursAndMins[1][0]) + 10*int(hoursAndMins[1][1])
                splitArgsHere += 1
                # Assumes users will not set times like 13:00 am/pm
                if len(hoursAndMins[1]) > 2:
                    if hoursAndMins[1][2].lower() == 'p':
                        hour += 12
                elif args[splitArgsHere].lower() == 'pm':
                    hour += 12
                    splitArgsHere += 1
                elif args[splitArgsHere].lower() == 'am':
                    splitArgsHere += 1

            if len(args) < splitArgsHere + 1:
                raise SyntaxError('Missing reminder message')

            message = ' '.join(args[splitArgsHere:])
            daysToAdd = timedelta(days=numberOfDays)
            reminderTime = now + daysToAdd
            reminderTime = reminderTime.replace(hour=hour, minute=minute, second=0, microsecond=0)
            await ctx.send('Hello there! It worked! Add {0} days!'.format(numberOfDays))
            await ctx.send('Reminder Time is now ' + str(reminderTime))
            await ctx.send('Message is this: ' + message)

        except (IndexError, SyntaxError, TypeError, commands.errors.UnexpectedQuoteError) as e:
            await ctx.send('Invalid reminder format! '
                           'Type \'!reminder\' to see supported '
                           'formats.')
    elif (subcommand == 'remove'):
        personID = ctx.message.author
        
    elif (subcommand == 'list'):
        if not ctx.message.mentions:
            # Require the user to mention someone
            await ctx.send('You must mention (@) someone!')
        elif bot.user in ctx.message.mentions:
            await ctx.send('Cannot mention (@) the bot!')
        else:
            personID = ctx.message.mentions[0]

    else:
        await ctx.send('Invalid subcommand! Valid subcommands are '
                       'add, remove, list, and help.')

bot.run('bot-token') # Add bot token here to run the bot
