# to be run locally

from discord.ext import commands
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

async def send_reminder(seconds, authorID, channelID, message):
    '''
    Helper method for sending a reminder. Takes in an integer
    number of seconds, the Discord ID of the person to send the
    reminder to, the channel ID to send the reminder in,
    and the reminder message.
    '''
    if seconds > 0:
        await asyncio.sleep(seconds)
    author = bot.get_user(authorID)
    channel = bot.get_channel(channelID)
    reminderFile = open('reminders.txt', 'r+')
    newReminderLines = reminderFile.readlines()
    reminderFile.close()
    reminderFile = open('reminders.txt', 'w')
    lineswritten = 0
    overdueReminders = 0
    for i in newReminderLines:
        fullreminder = i.split(' ')
        date = fullreminder[0]
        time = fullreminder[1]
        reminderdt = datetime(year=int(date[0:4]), month=int(date[5:7]), day=int(date[8:10]), hour=int(time[0:2]), minute=int(time[3:5]))
        timediff = reminderdt - datetime.today()
        messagetimecorrect = (abs(timediff.days*3600*24 + timediff.seconds) < 29)
        overdueReminder = (timediff.days*3600*24 + timediff.seconds <= -29)
        if not (message in i and (messagetimecorrect or overdueReminder)):
            reminderFile.write(i)
            lineswritten += 1
        else:
            if overdueReminder:
                await channel.send('{0}, you have a late reminder: \n'.format(author.mention) +
                       '```' + message + '```')
                overdueReminders += 1
    reminderFile.close()
    # Check to skip reminder sending if it is deleted through !reminder remove
    if lineswritten == len(newReminderLines):
        return
    elif overdueReminders + lineswritten == len(newReminderLines):
        return
    await channel.send('{0}, you have a reminder: \n'.format(author.mention) +
                       '```' + message + '```')

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    # Ensure that a file for reminders exists in the .py file directory
    if os.getcwd() != str(abspath(getsourcefile(lambda:0))):
        os.chdir(os.path.dirname(abspath(getsourcefile(lambda:0))))
    reminderFile = open('reminders.txt', 'a')
    reminderFile.close()
    # Ensure that bot channel and category exist
    for botguild in bot.guilds:
        if not any('bot-reminders' in channelname.name for channelname in botguild.text_channels):
            botstuffcat = await botguild.create_category('bot-stuff')
            await botguild.create_text_channel('bot-reminders', category=botstuffcat)
    # Setup reminder checking
    reminderFile = open('reminders.txt', 'r')
    activeReminder = reminderFile.readline()
    reminderFile.close()
    while activeReminder != '':
        reminderargs = activeReminder.split(' ')
        date = reminderargs[0]
        time = reminderargs[1]
        authorID = reminderargs[2]
        channelID = reminderargs[3]
        reminderMessage = ' '.join(reminderargs[4:])
        timediff = datetime(year=int(date[0:4]), month=int(date[5:7]), day=int(date[8:10]), hour=int(time[0:2]), minute=int(time[3:5])) - datetime.today()
        secondsToSleep = timediff.seconds + timediff.days*24*3600
        await send_reminder(secondsToSleep, int(authorID), int(channelID), reminderMessage)
        reminderFile = open('reminders.txt', 'r')
        activeReminder = reminderFile.readline()
        reminderFile.close()

@bot.command()
async def reminder(ctx, subcommand='help', *args):
    '''
    Set reminders for yourself, supports multiple formats.
    Type \'!reminder\' to see a list of supported command formats.
    '''
    if (subcommand == 'help'):
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
        # assumes users of the bot are in the same timezone as the bot
        try:
            if len(args) < 2:
                raise SyntaxError('Too few arguments to add a reminder')
            numberOfDays = 0
            splitArgsHere = 0
            now = datetime.today()
            indicator = args[0].lower()
            hour = 8
            minute = 0

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
            elif 'hour' in args[1]:
                hour = now.hour + int(args[0])
                minute = now.minute
                splitArgsHere += 2
                if (4 < len(args)) and 'min' in args[3]:
                    minute += int(args[2])
                    while (minute >= 60):
                        minute -= 60
                        hour += 1
                    splitArgsHere += 2
                while (hour >= 24):
                    numberOfDays += 1
                    hour -= 24
            elif 'min' in args[1]:
                minute = now.minute + int(args[0])
                hour = now.hour
                splitArgsHere += 2
                while (minute >= 60):
                    minute -= 60
                    hour += 1
                while (hour >= 24):
                    numberOfDays += 1
                    hour -= 24
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

            if ':' in args[splitArgsHere]:
                hoursAndMins = args[splitArgsHere].split(':')
                hour = int(hoursAndMins[0])
                minute = int(hoursAndMins[1][1]) + 10*int(hoursAndMins[1][0])
                splitArgsHere += 1
                # Assumes users will not set times like 13:00 am/pm
                if len(hoursAndMins[1]) > 2:
                    if hoursAndMins[1][2].lower() == 'p':
                        if hour != 12:
                            hour += 12
                elif args[splitArgsHere].lower() == 'pm':
                    if hour != 12:
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
            authorID = ctx.message.author.id
            channelID = 0
            for channel in ctx.guild.text_channels:
                if channel.name == 'bot-reminders':
                    channelID = channel.id
                    break
            reminderFile = open('reminders.txt', 'r')
            allReminders = reminderFile.readlines()
            reminderFile.close()
            newReminder = ' '.join([str(reminderTime), str(authorID), str(channelID), message]) + '\n'
            allReminders.append(newReminder)
            allReminders.sort()
            reminderFile = open('reminders.txt', 'w')
            for eachReminder in allReminders:
                reminderFile.write(eachReminder)
            reminderFile.close()
            await ctx.send('Reminder set for ' + str(reminderTime))
            if newReminder == allReminders[0]:
                timediff = reminderTime - datetime.today()
                secondsToSleep = timediff.seconds + timediff.days*24*3600
                await send_reminder(secondsToSleep, authorID, channelID, message)

        except (IndexError, SyntaxError, TypeError, ValueError, commands.errors.UnexpectedQuoteError):
            await ctx.send('Invalid reminder format! '
                           'Type \'!reminder\' to see supported '
                           'formats.')
    elif (subcommand == 'remove'):
        authorID = ctx.message.author.id
        reminderFile = open('reminders.txt', 'r')
        activeReminders = []
        currentReminder = reminderFile.readline()
        while currentReminder:
            if str(authorID) in currentReminder:
                formattedCRList = currentReminder.split()
                # Remove member and channel IDs
                formattedCR = ' '.join(formattedCRList[0:2] + formattedCRList[4:])
                activeReminders.append(formattedCR)
            currentReminder = reminderFile.readline()
        reminderFile.close()
        if len(activeReminders) == 0:
            await ctx.send('No reminders scheduled, nothing to remove.')
        else:
            await ctx.send('Which of the following reminders would you like to '
                    'remove?\n```' +
                    '\n'.join(('{0}. {1}').format(i, str(reminder)) for i, reminder in enumerate(activeReminders, 1)) +
                    '```')
            try:
                def check(m):
                    return m.channel == ctx.message.channel
                reply = await bot.wait_for('message', timeout=60, check=check)
                numtodel = int(reply.content)
                linetodel = activeReminders[numtodel - 1]
                linetodelTime = linetodel[:19]
                linetodelMessage = linetodel[20:]
                reminderFile = open('reminders.txt', 'r+')
                newReminderLines = reminderFile.readlines()
                reminderFile.seek(0)
                resendRemindersNeeded = False
                for i in newReminderLines:
                    if not (linetodelTime in i and linetodelMessage in i):
                        reminderFile.write(i)
                    else:
                        if i == newReminderLines[0]:
                            resendRemindersNeeded = True
                reminderFile.truncate()
                reminderFile.close()
                await ctx.channel.send('Reminder #' + str(numtodel) + ': \n' +
                                    '```' + linetodel + '```' +
                                    'successfully removed!')
                # When deleting first reminder on list,
                # prepare to send out another reminder
                if resendRemindersNeeded:
                    newFirstReminder = newReminderLines[1].split(' ')
                    date = newFirstReminder[0]
                    time = newFirstReminder[1]
                    authorID = newFirstReminder[2]
                    channelID = newFirstReminder[3]
                    newReminderMessage = ' '.join(newFirstReminder[4:])
                    timediff = datetime(year=int(date[0:4]), month=int(date[5:7]), day=int(date[8:10]), hour=int(time[0:2]), minute=int(time[3:5])) - datetime.today()
                    secondsToSleep = timediff.seconds + timediff.days*24*3600
                    await send_reminder(secondsToSleep, int(authorID), int(channelID), newReminderMessage)
            except (asyncio.TimeoutError, ValueError, IndexError):
                await ctx.channel.send('Invalid input, canceling reminder removal')

    elif (subcommand == 'list'):
        if not ctx.message.mentions:
            # Require the user to mention someone
            await ctx.send('You must mention (@) someone!')
        elif bot.user in ctx.message.mentions:
            await ctx.send('Cannot mention (@) the bot!')
        else:
            authorID = ctx.message.mentions[0].id
            reminderFile = open('reminders.txt', 'r')
            activeReminders = []
            currentReminder = reminderFile.readline()
            while currentReminder:
                if str(authorID) in currentReminder:
                    formattedCRList = currentReminder.split()
                    # Remove member and channel IDs
                    formattedCR = ' '.join(formattedCRList[0:2] + formattedCRList[4:])
                    activeReminders.append(formattedCR)
                currentReminder = reminderFile.readline()
            if len(activeReminders) == 0:
                await ctx.send('No reminders scheduled.')
            else:
                await ctx.send('Here are all active reminders for {0}:\n'.format(ctx.message.mentions[0].mention) + 
                        '```' + '\n'.join(('{0}. {1}').format(i, str(reminder)) for i, reminder in enumerate(activeReminders, 1)) +
                        '```')

    else:
        await ctx.send('Invalid subcommand! Valid subcommands are '
                       'add, remove, list, and help.')

bot.run('bot-token') # Add bot token here to run the bot
