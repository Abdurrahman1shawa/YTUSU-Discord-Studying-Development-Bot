import threading
from classes_db_funs import *
from Bot import *
from extra_funs import validate_message
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
lock = threading.Lock()
token = os.environ['token_dev']
bot_id = os.environ['bot_dev_id']

def checking_thread():

    print("thread started")

    while True:

        time.sleep(1)

        for timer in Timers.ongoing_timers:
            print(timer.end_date)

            if datetime.utcnow() > timer.end_date and timer.server in [guild.id for guild in bot.guilds] and timer.status :

                print("finishing timer")

                channel = bot.get_channel(timer.channel)

                if timer.timer_type == "break_duration" :

                    bot.loop.create_task(channel.send(f"<@{timer.user}> Your break is over! Don't let the cycle stop rolling :person_running:"))

                else:

                    if timer.break_duration > 0 :

                        bot.loop.create_task(channel.send(
                        f"<@{timer.user}> Your {timer.timer_type} timer is over!\nHave a {timer.break_duration} minutes break, champion :fist:"))

                    else:

                        bot.loop.create_task(channel.send(f"<@{timer.user}> Your {timer.timer_type} timer is over! Well done :clap:"))


                if timer.timer_type == "study" or "work":

                    save_tm_to_user(timer)
                    save_tm_to_server(timer)
                    save_tm_to_user_servers(timer)

                    if timer.break_duration > 0 :
                        # check this squence carfully
                        break_timer = Timer(timer.user, timer.server, timer.channel, "break", timer.break_duration, 0)
                        bot.loop.create_task(break_timer.start(bot))

                else:
                    #drop break timer
                    drop_tm_from_tms(timer)

                timers.ongoing_timers.remove(timer)
                deactivate_timer(timer)
                # take and give role with excpect

bot = Bot() # the name of the object must be "bot" or the other objects will fail
servers = Servers()
servers.init_servers(bot.get_cursor())
timers = Timers()
timers.init_timers(bot.get_cursor())
thread = threading.Thread(target = checking_thread)
thread.start()

@bot.event
async def on_ready():

    print("bot lunched :)", bot.user)

    await bot.change_presence(activity = discord.Game("beta test"))

@bot.event
async def on_guild_join(guild):

    new_server = Server(guild.id)
    save_server_to_server(new_server) # add auto default settings adding
    servers.add_server(new_server)

@bot.event
async def on_message(message):

    global servers, timer
    command = None
    valid_command = False
    mai = message.author.id
    mci = message.channel.id
    msi = message.guild.id
    servers.check_server(msi)
    server = servers.get_server(msi)

    if bot.user in message.mentions:
        await message.add_reaction('\N{EYES}')

    if message.author == bot.user:
        return False

    valid_command, command = validate_message(message, server)

    if valid_command:

        if len(command) == 1 and command[0].lower() == "study":

            if not timers.chcek_timer(mai):

                study_timer = Timer(mai, msi, mci, "study", 25, 0)
                await study_timer.start(bot)

            else:
                await bot.ongoing_timer(mai, mci)

        elif len(command) == 2 and command[0].lower() == "study" and type(int(
                command[1])) is int:

            if 10 <= int(command[1]) <= 120:

                if not timers.chcek_timer(mai):

                    study_timer = Timer(mai, msi, mci, "study", int(command[1]), 0)
                    await study_timer.start(bot)

                else:
                    await bot.ongoing_timer(mai, mci)

            else:

                await message.channel.send("Your specified time duration is out of range! :eyes:")


        elif len(command) == 4 and command[0].lower() == "study" and type(int(
                command[1])) is int and command[2].lower() == "break" and type(int(
                command[3])) is int:

            if 10 <= int(command[1]) <= 120 and 5 <= int(command[3]) <= 30:

                if not timers.chcek_timer(mai):

                    study_timer = Timer(mai, msi, mci, "study", int(command[1]), int(command[3]))
                    await study_timer.start(bot)

                else:
                    await bot.ongoing_timer(mai, mci)

            else:

                await message.channel.send("Your specified time duration is out of range! :eyes:")


        elif len(command) == 1 and command[0].lower() == "work":

            if not timers.chcek_timer(mai):

                study_timer = Timer(mai, msi, mci, "work", 25, 0)
                await study_timer.start(bot)

            else:
                await bot.ongoing_timer(mai, mci)


        elif len(command) == 2 and command[0].lower() == "work" and type(int(
                command[1])) is int:

            if 10 <= int(command[1]) <= 120:

                if not timers.chcek_timer(mai):

                    study_timer = Timer(mai, msi, mci, "work", int(command[1]), 0)
                    await study_timer.start(bot)

                else:
                    await bot.ongoing_timer(mai, mci)

            else:

                await message.channel.send("Your specified time duration is out of range! :eyes:")


        elif len(command) == 4 and command[0].lower() == "work" and type(int(
                command[1])) is int and command[2].lower() == "break" and type(int(
                command[3])) is int:

            if 10 <= int(command[1]) <= 120 and 5 <= int(command[3]) <= 30:

                if not timers.chcek_timer(mai):

                    study_timer = Timer(mai, msi, mci, "work", int(command[1]), int(command[3]))
                    await study_timer.start(bot)

                else:
                    await bot.ongoing_timer(mai, mci)

            else:

                await message.channel.send("Your specified time duration is out of range! :eyes:")

        elif command[0].lower() == "rtime":

            await timers.remaining_time(mai, message.channel)

        elif len(command) == 1 and command[0].lower() == "cancel":

            await timers.stop(mai, message.channel)

        elif len(command) == 2 and command[0].lower() == "cancel" and command[1].lower() == "clear" :

            await timers.stop(mai, message.channel, save = False)

        elif len(command) == 4 and  command[0].lower() == "give" and (command[3] == "study" or command[3] == "work"):

            user = None

            if len(command[1]) == 22:

                id = command[1][3:21]
                user = bot.get_user(id)

            else:

                id = command[1][2:20]
                user = bot.get_user(id)


            if type(user) != None:
                
                print(f"giving {command[2]} {command[3]} to {id}")
                timer = Timer(id, msi, mci, command[3], command[2], 0)
                timer.end_date = datetime.utcnow()
                save_tm_to_timer(timer)
                save_tm_to_user(timer)
                save_tm_to_server(timer)
                save_tm_to_user_servers(timer)
                await message.channel.send(f"{command[2]} {command[3]} minutes given to <@{id}>")

        elif len(command) == 1 and command[0].lower() == "top"  :

            await bot.top_periodicly(server, message.channel)

        elif len(command) == 1 and command[0].lower() == "shistory"  :

            pass
            #add history fun to external file

        elif len(command) == 1 and command[0].lower() == "help"  :

            await bot.help(server, message.channel)

        elif len(command) == 2 and command[0].lower() == "help" and command[1].lower() == "admin":

            await bot.help(server, message.channel, True)

        elif len(command) == 1 and command[0].lower() == "clearrecords":

            clear_tm(server)

        else:
            await message.channel.send("invalid command")


bot.run(token)
