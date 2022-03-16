import time
from datetime import datetime, timedelta
from Bot import Bot

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

class Timer(Timers):

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



    elif timer_objtimer_type == "work":

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
    cursor.execute(f"update timer set status = 0 where id = {timer_obj.id}")
