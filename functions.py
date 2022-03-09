from discord import Embed
import os, threading
import mysql.connector
from dotenv import load_dotenv
from discord import Embed

class bot_functions:

    lock = threading.Lock()
    load_dotenv()
    conn_dict = {"host": os.environ['database_host'],
                 "user": os.environ['database_user'],
                 "password": os.environ['database_password'],
                 "database": os.environ['database'],
                 "autocommit": True,
                 "get_warnings": True
                 }

    @staticmethod
    def init_db():


        conn = mysql.connector.connect(**bot_functions.conn_dict)

        cursor = conn.cursor(dictionary = True)

        cursor.execute("""

        CREATE TABLE IF NOT EXISTS servers_settings (
          server_id bigint(20) DEFAULT NULL,
          prefix varchar(5) DEFAULT NULL,
          role_settings tinyint(1) DEFAULT NULL,
          auto_reset tinyint(1) DEFAULT NULL,
          next_reset datetime DEFAULT NULL,
          logs_channel_id bigint(20) DEFAULT NULL,
          reset_period smallint(6) DEFAULT NULL
          );

        """)

        cursor.execute("""

        create table if not exists users (user_id bigint unique, study_duration int, work_duration int);

        """)

        cursor.execute(""" CREATE TABLE IF NOT EXISTS timers (

          user_id bigint(20) unique,
          server_id bigint(20) DEFAULT NULL,
          channel_id bigint(20) DEFAULT NULL,
          timer_date datetime DEFAULT NULL,
          timer_duration int(11) DEFAULT NULL,
          break_duration int(11) DEFAULT NULL,
          timer_type varchar(7) DEFAULT NULL);

        """)

        cursor.execute("""

        select * from servers_settings ;

        """)

        servers_settings = cursor.fetchall()

        cursor.close()

        return servers_settings


    @staticmethod
    async def help_fun(message, admin = False):

        conn = mysql.connector.connect(**bot_functions.conn_dict)

        take_cor = conn.cursor()

        if admin:

            take_cor.execute("""select prefix from servers_settings where server_id = {}""".format(message.guild.id))

            hel = """
                    {prefix}<give/take> <@member> <x: number> <study/work>
                    Gives/Takes x study/work minutes from member.

                    {prefix}stopalltimers
                    Cancels and saves elapsed time of all ongoing timers.

                    {prefix}swroles <on/off>
                    Activates/Deactivates the studying and working roles.

                    {prefix}cleardatabase
                    Resets all saved server data on the <@> Beta database.

                    {prefix}my settings
                    Shows bot settings for the server.

                    {prefix}change prefix <prefix>
                    I mean it's obvious lol.

                    &autoreset <on/off>
                    Activates/Deactivates the auto reset mode.

                    &set logschannel
                    define the current channel as logs channel.

                    &autoreset datetime year-month-day hours:minutes:secnods
                    set the inital auto reset datetime.
                    please consider that you are using the utc time.

                    &autoreset periode x
                    set the periode of the auto reset.

                    """.format(prefix = take_cor.fetchone()[0])

        else:
            take_cor.execute("""select prefix from servers_settings where server_id = {}""".format(message.guild.id))

            hel = """
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
                    Shows the top 10 productive people of the server""".format(prefix = take_cor.fetchone()[0])

        embed = Embed(title = "Commands", description = hel)

        await message.channel.send(embed = embed)

        conn.close()


    @staticmethod
    async def save_to_database(user_id, server_id, time_duration, timer_type):
        save_conn = mysql.connector.connect(**bot_functions.conn_dict)

        save_cursor = save_conn.cursor()

        save_cursor.execute("""
        create table if not exists sql11415982.s{} (user_id bigint unique,study_time int,work_time int)
        """.format(server_id))

        if timer_type == "study":

            save_cursor.execute(f"""
            insert into s{server_id} values ({user_id}, {time_duration}, {0}) on duplicate key
            update study_time = study_time + {time_duration} ;""")

            # save_cursor.execute("""
            # insert into users values ({userid}, {studytime}, {worktime}) on duplicate key
            # update study_duration = study_duration + {studytime};
            #     """.format(serverid = server_id,
            #                userid = user_id,
            #                studytime = time_duration,
            #                worktime = 0, ))

        elif timer_type == "work":

            save_cursor.execute(f"""
            insert into s{server_id} values ({user_id}, {0}, {time_duration}) on duplicate key
            update work_time = work_time + {time_duration};
                  """)

            # save_cursor.execute("""
            # insert into users values ({userid}, {studytime}, {worktime}) on duplicate key
            # update work_duration = work_duration + {worktime}
            #       """.format(serverid = server_id,
            #                  userid = user_id,
            #                  studytime = 0,
            #                  worktime = time_duration))

        save_conn.close()


    @staticmethod
    async def give_take(message, command):

            if len(command[1]) == 22:

                u = command[1][3:21]

            else:

                u = command[1][2:20]

            if command[0] == "give":

                await bot_functions.save_to_database(u, message.guild.id, command[2], command[3])

                await message.channel.send(f"{command[2]} {command[3]} minutes given to <@{u}>")

            else:

                take_conn = mysql.connector.connect(**bot_functions.conn_dict)

                take_cor = take_conn.cursor()

                take_cor.execute(f"""
                                    update s{message.guild.id} set {command[3]}_time = {command[3]}_time - {command[2]} where user_id = {u}""")

                take_conn.close()

                await message.channel.send(f"{command[2]} {command[3]} minutes taken from <@{u}>")


    @staticmethod
    async def sw_roles(message, command):

            role_con = mysql.connector.connect(**bot_functions.conn_dict)

            role_cursor = role_con.cursor(dictionary = True)

            if command == "off":

                role_cursor.execute(
                    f"""update servers_settings set role_settings = 0 where server_id = {message.guild.id}""")

                await message.channel.send("Role giving deactivated")

            else:

                role_cursor.execute(
                    f"""update servers_settings set role_settings = 1 where server_id = {message.guild.id}""")

                await message.channel.send("Role giving activated")

            role_cursor.execute("""select * from servers_settings""")

            servers_settings = role_cursor.fetchall()

            role_con.close()

            return servers_settings
