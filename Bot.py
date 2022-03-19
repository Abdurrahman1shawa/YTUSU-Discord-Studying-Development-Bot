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
