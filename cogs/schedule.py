import discord
from discord.ext import commands, tasks
import os
import json
import asyncio
import datetime
import calendar

class Schedule(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self._schedules_json_path = os.path.join(
                                        os.path.dirname(
                                            os.path.realpath(__file__)), 
                                        'schedules.json')
        self._full_schedule = None
    
    @commands.Cog.listener()
    async def on_ready(self):
        # Ensure that a file for schedules exists in this same directory
        with open(f'{self._schedules_json_path}', 'a+') as schedule_file:
            schedule_file.seek(0, 0)
            full_schedule = {}
            try:
                full_schedule = json.load(schedule_file)
            except json.decoder.JSONDecodeError:
                print('No valid schedule found, will create a new one.')
            finally:
                rewrite_file_needed = False
                for guild in self.bot.guilds:
                    guild_id = str(guild.id)
                    if guild_id not in full_schedule:
                        full_schedule[guild_id] = {}
                        rewrite_file_needed = True
                self._full_schedule = full_schedule
                if rewrite_file_needed:
                    json.dump(full_schedule, schedule_file, indent=4)
        
        # Ensure the proper "scheduled" role exists
        for guild in self.bot.guilds:
            if not any(role.name == 'Scheduled by Bot' 
                       for role in guild.roles):
                await guild.create_role(name="Scheduled by Bot", 
                                        mentionable=True)
        
        self.update_scheduled_roles.start()
    
    @commands.command()
    @commands.has_permissions(manage_roles=True)
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

        full_schedule = self._full_schedule
        author_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)

        if (subcommand == 'set'):
            if len(args) == 0:
                await ctx.send('Set your schedule using this command! '
                               'Creates a new schedule for the user if '
                               'none already exist, or erases the old '
                               'schedule entirely should the user confirm '
                               'their intent. \n'
                               'Supported syntax is of the form '
                               '```!schedule set [weekday] [start time] - '
                               '[end time], [other weekday] [start time] - '
                               '[end time] and [start time] - [end time], '
                               '...```\n'
                               'where start and end times for a single '
                               '"shift" are separated by a dash, '
                               'different "shifts" in a day are separated '
                               'by the "*and*" keyword, and different days '
                               'are separated by a comma. '
                               'This subcommand is also case-insensitive. \n'
                               'Some in-practice examples of supported '
                               'syntax are as follows: \n'
                               '```'
                               '!schedule set Monday 8 AM - 12 PM\n'
                               '!schedule set Monday 8:00 - 13:00\n'
                               '!schedule set Thursday 1 PM - 5:30 PM\n'
                               '!schedule set Tue 12:00 - 20:00, Wed '
                               '10:00 - 20:00\n'
                               '!schedule set Tue 8:00 - 12:00 and '
                               '15:00 - 20:00'
                               '```\n'
                               '**Currently does not support overnight '
                               'scheduling!**')
                return
            if (author_id in full_schedule[guild_id]
                    and full_schedule[guild_id][author_id]):
                await ctx.send('**WARNING!** You already have a schedule on '
                               'file. Using the "set" subcommand now will '
                               'completely reset your schedule, deleting '
                               'all of the old information.\n'
                               'Are you sure you wish to do a complete reset '
                               'of your schedule? Please type "yes" or "no".')
                try:
                    def check(m):
                        return (m.channel == ctx.message.channel
                                and m.author == ctx.message.author)
                    reply = await self.bot.wait_for('message', timeout=60, 
                                                    check=check)
                    if reply.content == 'yes':
                        # Do nothing and continue with schedule reset
                        pass
                    elif reply.content == 'no':
                        await ctx.send('Cancelling schedule reset. Use the '
                                       '*change* subcommand to modify your '
                                       'schedule without resetting it '
                                       'completely.')
                        return
                    else:
                        raise ValueError('User typed something other than '
                                         'yes/no')
                except (asyncio.TimeoutError, ValueError):
                    await ctx.send('Invalid input received. Cancelling '
                                   'schedule reset. Please try again, or use '
                                   'the *change* subcommand to modify your '
                                   'schedule without resetting it '
                                   'completely.')
                    return

            new_user_schedule = {'0' : [], '1' : [], '2' : [], 
                                 '3' : [], '4' : [], '5' : [],
                                 '6' : []}
            
            try:
                new_user_schedule = self._parse_user_input_times(
                                        ctx, args, new_user_schedule)
            except ValueError:
                await ctx.send('Invalid input format. Please try again! You '
                            'can type "!schedule" for more information on '
                            'valid formatting.')
                return

            full_schedule[guild_id][author_id] = new_user_schedule
            self._full_schedule = full_schedule
            with open(f'{self._schedules_json_path}', 'w') as schedule_file:
                json.dump(full_schedule, schedule_file, indent=4)
            await ctx.send('New availability schedule successfully set!')
        elif (subcommand == 'change'):
            if len(args) == 0:
                await ctx.send('Use this command to change certain days in '
                               'your schedule, or add shifts for a new day! '
                               'Uses the same syntax as the "!schedule set" '
                               'subcommand, i.e.:'
                               '```!schedule set [weekday] [start time] - '
                               '[end time], [other weekday] [start time] - '
                               '[end time] and [start time] - [end time], '
                               '...```\n'
                               'where start and end times for a single '
                               '"shift" are separated by a dash, '
                               'different "shifts" in a day are separated '
                               'by the "*and*" keyword, and different days '
                               'are separated by a comma.\n'
                               'If there were any old scheduled times in '
                               'the day(s) that you wish to change, this '
                               'subcommand will overwrite them completely.')
                return
            if (author_id in full_schedule[guild_id]
                    and full_schedule[guild_id][author_id]):
                await ctx.send('**WARNING!** You already have a schedule on '
                               'file. Using the "change" subcommand now will '
                               'reset all of the days that you '
                               'have mentioned in your message, if schedule '
                               'times already exist for them.'
                               'All of the old information will be deleted, '
                               'leaving behind only the new times that you '
                               'have typed in. \n'
                               'Are you sure you wish to continue with the '
                               'schedule change? Please type "yes" or "no".')
                try:
                    def check(m):
                        return (m.channel == ctx.message.channel
                                and m.author == ctx.message.author)
                    reply = await self.bot.wait_for('message', timeout=60, 
                                                    check=check)
                    if reply.content == 'yes':
                        # Do nothing and continue with schedule change
                        pass
                    elif reply.content == 'no':
                        await ctx.send('Cancelling schedule change. '
                                       'Please try again once you are ready.')
                        return
                    else:
                        raise ValueError('User typed something other than '
                                         'yes/no')
                except (asyncio.TimeoutError, ValueError):
                    await ctx.send('Invalid input received, cancelling '
                                   'schedule change. Please try again.')
                    return

            user_schedule = full_schedule[guild_id][author_id]
            try:
                user_schedule = self._parse_user_input_times(
                                    ctx, args, user_schedule)
            except ValueError:
                await ctx.send('Invalid input format. Please try again! You '
                            'can type "!schedule" for more information on '
                            'valid formatting.')
                return

            full_schedule[guild_id][author_id] = user_schedule
            self._full_schedule = full_schedule
            with open(f'{self._schedules_json_path}', 'w') as schedule_file:
                json.dump(full_schedule, schedule_file, indent=4)
            await ctx.send('Availability schedule successfully changed!')
        elif (subcommand == 'view'):
            if author_id not in full_schedule[guild_id]:
                await ctx.send('Did not find a schedule on file for you!')
                return
            
            embed = discord.Embed(title="Schedule for " 
                                        + str(ctx.message.author) + ": ")
            
            user_schedule = full_schedule[guild_id][author_id]
            for day in user_schedule:
                if user_schedule[day]:
                    field_name = calendar.day_name[int(day)] + ': '
                    field_value = ''
                    newline = ''
                    for shift in user_schedule[day]:
                        field_value += newline
                        field_value += shift[0] + ' - ' + shift[1]
                        newline = "\n"
                    embed.add_field(name=field_name, value=field_value, 
                                    inline=False)
            
            await ctx.send(embed=embed)
        elif (subcommand == 'clear'):
            await ctx.send('Are you sure you want to **completely clear** '
                           'your schedule? Type "yes" if you are sure.')
            try:
                def check(m):
                    return (m.channel == ctx.message.channel
                            and m.author == ctx.message.author)
                reply = await self.bot.wait_for('message', timeout=60, 
                                                check=check)
                if reply.content == 'yes':
                    if author_id in self._full_schedule[guild_id]:
                        self._full_schedule[guild_id].pop(author_id)
                        with open(f'{self._schedules_json_path}', 'w') as f:
                            json.dump(self._full_schedule, f, indent=4)
                        await ctx.send('Schedule successfully cleared!')
                    else:
                        await ctx.send('Did not find a schedule for you '
                                       'on file, so it was already cleared!')
                else:
                    await ctx.send('Cancelling schedule clear.')
                    return
            except asyncio.TimeoutError:
                await ctx.send('No input received. Cancelling '
                               'schedule clear. Please try again.')

    def _parse_user_input_times(self, ctx, args, user_schedule):
        weekdays = {'sunday': '6', 'monday': '0', 'tuesday': '1', 
                    'wednesday': '2', 'thursday': '3', 'friday': '4', 
                    'saturday': '5'}
        
        full_message = ((' ').join(args)).lower()
        input_by_days = [day.strip() 
                            for day in full_message.split(',')]

        # Handle each day in user input
        for day in input_by_days:
            day_args = day.split(' ', 1)
            current_day = None

            original_number_of_weekdays = len(weekdays)
            inputted_day = day_args[0]
            for weekday in weekdays:
                if (inputted_day == weekday 
                        or inputted_day == weekday[0:3]):
                    current_day = weekdays[weekday]
                    weekdays.pop(weekday)
                    break
            # disallow mentioning the same day twice
            if len(weekdays) == original_number_of_weekdays:
                raise ValueError('User did not enter a valid weekday')
            
            # Handle every set of start and end times within a day
            parsed_shift_datetimes = []
            times_in_day_string = [time.strip() 
                                for time in day_args[1].split('and')]
            for time_string in times_in_day_string:
                times = [time.strip() 
                            for time in time_string.split('-')]
                start_and_end_datetimes = []
                def parse_time(time_string, format): 
                    return datetime.datetime.strptime(
                                                time_string, format)
                for time in times:
                    # Run through all accepted cases of user input, 
                    # i.e. "x:xxpm", "x:xx pm", "x pm", and "xx:xx"
                    try:
                        start_and_end_datetimes.append(
                            parse_time(time, "%I:%M%p"))
                        continue
                    except ValueError:
                        pass
                    try:
                        start_and_end_datetimes.append(
                            parse_time(time, "%I:%M %p"))
                        continue
                    except ValueError:
                        pass
                    try:
                        start_and_end_datetimes.append(
                            parse_time(time, "%I%p"))
                        continue
                    except ValueError:
                        pass
                    try:
                        start_and_end_datetimes.append(
                            parse_time(time, "%I %p"))
                        continue
                    except ValueError:
                        pass
                    try:
                        start_and_end_datetimes.append(
                            parse_time(time, "%H:%M"))
                        continue
                    except ValueError:
                        pass

                    raise ValueError('Invalid input, could not parse')
                
                start_datetime = start_and_end_datetimes[0]
                end_datetime = start_and_end_datetimes[1]
                start_time_in_minutes = (start_datetime.hour*60
                                            + start_datetime.minute)
                end_time_in_minutes = (end_datetime.hour*60
                                        + end_datetime.minute)
                if (start_time_in_minutes > end_time_in_minutes):
                    raise ValueError('End time is earlier than start '
                                        'time')

                for shift in parsed_shift_datetimes:
                    other_start = (shift[0].hour*60 
                                    + shift[0].minute)
                    other_end = (shift[1].hour*60 
                                    + shift[1].minute)
                    if ((end_time_in_minutes > other_start
                            and start_time_in_minutes < other_end)
                        or (start_time_in_minutes < other_end
                            and end_time_in_minutes > other_start)):
                        raise ValueError('Invalid input, as '
                                            'scheduled times overlap')

                parsed_shift_datetimes.append(start_and_end_datetimes)

            complete_day = [[datetime.datetime.strftime(time, "%H:%M")
                                for time in shift]
                                for shift in parsed_shift_datetimes]
            user_schedule[current_day] = complete_day

        return user_schedule

    @tasks.loop(minutes=1.0)
    async def update_scheduled_roles(self):
        today = datetime.datetime.now()
        todays_time = today.strftime("%H:%M")
        for guild_id in self._full_schedule:
            for user_id in self._full_schedule[guild_id]:
                try:
                    guild = self.bot.get_guild(int(guild_id))
                    member = guild.get_member(int(user_id))
                    role = discord.utils.get(
                                guild.roles, name='Scheduled by Bot')
                    times = (self._full_schedule[guild_id][user_id]
                                            [str(today.weekday())])
                    remove_role = True
                    has_role = any(member_role.name == 'Scheduled by Bot' 
                                   for member_role in member.roles)
                    for time in times:
                        if ((time[0] < todays_time or time[0] == todays_time)
                                and (todays_time < time[1] 
                                     or todays_time == time[1])):
                            if not has_role:
                                await member.add_roles(role)
                            remove_role = False
                            break
                    if remove_role:
                        if has_role:
                            await member.remove_roles(role)
                except KeyError:
                    pass


def setup(bot):
    bot.add_cog(Schedule(bot))