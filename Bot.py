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
