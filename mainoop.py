import threading
import time
import discord
import mysql.connector
import os, asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from tabulate import tabulate
from functions import bot_functions

#قم بتعديل الغاء المؤقت من قاعدة البيانات عند الانتهاء منه لتصبح تعديل الحالة الى غير فعال بدل ذلك

load_dotenv()
lock = threading.Lock()
token = os.environ['token_dev']
bot_id = os.environ['bot_dev_id']

class bot(discord.Client):

    def __init__(self):

        super().__init__()
        print("bot/Client initiated")
        self.conn_dict = {"host": os.environ['database_host_heroku'],
                     "user": os.environ['database_user_heroku'],
                     "password": os.environ['database_password_heroku'],
                     "database": os.environ['database_heroku'],
                     "autocommit": True,
                     "get_warnings": True
                     }
        self.connection = mysql.connector.connect(**self.conn_dict)
        print("connected to database")

    def init_checking_thread(self):

        thread = threading.Thread(target = self.checking_thread)
        thread.start()

    def checking_thread(self):

        print("thread started")

        while True:

            time.sleep(1)

            for timer in timers.ongoing_timers:
                print(timer.end_date, type(timer.end_date))

                if datetime.utcnow() > timer.end_date and timer.server in [guild.id for guild in bot.guilds] :
                    print(datetime.utcnow(), timer.end_date)

                    channel = bot.get_channel(timer.channel)

                    if timer.timer_type == "break_duration" :

                        #async function need to be awaited
                        bot.loop.create_task(channel.send(f"<@{timer.user}> Your break is over! Don't let the cycle stop rolling :person_running:"))

                    else:

                        if timer.break_duration > 0 :

                            bot.loop.create_task(channel.send(
                            f"<@{timer.user}> Your {timer.timer_type} timer is over!\nHave a {timer.break_duration} minutes break, champion :fist:"))

                        else:

                            bot.loop.create_task(channel.send(f"<@{timer.user}> Your {timer.timer_type} timer is over! Well done :clap:"))


                    if timer.timer_type == "study" or "work":

                        timer.save_tm_to_user()
                        timer.save_tm_to_server()
                        timer.save_tm_to_user_servers()

                    if timer.break_duration > 0 :
                        # check this squence carfully
                        break_timer = timer(timer.user, timer.server, timer.channel, "break", timer.break_duration, 0)

                    # add fun. to change the status of the timers to 0
                    timers.ongoing_timers.remove(timer)
                    timer.deactivate_timer()
                    # take and give role

    def get_cursor(self, s = "", dictionary = True):

        print("getting cursor",s)

        if self.connection.is_connected() :
            print("connection is already exist")

            return self.connection.cursor(dictionary = True)

        else :
            print("opening a new connection")
            self.connection = mysql.connector.connect(**self.conn_dict)
            return self.connection.cursor(dictionary = True)

    async def ongoing_timer(self, user_id, channel):

        channel = self.get_channel(channel)
        await channel.send(f" <@{user_id}>Slow down! You're already have an ongoing timer :face_with_monocle:")


class timers:

    def __init__(self):

        self.ongoing_timers = []


    def init_timers(self):

        start = time.time()
        print("loading ongoing timers")
        cursor = bot.get_cursor()
        cursor.execute("select * from timer")
        timers = cursor.fetchall()

        for tim in timers:

            if tim["status"]:

                self.ongoing_timers.append(timer(
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
            print(timer)

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

        timer = timers.get_timer(user_id)

        if timer :

            await channel.send(
                "There are still {} {} minutes to go! Be patient :sparkles:"
                .format(timer.calculate_remaining_timer(), timer.timer_type))

        else:
            await channel.send("You have to create a timer before doing that :upside_down:")


    async def stop(self, user_id, channel, save = True):

        channel = bot.get_channel(channel)

        if not timers.chcek_timer(user_id) :

            await channel.send("There's no ongoing timer to be canceled :person_shrugging:")
            return

        timer = timers.get_timer(user_id)
        print

        if timer.timer_type == "break": # don't save any break timers

            save = False

        if save:

            duration = timer.duration
            elapsedtime = duration - timer.calculate_remaining_timer()
            timer.status = False
            timer.save_tm_to_user(elapsedtime) # edit the save function to be efficent to work with stop method
            timer.save_tm_to_user_servers(elapsedtime)
            timer.save_tm_to_server(elapsedtime)

            await channel.send(
                "<@{}>  {} timer canceled and {} minutes saved! I hope you have a good reason for this :new_moon_with_face:".format(
                    timer.user, timer.timer_type, elapsedtime))

            #await give_take_role(self.user, server_id, timer["timer_type"], "take")

        else:

            await channel.send(
                "<@{}>  {} timer canceled and **didn't save!** I hope you have a good reason for this :new_moon_with_face:".format(
                    timer.user, timer.timer_type))

        timers.ongoing_timers.remove(timer)
        #timer.drop_tm_from_tms()


class timer(timers):

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


    async def start(self):

        print("starting timer")
        self.end_date = timedelta(seconds = self.duration) + datetime.utcnow()
        self.status = True
        channel = bot.get_channel(self.channel)
        self.save_tm_to_timer()

        if self.id is None:
            cursor = bot.get_cursor("setting the timer id")
            cursor.execute(f"""select id from timer where user_id = {self.user} and status = 1""")
            self.id = cursor.fetchall()[0]["id"]
            print(self.id)

        timers.ongoing_timers.append(self)
        await channel.send(
            f"<@{self.user}> Your {self.timer_type} timer has started! See you in {self.duration} minutes! :fire: ")

        #await give_take_role(user_id, self.server, timer_type, "give")
        print("timer started")


    def save_tm_to_timer(self):

        cursor = bot.get_cursor("for: saving the timer to database")
        cursor.execute("""insert into timer
        (user_id, server_id, channel_id, end_date, duration, break_duration, timer_type, status)
        values ("{}","{}","{}","{}","{}","{}","{}",{});
        """.format(self.user,
                   self.server,
                   self.channel,
                   self.end_date,
                   self.duration,
                   self.break_duration,
                   self.timer_type,
                   self.status))
        cursor.close()
        print("the timer saved to database")

    def drop_tm_from_tms(self):

        cursor = bot.get_cursor("for droping the timer from database")
        cursor.execute(f"""delete from timer
        where user_id = {self.user} and server_id = {self.server} and duration = {self.duration}""")
        print("timer droped from database")
        cursor.close()

    def calculate_remaining_timer(self):

        print("clculating remaining time")
        temp = self.end_date - datetime.utcnow()
        elapsedtime = round(temp.total_seconds() / 60)
        print(f"remaining time = {elapsedtime}" )
        return elapsedtime

    def save_tm_to_user(self, custom_time = 0):

        cursor = bot.get_cursor("for saving the time into user table")
        duration = self.duration

        if custom_time > 0:

            duration = custom_time

        if self.timer_type == "study":

            cursor.execute(f"""insert into user
            (id, total_studied_time, total_worked_time)
            values ({self.user}, {duration}, 0)
            on duplicate key update
            total_studied_time = total_studied_time + {duration}""")


        elif self.timer_type == "work":

            cursor.execute(f"""insert into user
            (id, total_studied_time, total_worked_time)
            values ({self.user}, 0,{duration})
            on duplicate key update
            total_worked_time = total_worked_time + {duration}""")


        cursor.close()

    def save_tm_to_server(self, custom_time = 0):

        cursor = bot.get_cursor("for saving the time into server table")
        duration = self.duration

        if custom_time > 0:

            duration = custom_time

        if self.timer_type == "study":

            cursor.execute(f"""update servers set
            total_studied_time = total_studied_time + {duration}
            where id = {self.server}""")



        elif self.timer_type == "work":

            cursor.execute(f"""update servers set
            total_worked_time = total_worked_time + {duration}
            where id = {self.server}""")

        cursor.close()

    def save_tm_to_user_servers(self, custom_time = 0):

        cursor = bot.get_cursor("for saving the time into user_servers table")
        cursor.execute(f"""
        select user_id, server_id from user_servers
        where user_id = {self.user} AND server_id = {self.server}
        """)
        result = len(cursor.fetchall())
        duration = self.duration

        if custom_time > 0:

            duration = custom_time

        if self.timer_type == "study":

            if result == 0:

                cursor.execute(f"""
                insert into user_servers (server_id, user_id, server_studied_time,
                server_worked_time, goal)
                values ({self.server}, {self.user}, {duration}, 0, 0)
                """)

            else:

                cursor.execute(f"""
                update user_servers set
                server_studied_time = server_studied_time + {duration}
                where server_id = {self.server} AND user_id = {self.user}

                """)

        elif self.timer_type == "work":

            if result == 0:

                cursor.execute(f"""
                insert into user_servers (server_id, user_id, server_studied_time,
                server_worked_time, goal)
                values ({self.server}, {self.user}, {0}, {duration}, 0)

                """)

            else:

                cursor.execute(f"""
                update user_servers set
                server_worked_time = server_worked_time + {duration}
                where user_id = {self.user} AND server_id = {self.server}
                """)

        cursor.close()

    def deactivate_timer(self):

        cursor = bot.get_cursor("disabling timer")
        cursor.execute(f"update timer set status = 0 where id = {self.id}")

class server:

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


    def save_to_db(self):

        cursor = bot.get_cursor()

        cursor.execute("""insert ignore into servers values ( {}, "{}", 0, 0, Null, Null, Null, Null, Null, 100, 500, 1000, 1500)

        """.format(self.id, "&"))
        cursor.close()



class servers:

    def __init__(self):

        print("getting servers' settings")
        self.servers_list = []
        cursor = bot.get_cursor()
        cursor.execute("select * from servers")
        result = cursor.fetchall()

        for server_ in result:

            self.servers_list.append(server(server_["id"],
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

        ser = server(server_id, "&") # error local variable 'server' referenced before assignment
        ser.save_to_db()
        self.servers_list.append(ser)



class user:

    def __init__(self):
        pass

bot = bot()
servers = servers()
timers = timers()
timers.init_timers()
bot.init_checking_thread()

@bot.event
async def on_ready():

    print("bot lunched :)", bot.user)

    await bot.change_presence(activity = discord.Game("beta test"))

@bot.event
async def on_guild_join(guild):

    pass # add auto default settings adding


@bot.event
async def on_message(message):

    global servers, timer
    command = None
    valid_command = False
    mai = message.author.id
    mci = message.channel.id
    msi = message.guild.id

    if message.author == bot.user:
        return

    if bot.user in message.mentions:
        await message.add_reaction('\N{EYES}')

    servers.check_server(msi)
    server = servers.get_server(msi)

    if message.content.startswith(server.prefix):

        command = message.content.split()

        if len(command[0]) != server.prefix:

            temp = command[0].split(server.prefix)

            command[0] = temp[1]
            valid_command = True
            print(command)

        else:

            command.remove(command[0])
            valid_command = True
            print(command)


    if valid_command:

        if len(command) == 1 and command[0].lower() == "study":

            if not timers.chcek_timer(mai):

                study_timer = timer(mai, msi, mci, "study", 25, 0)
                await study_timer.start()

            else:
                await bot.ongoing_timer(mai, mci)

        elif len(command) == 2 and command[0].lower() == "study" and type(int(
                command[1])) is int:

            if 10 <= int(command[1]) <= 120:

                study_timer = timer(mai, msi, mci, "study", int(command[1]), 0)
                await study_timer.start()

            else:

                await message.channel.send("Your specified time duration is out of range! :eyes:")

        elif command[0].lower() == "rtime":

            await timers.remaining_time(mai, message.channel)

        elif len(command) == 1 and command[0].lower() == "cancel":

            await timers.stop(mai, mci)

        elif len(command) == 2 and command[0].lower() == "cancel" & command[1].lower() == "clear" :

            await timers.stop(mai, mci, save = False)

        elif command[0].lower() == "give" and len(command) == 4 and (command[3] == "study" or command[3] == "work"):

            user = int()

            if len(command[1]) == 22:

                user = command[1][3:21]

            else:

                user = command[1][2:20]

            timer = timer(user, msi, mci, "study", 10, 0)
            timer.save_tm_to_user()
            timer.save_tm_to_server()
            timer.save_tm_to_user_servers()

        elif command[0].lower() == "shistory" and len(command) == 4 :

            pass
            #add history fun to external file

        else:
            await message.channel.send("invalid command")


bot.run(token)
