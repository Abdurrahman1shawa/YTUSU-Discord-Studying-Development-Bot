


def save_tm_to_user(timer_obj, cursor, custom_time = 0):

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

def save_tm_to_server(timer_obj, cursor, custom_time = 0):

    #cursor = bot.get_cursor("for saving the time into server table")
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

def save_tm_to_timer(timer_obj, cursor, custom_time = 0):

    # cursor = bot.get_cursor("for: saving the timer to database")
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

def save_tm_to_user_servers(timer_obj, cursor, custom_time = 0):

    #cursor = bot.get_cursor("for saving the time into user_servers table")
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

def save_server_to_server(server_obj, cursor):

    #cursor = bot.get_cursor()
    cursor.execute("""insert ignore into servers values ( {}, "{}", 0, 0, Null, Null, Null, Null, Null, 100, 500, 1000, 1500)
    """.format(server_obj.id, "&"))

    cursor.close()

def drop_tm_from_tms(timer_obj, cursor):

    # cursor = bot.get_cursor("for droping the timer from database")
    cursor.execute(f"""delete from timer
    where user_id = {timer_obj.user} and server_id = {timer_obj.server} and duration = {timer_obj.duration}""")
    print("timer droped from database")
    cursor.close()

def drop_tm_from_tms(timer_obj, cursor):

    #cursor = bot.get_cursor("for droping the timer from database")
    cursor.execute(f"""delete from timer
    where user_id = {timer_obj.user} and server_id = {timer_obj.server} and duration = {timer_obj.duration}""")
    print("timer droped from database")
    cursor.close()
