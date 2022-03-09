import threading
import time
from datetime import datetime, timedelta
import discord
import mysql.connector
import os
from dotenv import load_dotenv
from tabulate import tabulate
from functions import bot_functions

load_dotenv()
lock = threading.Lock()

token = os.environ['token']

bot_id = os.environ['bot_beta_id']

client = discord.Client()

conn_dict = {"host": os.environ['database_host'],
             "user": os.environ['database_user'],
             "password": os.environ['database_password'],
             "database": os.environ['database'],
             "autocommit": True,
             "get_warnings": True
             }

servers_settings = bot_functions.init_db()


async def tim_start(user_id, server_id, channel_id, timer_duration, break_duration, timer_type, message = None):
    tim_conn = mysql.connector.connect(**conn_dict)

    tim_cor = tim_conn.cursor()

    info = {"found": False, "timer_type": ""}

    timedt = (timedelta(minutes = timer_duration) + datetime.utcnow()).strftime('%Y-%m-%d %H:%M:%S')

    tim_cor.execute(
        f"""select * from timers where user_id = {user_id} and server_id = {server_id} and channel_id = {channel_id} ;""")

    timer = tim_cor.fetchone()

    if timer != None and timer[0] == user_id and timer[1] == server_id and "break" != timer_type:
        info = {"found": True, "timer_type": timer[6]}

        await message.channel.send(
            f"<@{user_id}>Slow down! You're already have an ongoing {info['timer_type']} timer :face_with_monocle:")

        return

    if not info["found"]:
        tim_cor.execute("""insert into sql11415982.timers
        (user_id, server_id, channel_id, timer_date, timer_duration, break_duration, timer_type)
        values ("{}","{}","{}","{}","{}","{}","{}");
    """.format(user_id, server_id, channel_id, timedt, timer_duration, break_duration, timer_type))

        await give_take_role(user_id, server_id, timer_type, "give")

        if message is not None:

            await message.channel.send(
                f"<@{user_id}> Your {timer_type} timer has started! See you in {timer_duration} minutes! :fire: ")

        else:
            channel = client.get_channel(channel_id)

            await channel.send(
                f"<@{user_id}> Your {timer_type} timer has started! See you in {timer_duration} minutes! :fire: ")

    tim_conn.close()


async def timer_cancel(message, user_id, server_id, save = True):
    cancel_conn = mysql.connector.connect(**conn_dict)

    a = dict()

    a["timerfound"] = False

    cancel_cor = cancel_conn.cursor()

    cancel_cor.execute(f"select * from timers where user_id = {user_id} and server_id = {server_id}")

    timer = cancel_cor.fetchone()

    if timer != None and timer[0] == user_id and timer[1] == server_id:

        a["timerfound"] = True

        a["timertype"] = timer[6]

        ts = timer[3] - datetime.utcnow()

        ts = timer[4] - round(ts.total_seconds() / 60)

        a["elapsedtime"] = ts

        if save:

            await bot_functions.save_to_database(timer[0], timer[1], ts, timer[6])

            await message.channel.send(
                "<@{}>  {} timer canceled and {} minutes saved! I hope you have a good reason for this :new_moon_with_face:".format(
                    message.author.id, a["timertype"], a["elapsedtime"]))

        await give_take_role(user_id, server_id, timer[6], "take")

        cancel_cor.execute(
            """delete from timers where user_id = {} and server_id = {} and timer_duration = {}""".format(timer[0],
                                                                                                          timer[1],
                                                                                                          timer[4]))


    if not a["timerfound"]:
        await message.channel.send("There's no ongoing timer to be canceled :person_shrugging:")

    elif not save:
        await message.channel.send(
            "<@{}>  {} timer canceled and didn't save! I hope you have a good reason for this :new_moon_with_face:".format(
                message.author.id, a["timertype"], a["elapsedtime"]))

    cancel_conn.close()


async def give_take_role(user_id, server_id, timer_type, action):

    global bot_id
    server = await client.fetch_guild(server_id)
    bot = await server.fetch_member(bot_id)
    prim = False

    for ser in servers_settings:
        if server_id == ser["server_id"]:
            prim = ser["role_settings"]


    if prim and bot.guild_permissions.manage_roles:

        user = await server.fetch_member(user_id)

        if timer_type == "work":

            work = discord.utils.get(server.roles, name = "Working")


            if work is None:
                work = await server.create_role(name = "Working")
                work.hosit = True

            if action == "take":

                await user.remove_roles(work)

            elif action == "give":

                await user.add_roles(work)


        elif timer_type == "study":

            study = discord.utils.get(server.roles, name = "Studying")


            if study is None:
                study = await server.create_role(name = "Studying")
                study.hosit = True

            if action == "take":

                await user.remove_roles(study)

            elif action == "give":

                await user.add_roles(study)


async def clear_db(channel, server_id):

    if type(channel) == int:

        channel = client.get_channel(channel)

    clear_conn = mysql.connector.connect(**conn_dict)

    clear_cor = clear_conn.cursor()

    clear_cor.execute(f"""TRUNCATE TABLE s{server_id} ;""")

    clear_cor.close()

    if channel == None:
        return

    await channel.send("https://tenor.com/view/thanos-finger-snap-disappear-gif-13174976")

    await channel.send("Boom! Timers have been reset")

async def leaderboard(server_id, channel):

    if type(channel) == int :

        channel = client.get_channel(channel)

    if channel == None:
        return

    top_conn = mysql.connector.connect(**conn_dict)

    top_cor = top_conn.cursor()

    top_cor.execute(f"""select * from s{server_id} order by work_time + study_time desc""")

    data = top_cor.fetchall()

    if len(data) == 0:

        await channel.send(
            "No one has studied ever yet here! What are you looking for?! :thinking:")

        top_conn.close()

        return

    i = 0

    s = list()

    for drow in data:

        i += 1

        s.append([
            f"{i}-", await client.fetch_user(drow[0]),
            drow[1], drow[2]])

    s = "And here are our top productive people!!\n```\n{}\n```".format(
        str(tabulate(s, headers = ["#", "Name", "Study", "Work"], numalign = "right")))

    embed = discord.Embed(title = "Leaderboard", description = s)

    await channel.send(embed = embed)

    await channel.send("The race is on")

    await channel.send("https://media.discordapp.net/attachments/824405271433838602/852561064594767872/tenor5.gif")

    top_conn.close()


def timer_check():

    global servers_settings

    exthread_conn = mysql.connector.connect(**conn_dict)

    exthread_cor1 = exthread_conn.cursor(dictionary = True)

    print("Database connection status:" , exthread_conn.is_connected())

    while True:

        time.sleep(1)

        if not exthread_conn.is_connected() :

            exthread_conn = mysql.connector.connect(**conn_dict)

            exthread_cor1 = exthread_conn.cursor(dictionary = True)

            print("connection status:" , exthread_conn.is_connected())

        else:

            exthread_cor1 = exthread_conn.cursor(dictionary = True)

        exthread_cor1.execute("""select * from timers """)

        timers = exthread_cor1.fetchall()

        exthread_cor1.execute("""select * from servers_settings""")

        servers_settings = exthread_cor1.fetchall()

        today = datetime.utcnow()

        for key in timers:

            if datetime.utcnow() > key["timer_date"] and key["server_id"] in [guild.id for guild in client.guilds] :

                channel = client.get_channel(key["channel_id"])

                if key["timer_type"] == "break":

                    client.loop.create_task(channel.send(
                        "<@{}> Your break is over! Don't let the cycle stop rolling :person_running:".format(
                            key["user_id"])))

                else:

                    if key["break_duration"] > 0:

                        client.loop.create_task(channel.send(
                            "<@{}> Your {} timer is over!\nHave a {} minutes break, champion :fist:".format(key["user_id"],
                                                                                                            key["timer_type"],
                                                                                                            key["break_duration"])))

                    else:

                        client.loop.create_task(
                            channel.send("<@{}> Your {} timer is over! Well done :clap:".format(key["user_id"], key["timer_type"])))

                if key["timer_type"] == "study" or key["timer_type"] == "work":
                    client.loop.create_task(bot_functions.save_to_database(key["user_id"], key["server_id"], key["timer_duration"], key["timer_type"]))

                if key["break_duration"] > 0:
                    client.loop.create_task(tim_start(key["user_id"], key["server_id"], key["channel_id"], key["break_duration"], 0, "break"))

                exthread_cor1.execute(
                    """delete from timers where user_id = {} and server_id = {} and timer_duration = {}""".format(
                        key["user_id"], key["server_id"], key["timer_duration"]))

                client.loop.create_task(give_take_role(key["user_id"], key["server_id"], key["timer_type"], "take"))

        for set in servers_settings :

            if set["auto_reset"] and  set["server_id"] in [guild.id for guild in client.guilds] :

                if set["next_reset"] is not None and set["reset_period"] is not None and set["next_reset"] <= today :

                    print(today, set["next_reset"])

                    if set["logs_channel_id"] is not None :

                        client.loop.create_task(leaderboard(set["server_id"], set["logs_channel_id"]))

                    client.loop.create_task(clear_db(set["logs_channel_id"], set["server_id"]))

                    next_reset = today + timedelta(days = set["reset_period"])

                    print(next_reset)

                    exthread_cor1.execute("""update servers_settings set next_reset = "{}" where server_id = {}
                    """.format(next_reset.strftime('%Y-%m-%d %H:%M:%S'), set["server_id"]))



@client.event
async def on_guild_join(guild):
    global servers_settings, lock
    init_set_conn = mysql.connector.connect(**conn_dict)
    init_set_cursor = init_set_conn.cursor()
    init_set_cursor.execute("""

    insert ignore into servers_settings values ( {}, "{}", 0, 0, Null, Null, Null)

    """.format(guild.id, "&"))

    init_set_cursor.execute("""

    create table if not exists sql11415982.s{} (user_id bigint unique,study_time int,work_time int)

    """.format(guild.id))

    init_set_cursor.execute("""

    select * from servers_settings ;

    """)

    with lock:
        servers_settings = init_set_cursor.fetchall()

    init_set_cursor.close()


@client.event
async def on_ready():
    print("bot lunched :)", client.user)

    await client.change_presence(activity = discord.Game("beta test"))


@client.event
async def on_message(message):

    global command, servers_settings

    valid_command = False

    mc = int(message.channel.id)

    mai = int(message.author.id)

    msi = int(message.guild.id)

    if message.author == client.user:
        return

    if client.user in message.mentions:
        await message.add_reaction('\N{EYES}')
        await message.add_reaction('<:iq1234:852616026055376896>')

    for server in servers_settings:

        if message.content.startswith(server["prefix"]) and msi == server["server_id"]:

            global temp_server_settings
            temp_server_settings = server

            command = message.content.split()

            if len(command[0]) != len(server["prefix"]):

                u = command[0].split(server["prefix"])

                command[0] = u[1]

                print(command)
                valid_command = True
                break

            else:

                command.remove(command[0])
                valid_command = True
                print(command)
                break

    if valid_command:

        if len(command) == 1 and command[0].lower() == "study":

            t = 25

            await tim_start(mai, msi, mc, t, 0, "study", message)


        elif len(command) == 2 and command[0].lower() == "study" and type(int(
                command[1])) is int:

            if 10 <= int(command[1]) <= 120:

                await tim_start(mai, msi, mc, int(command[1]), 0, "study",message)

            else:

                await message.channel.send("Your specified time duration is out of range! :eyes:")

        elif len(command) == 4 and command[0].lower() == "study" and command[2].lower() == "break":

            if type(int(command[1])) == int and type(int(command[3])) == int:

                if 10 <= int(command[1]) <= 120 and 5 <= int(command[3]) <= 30:

                    await tim_start(mai, msi, mc, int(command[1]), int(command[3]), "study",message)

                else:

                    await message.channel.send("Your specified time duration is out of range! :eyes:")

        elif len(command) == 1 and command[0].lower() == "work":

            t = 25

            await tim_start(mai, msi, mc, t, 0, "work", message)

        elif len(command) == 2 and command[0].lower() == "work" and type(int(
                command[1])) == int:

            if 10 <= int(command[1]) <= 120:

                await tim_start(mai, msi, mc, int(command[1]), 0, "work", message)

            else:

                await message.channel.send("Your specified time duration is out of range! :eyes:")

        elif len(command) == 4 and command[0].lower() == "work" and command[2].lower() == "break":

            if type(int(command[1])) == int and type(int(command[3])) == int:

                if 10 <= int(command[1]) <= 120 and 5 <= int(command[3]) <= 30:

                    await tim_start(mai, msi, mc, int(command[1]), int(command[3]), "work", message)

                else:

                    await message.channel.send("Your specified time duration is out of range! :eyes:")

        elif command[0].lower() == "top" and len(command) == 1:

            await leaderboard(msi, message.channel.id)

        elif command[0].lower() == "cancel" and len(command) == 1:

            await timer_cancel(message, mai, msi, True)

        elif len(command) == 2 and command[0].lower() == "cancel" and command[1].lower() == "clear":

            await timer_cancel(message, mai, msi, False)

        elif command[0].lower() == "rtime" and len(command) == 1:

            rtime_conn = mysql.connector.connect(**conn_dict)

            rtime_cor = rtime_conn.cursor()

            rtime_cor.execute("select * from timers")

            rtime_timer_list = rtime_cor.fetchall()

            s = False

            for key in rtime_timer_list:

                if key[0] == mai and key[1] == msi:
                    s = True
                    ts = key[3] - datetime.utcnow()

                    ts = round(ts.total_seconds() / 60)

                    await message.channel.send(
                        "There are still {} {} minutes to go! Be patient :sparkles:".format(ts, key[6]))

                    rtime_cor.close()

            if not s:
                rtime_cor.close()

                await message.channel.send("You have to create a timer before doing that :upside_down:")

        elif command[0].lower() == "help" and len(command) == 1:

            await bot_functions.help_fun(message)

        elif command[0].lower() == "help" and command[1].lower() == "admin" and len(command) == 2:

            await bot_functions.help_fun(message, True)

        elif command[0].lower() == "give" and len(command) == 4 and (command[3] == "study" or command[3] == "work"):

            if message.author.guild_permissions.manage_channels:

                await bot_functions.give_take(message, command)

            else:
                await message.channel.send(
                    "you are not allowed to use this command you have to get manage **channels permission** to use this command")

        elif command[0].lower() == "take" and len(command) == 4 and (command[3] == "study" or command[3] == "work"):

            await bot_functions.give_take(message, command)

        elif command[0].lower() == "cleardatabase" and len(command) == 1:

            if message.author.guild_permissions.manage_channels:

                await clear_db(mc ,msi)

            else:

                await message.channel.send(
                    "you are not allowed to use this command you have to get manage **channels permission** to use this command")

        elif command[0].lower() == "stopalltimers" and len(command) == 1:

            if message.author.guild_permissions.manage_channels:

                stop_conn = mysql.connector.connect(**conn_dict)
                stop_cor = stop_conn.cursor()

                stop_cor.execute(f"""select * from timers where server_id = {msi}""")

                cache_tim = stop_cor.fetchall()

                for tim in cache_tim:
                    await timer_cancel(message, tim[0], tim[1], True)

                await message.channel.send("timers have been stopped and saved")

                stop_conn.close()

            else:

                await message.channel.send(
                    "you are not allowed to use this command you have to get manage **channels permission** to use this command")

        elif command[0].lower() == "ntimer" and len(command) == 1:

            ntimer_conn = mysql.connector.connect(**conn_dict)

            ntimer_cor = ntimer_conn.cursor()

            ntimer_cor.execute("select count(*) from timers")

            await message.channel.send("there is {} ongoing timer :fire:".format(ntimer_cor.fetchall()[0][0]))

            ntimer_conn.close()

        elif command[0].lower() == "change" and command[1].lower() == "prefix" and len(command) == 3:

            if message.author.guild_permissions.manage_channels:

                role_con = mysql.connector.connect(**conn_dict)

                role_cursor = role_con.cursor(dictionary = True)

                role_cursor.execute(
                    """update servers_settings set prefix = "{}" where server_id = {}""".format(command[2], message.guild.id))

                role_cursor.execute("""select * from servers_settings""")

                with lock:
                    servers_settings = role_cursor.fetchall()

                await message.channel.send("prefix successfully changed")

                role_con.close()

            else:

                await message.channel.send(
                    "you are not allowed to use this command you have to get manage **channels permission** to use this command")

        elif command[0].lower() == "swroles" and command[1].lower() == "on" and len(command) == 2:

            if message.author.guild_permissions.manage_channels:

                with lock:
                    servers_settings = await bot_functions.sw_roles(message, command[1].lower())

            else:
                await message.channel.send(
                    "you are not allowed to use this command you have to get manage roles permission to use this command")

        elif command[0].lower() == "swroles" and command[1].lower() == "off" and len(command) == 2:

            if message.author.guild_permissions.manage_channels:

                with lock:
                    servers_settings = await bot_functions.sw_roles(message, command[1].lower())

            else:
                await message.channel.send(
                    "you are not allowed to use this command you have to get manage roles permission to use this command")

        elif command[0].lower() == "my" and command[1].lower() == "settings" and len(command) == 2:

            if message.author.guild_permissions.manage_channels:

                role_con = mysql.connector.connect(**conn_dict)
                role_cursor = role_con.cursor(dictionary = True)

                role_cursor.execute("""select * from servers_settings where server_id = {}""".format(message.guild.id))

                server = role_cursor.fetchone()

                role_con.close()

                if server["role_settings"]:
                    r = "ON"
                else:
                    r = "OFF"

                if server["auto_reset"]:
                    ar = "ON"

                else:
                    ar = "OFF"

                if server["logs_channel_id"] is not None:
                    lc = client.get_channel(server["logs_channel_id"]).name
                else:
                    lc = "Not set"

                await message.channel.send(
"""Your settings are:
Prefix: " **{}** "
Roles giving: **{}**
Logs channel: **{}**
Auto reset: **{}**
Auto reset periode: **{}**
Auto reset date: **{} UTC**
""".format(server["prefix"], r, lc, ar,server["reset_period"] , server["next_reset"]))

            else:

                await message.channel.send(
                    "you are not allowed to use this command you have to get manage **channels permission** to use this command")

        elif len(command) == 3 and command[0].lower() == "autoreset" and command[1].lower() ==  "periode" and type(int(command[2])) == int:

            if message.author.guild_permissions.manage_channels :

                    if command[2] == 0:

                        await message.channel.send("invalid periode")
                        return

                    conn = mysql.connector.connect(**conn_dict)

                    cursor = conn.cursor(dictionary = True)

                    cursor.execute(f"update servers_settings set reset_period = {command[2].lower()} where server_id = {msi}")

                    cursor.execute("select * from servers_settings")

                    with lock:
                        servers_settings = cursor.fetchall()

                    conn.close()

                    await message.channel.send("auto reset periode has set")

            else:

                await message.channel.send(
                    "you are not allowed to use this command you have to get manage **channels permission** to use this command")

        elif len(command) == 4 and command[0].lower() == "autoreset" and command[1].lower() == "datetime" :

            if message.author.guild_permissions.manage_channels :

                try:

                    input = f"{command[2].lower()} {command[3].lower()}"

                    date = datetime.strptime(input, '%Y-%m-%d %H:%M:%S')

                    conn = mysql.connector.connect(**conn_dict)

                    cursor = conn.cursor()

                    cursor.execute("""update servers_settings set next_reset = "{}" where server_id = {}""".format(date, msi))

                    cursor.execute("select * from servers_settings")

                    with lock:
                        servers_settings = cursor.fetchall()

                    conn.close()

                    await message.channel.send("""auto reset date has set.
Note: in order to lunche auto reset properly please make sure that reset periode is set""")

                except:

                    await message.channel.send("Invalid syntax \n please make sure to use the folowing syntax \n Y-m-d H:M:S")

            else:

                await message.channel.send(
                "you are not allowed to use this command you have to get manage **channels permission** to use this command")

        elif len(command) == 2 and command[0].lower() == "autoreset" :

            if message.author.guild_permissions.manage_channels:

                conn = mysql.connector.connect(**conn_dict)

                cursor = conn.cursor(dictionary = True)

                if command[1].lower() == "on":

                    cursor.execute(f"update servers_settings set auto_reset = 1 where server_id = {msi}")

                    cursor.execute("select * from servers_settings")

                    with lock:
                        servers_settings = cursor.fetchall()

                    await message.channel.send("Auto reset activated")

                elif command[1].lower() == "off" :

                    cursor.execute(f"update servers_settings set auto_reset = 0 where server_id = {msi}")

                    cursor.execute("select * from servers_settings")

                    with lock:
                        servers_settings = cursor.fetchall()

                    await message.channel.send("Auto reset deactivated")

                else:

                    await message.channel.send("Invalid syntax")

            else:
                await message.channel.send(
                    "you are not allowed to use this command you have to get manage **channels permission** to use this command")

        elif len(command) == 2 and command[0].lower() == "set" and command[1] == "logschannel":

            if message.author.guild_permissions.manage_channels:

                conn = mysql.connector.connect(**conn_dict)

                cur = conn.cursor(dictionary = True)

                cur.execute(f"update servers_settings set logs_channel_id = {mc} where server_id = {msi}")

                cur.execute("select * from servers_settings")

                with lock:
                    servers_settings = cur.fetchall()

                await message.channel.send("logs channel set")


                conn.close()

            else:
                await message.channel.send(
                    "you are not allowed to use this command you have to get manage **channels permission** to use this command")

        else:

            await message.channel.send("invalid command")


time_worker = threading.Thread(target = timer_check)

time_worker.start()

client.run(token)
