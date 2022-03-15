
def validate_message(message, server):

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

        return valid_command, command

    else:
        return False
