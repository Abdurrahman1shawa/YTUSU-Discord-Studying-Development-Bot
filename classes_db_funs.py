import time
from datetime import datetime, timedelta
import discord
import mysql.connector
import os
from dotenv import load_dotenv
from tabulate import tabulate
load_dotenv()

class Bot(discord.Client):

    conn_dict = {"host": os.environ['database_host_heroku'],
                 "user": os.environ['database_user_heroku'],
                 "password": os.environ['database_password_heroku'],
                 "database": os.environ['database_heroku'],
                 "autocommit": True,
                 "get_warnings": True
                 }
    connection = mysql.connector.connect(**conn_dict)


    def __init__(self):
        super().__init__() # related with the inhertince
        print("Bot/Client successfully initiated")
        #guilds = self.guilds

    @classmethod
    def get_cursor(cls, s = "", dictionary = True):

        print("getting cursor",s)

        if cls.connection.is_connected() :
            print("connection is already exist")

            return cls.connection.cursor(dictionary = True)

        else :
            print("opening a new connection")
            cls.connection = mysql.connector.connect(**cls.conn_dict)
            return cls.connection.cursor(dictionary = True)

    async def ongoing_timer(self, user_id, channel):

        channel = self.get_channel(channel)
        await channel.send(f" <@{user_id}>Slow down! You're already have an ongoing timer :face_with_monocle:")

    async def top_periodicly(self, server, channel):

        cursor = self.get_cursor()
        cursor.execute(f"""
        select distinct user_id from timer where server_id = {server.id}
        """)
        guild = await self.fetch_guild(server.id)
        print()
        the_most_productive_people = []
        users = cursor.fetchall()
        print(users)
        number = 0
        for user in users:

            number += 1
            cursor.execute(f"""
            select sum(duration) from timer where user_id = {user["user_id"]} and server_id = {server.id}
            """)
            productive_time = cursor.fetchone()["sum(duration)"]
            print(productive_time)
            the_most_productive_people.append([number, (await guild.fetch_member(user["user_id"])).nick, productive_time])

        final_table = "And here are our top productive people!!\n```\n{}\n```".format(
            str(tabulate(the_most_productive_people, headers = ["#", "Name", "Productive Time"], numalign = "right")))

        embed = discord.Embed(title = "leaderboard", description = final_table)

        await channel.send(embed = embed)

    async def help(self, server, channel, admin = False):

        if admin:
            help = """
                    **{prefix}<give/take> <@member> <x: number> <study/work>**
                    Gives/Takes x study/work minutes from member.

                    **{prefix}stopalltimers**
                    Cancels and saves elapsed time of all ongoing timers.

                    **{prefix}swroles <on/off>**
                    Activates/Deactivates the studying and working roles.

                    **{prefix}cleardatabase**
                    Resets all saved server data on the <@> Beta database.

                    **{prefix}my settings**
                    Shows bot settings for the server.

                    **{prefix}change prefix <prefix>**
                    I mean it's obvious lol.

                    **&autoreset <on/off>**
                    Activates/Deactivates the auto reset mode.

                    **&set logschannel**
                    define the current channel as logs channel.

                    **&autoreset datetime year-month-day hours:minutes:secnods**
                    set the inital auto reset datetime.
                    please consider that you are using the utc time.

                    **&autoreset periode x**
                    set the periode of the auto reset.

                    """.format(prefix = server.prefix)
            embed = discord.Embed(title = "Admin's Commands", description = help)


        else:

            help = """
                    **{prefix}[study/work]**
                    creates a 25 minutes study/work timer.

                    **{prefix}[study/work] x**
                    Creates an x minutes study/work timer. (10 < x < 120)

                    **{prefix}[study/work] x break y**
                    Creates an x minutes study/work timer, followed by a y minutes break timer.
                    (10 < x < 120) (5 < y < 30)

                    **{prefix}cancel**
                    Cancels and saves (if exists) the remaining time of the ongoing timer.

                    **{prefix}cancel clear**
                    Cancels (if exists) the ongoing timer.

                    **{prefix}rtime**
                    Shows the remaining time for the end of the ongoing timer (if a timer exists).

                    **{prefix}top**
                    Shows the top 10 productive people of the server""".format(prefix = server.prefix)

            embed = discord.Embed(title = "User's Commands", description = help)

        await channel.send(embed = embed)

    async def give(self, server_id, channel_obj, tag, duration, type):

        user = str()

        if len(tag) == 22:

            id = tag[3:21]
            print(id)
            user = await self.fetch_user(id)

        else:

            id = tag[2:20]
            print(id)
            user = await self.fetch_user(id)

        print(user)
        if user is not None:
            print(f"giving {duration} {type} to {id}")
            timer = Timer(id, server_id, channel_obj.id, type, duration, 0)
            timer.end_date = datetime.utcnow()
            save_tm_to_timer(timer)
            save_tm_to_user(timer)
            save_tm_to_server(timer)
            save_tm_to_user_servers(timer)

        return id

    async def productivity(self, server_id, user_id):

        cursor = Bot.get_cursor()
        cursor.execute(f"""select sum(server_studied_time + server_worked_time) from user_servers
        where user_id = {user_id} and server_id = {server_id}""")
        score = cursor.fetchone()["sum(server_studied_time + server_worked_time)"]

        return score

    async def my_recoreds(self, server_id, user_id):

        cursor = Bot.get_cursor()
        cursor.execute(f"""select timer_type, duration, end_date from timer
        where user_id = {user_id} and server_id = {server_id} order by end_date""")
        timers = cursor.fetchall()
        recoreds = []

        for timer in timers:
            print(timer)
            recoreds.append([timer["timer_type"], timer["duration"], timer["end_date"] + timedelta(hours = 3)])


        final_recoreds = "and here is your invaluble study records \n```\n{}\n```".format(
        tabulate(recoreds, headers = ["Type", "Duration", "Date"], numalign = "right" )
        )

        embed = discord.Embed(title = "recoreds", description = final_recoreds)

        return embed

class Timers:

    ongoing_timers = []

    def __init__(self):
        pass

    def init_timers(self, cursor):

        start = time.time()
        print("loading ongoing timers")
        cursor.execute("select * from timer")
        timers = cursor.fetchall()

        for tim in timers:

            if tim["status"]:

                self.ongoing_timers.append(Timer(
                                   user_id = tim["user_id"],
                                   server_id = tim["server_id"],
                                   channel_id = tim["channel_id"],
                                   end_date = tim["end_date"],
                                   duration = tim["duration"],
                                   break_duration = tim["break_duration"],
                                   timer_type = tim["timer_type"],
                                   status = tim["status"],
                                   id = tim["id"]
                                   ))
        end = time.time()
        print(f"{len(self.ongoing_timers)}","ongoing timers loaded successfully", f"{end-start}"+"s")
        cursor.close()

    def get_timer(self, user_id):

        print("searching for ongoing timer")

        for timer in self.ongoing_timers:

            if timer.user == user_id and timer.status == True:

                print("ongoing timer found")
                return timer

        print("ongoing timer not found")
        return False

    def chcek_timer(self, user_id):

        print("checking for ongoing timer")

        for timer in self.ongoing_timers:

            if timer.user == user_id:

                print("ongoing timer found")
                return True

        print("ongoing timer not found")
        return False

    async def remaining_time(self, user_id, channel):

        timer = self.get_timer(user_id)

        if timer :

            await channel.send(
                "There are still {} {} minutes to go! Be patient :sparkles:"
                .format(timer.calculate_remaining_timer(), timer.timer_type))

        else:
            await channel.send("You have to create a timer before doing that :upside_down:")

    async def stop(self, user_id, channel, save = True):

        if not self.chcek_timer(user_id) :

            await channel.send("There's no ongoing timer to be canceled :person_shrugging:")
            return

        timer = self.get_timer(user_id)

        if timer.timer_type == "break": # don't save any break timers

            save = False

        if save:

            duration = timer.duration
            elapsedtime = duration - timer.calculate_remaining_timer()
            timer.status = False
            save_tm_to_user(timer, elapsedtime) # edit the save function to be efficent to work with stop method
            save_tm_to_user_servers(timer, elapsedtime)
            save_tm_to_server(timer, elapsedtime)

            await channel.send(
                "<@{}>  {} timer canceled and {} minutes saved! I hope you have a good reason for this :new_moon_with_face:".format(
                    timer.user, timer.timer_type, elapsedtime))

            #await give_take_role(self.user, server_id, timer["timer_type"], "take")

        else:

            await channel.send(
                "<@{}>  {} timer canceled and **didn't save!** I hope you have a good reason for this :new_moon_with_face:".format(
                    timer.user, timer.timer_type))

        self.ongoing_timers.remove(timer)
        deactivate_timer(timer)

    @classmethod
    async def finish(cls, timer_obj, channel):

                print("finishing timer")

                if timer_obj.timer_type == "break_duration" :

                    await channel.send(f"<@{timer_obj.user}> Your break is over! Don't let the cycle stop rolling :person_running:")

                else:

                    if timer_obj.break_duration > 0 :

                        await channel.send(
                        f"<@{timer_obj.user}> Your {timer_obj.timer_type} timer is over!\nHave a {timer_obj.break_duration} minutes break, champion :fist:")

                    else:

                        await channel.send(f"<@{timer_obj.user}> Your {timer_obj.timer_type} timer is over! Well done :clap:")


                if timer_obj.timer_type == "study" or "work":

                    save_tm_to_user(timer_obj)
                    save_tm_to_server(timer_obj)
                    save_tm_to_user_servers(timer_obj)

                    if timer_obj.break_duration > 0 :
                        # check this squence carfully
                        break_timer = Timer(timer_obj.user, timer_obj.server, timer_obj.channel, "break", timer_obj.break_duration, 0)
                        await break_timer.start(bot)

                else:
                    #drop break timer
                    drop_tm_from_tms(timer_obj)

                cls.ongoing_timers.remove(timer_obj)
                deactivate_timer(timer_obj)


class Timer:

    def __init__(self, user_id, server_id, channel_id, timer_type, duration, break_duration, end_date = None, status = False, id = None):

            self.id = id # very important
            self.user = user_id
            self.server = server_id
            self.channel = channel_id
            self.duration = duration
            self.break_duration = break_duration
            self.end_date = end_date
            self.timer_type = timer_type
            self.status = status
            print("a new timer initiated")

    async def start(self, bot_obj):

        print("starting timer")
        self.end_date = timedelta(seconds = self.duration) + datetime.utcnow()
        self.status = True
        channel = bot_obj.get_channel(self.channel)
        save_tm_to_timer(self)

        if self.id is None:
            cursor = Bot.get_cursor("setting the timer id")
            cursor.execute(f"""select id from timer where user_id = {self.user} and status = 1""")
            self.id = cursor.fetchall()[0]["id"]
            print(self.id)

        Timers.ongoing_timers.append(self)
        await channel.send(
            f"<@{self.user}> Your {self.timer_type} timer has started! See you in {self.duration} minutes! :fire: ")

        #await give_take_role(user_id, self.server, timer_type, "give")
        print("timer started")

    def calculate_remaining_timer(self):

        print("clculating remaining time")
        temp = self.end_date - datetime.utcnow()
        elapsedtime = round(temp.total_seconds() / 60)
        print(f"remaining time = {elapsedtime}" )
        return elapsedtime # can be seperated

class Servers:

    def __init__(self):
        self.servers_list = []
        print("getting servers' settings")

    def init_servers(self, cursor): # get the servers' settings from DB

        cursor.execute("select * from servers")
        result = cursor.fetchall()

        for server_ in result:

            self.servers_list.append(Server(server_["id"],
                                            server_["prefix"],
                                            server_["sw_roles_settings"],
                                            server_["auto_reset"],
                                            server_["next_reset"],
                                            server_["reset_period"],
                                            server_["logs_channel_id"],
                                            server_["total_studied_time"],
                                            server_["total_worked_time"]
                                            ))
        cursor.close()
        print("servers' settings loaded successfully")

    def get_server(self, server_id):

        for server in self.servers_list:

            if server.id == server_id:

                return(server)

    def check_server(self, server_id):

        for serv in self.servers_list:

            if serv.id == server_id:

                return True

        ser = Server(server_id, "&") # error local variable 'server' referenced before assignment
        save_server_to_server(ser, bot.get_cursor())
        self.servers_list.append(ser)

    def add_server(self, server_obj):
        self.servers_list.append(server_obj)

class Server:

    def __init__(self, server_id, prefix = "&", role_settings = False,
                auto_reset = False, next_reset = None, reset_period = None,
                logs_channel_id = None, total_studied_time = None, total_worked_time = None):

        self.id = server_id
        self.prefix = prefix
        self.role_settings = role_settings
        self.autoreset = auto_reset
        self.next_reset = next_reset
        self.logs_channel = logs_channel_id
        self.reset_period = reset_period
        self.total_studied_time = total_studied_time
        self.total_worked_time = total_worked_time

class User:

    def __init__(self):
        pass

def save_tm_to_user(timer_obj,  custom_time = 0):

    cursor = Bot.get_cursor()
    duration = timer_obj.duration

    if custom_time > 0:

        duration = custom_time

    if timer_obj.timer_type == "study":

        cursor.execute(f"""insert into user
        (id, total_studied_time, total_worked_time)
        values ({timer_obj.user}, {duration}, 0)
        on duplicate key update
        total_studied_time = total_studied_time + {duration}""")


    elif timer_obj.timer_type == "work":

        cursor.execute(f"""insert into user
        (id, total_studied_time, total_worked_time)
        values ({timer_obj.user}, 0,{duration})
        on duplicate key update
        total_worked_time = total_worked_time + {duration}""")


    cursor.close()

def save_tm_to_server(timer_obj, custom_time = 0):

    cursor = Bot.get_cursor("for saving the time into server table")
    duration = timer_obj.duration

    if custom_time > 0:

        duration = custom_time

    if timer_obj.timer_type == "study":

        cursor.execute(f"""update servers set
        total_studied_time = total_studied_time + {duration}
        where id = {timer_obj.server}""")



    elif timer_obj.timer_type == "work":

        cursor.execute(f"""update servers set
        total_worked_time = total_worked_time + {duration}
        where id = {timer_obj.server}""")

    cursor.close()

def save_tm_to_timer(timer_obj, custom_time = 0):

    cursor = Bot.get_cursor("for: saving the timer to database")
    cursor.execute("""insert into timer
    (user_id, server_id, channel_id, end_date, duration, break_duration, timer_type, status)
    values ("{}","{}","{}","{}","{}","{}","{}",{});
    """.format(timer_obj.user,
               timer_obj.server,
               timer_obj.channel,
               timer_obj.end_date,
               timer_obj.duration,
               timer_obj.break_duration,
               timer_obj.timer_type,
               timer_obj.status))
    cursor.close()
    print("the timer saved to database")

def save_tm_to_user_servers(timer_obj, custom_time = 0):

    cursor = Bot.get_cursor("for saving the time into user_servers table")
    cursor.execute(f"""
    select user_id, server_id from user_servers
    where user_id = {timer_obj.user} AND server_id = {timer_obj.server}
    """)
    result = len(cursor.fetchall())
    duration = timer_obj.duration

    if custom_time > 0:

        duration = custom_time

    if timer_obj.timer_type == "study":

        if result == 0:

            cursor.execute(f"""
            insert into user_servers (server_id, user_id, server_studied_time,
            server_worked_time, goal)
            values ({timer_obj.server}, {timer_obj.user}, {duration}, 0, 0)
            """)

        else:

            cursor.execute(f"""
            update user_servers set
            server_studied_time = server_studied_time + {duration}
            where server_id = {timer_obj.server} AND user_id = {timer_obj.user}

            """)

    elif timer_obj.timer_type == "work":

        if result == 0:

            cursor.execute(f"""
            insert into user_servers (server_id, user_id, server_studied_time,
            server_worked_time, goal)
            values ({timer_obj.server}, {timer_obj.user}, {0}, {duration}, 0)

            """)

        else:

            cursor.execute(f"""
            update user_servers set
            server_worked_time = server_worked_time + {duration}
            where user_id = {timer_obj.user} AND server_id = {timer_obj.server}
            """)

    cursor.close()

def save_server_to_server(server_obj):

    cursor = Bot.get_cursor()
    cursor.execute("""insert ignore into servers values ( {}, "{}", 0, 0, Null, Null, Null, Null, Null, 100, 500, 1000, 1500)
    """.format(server_obj.id, "&"))

    cursor.close()

def drop_tm_from_tms(timer_obj):

    cursor = Bot.get_cursor("for droping the timer from database")
    cursor.execute(f"""delete from timer
    where user_id = {timer_obj.user} and server_id = {timer_obj.server} and duration = {timer_obj.duration}""")
    print("timer droped from database")
    cursor.close()

def deactivate_timer(timer_obj ):
    cursor = Bot.get_cursor()
    cursor.execute(f"update timer set status = {0} where id = {timer_obj.id}")

def clear_tm(server):
    cursor = Bot.get_cursor()
    cursor.execute(f"delete from timer where status = {0} and server_id = {server.id}")
