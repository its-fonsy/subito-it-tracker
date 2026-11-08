import argparse
from . import __version__
from .subito import SubitoApi
from .command import (
    CommandAddQuery,
    CommandQuit,
    CommandHelp,
    CommandRemoveQuery,
    CommandListTrackedItemsOfQuery,
    CommandListQuery,
    CommandGetTrackedItemInfo,
    CommandUpdateAllQueries,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tracker for Subito.it.")
    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}"
    )
    return parser.parse_args()


def main() -> None:

    parse_arguments()

    api = SubitoApi()
    commands = {
        "add": CommandAddQuery(api),
        "remove": CommandRemoveQuery(),
        "queries": CommandListQuery(),
        "track": CommandListTrackedItemsOfQuery(),
        "info": CommandGetTrackedItemInfo(),
        "update": CommandUpdateAllQueries(api),
        "quit": CommandQuit(),
        "help": CommandHelp(),
    }
    user_input = ""

    while user_input not in ["quit"]:
        try:
            user_input = input("tracker> ")
            if not user_input:
                continue
        except KeyboardInterrupt:
            print()
            break

        user_cmd = user_input.split()[0]

        # Check if command is valid
        if user_cmd not in commands:
            print(f"Invalid command `{user_cmd}`. Type 'help' for a list of commands.")
            continue

        # Help command
        if user_cmd == "help":
            print("Available commands:")
            for name, cmd in commands.items():
                print(f"  {name.ljust(10)}{cmd.help_string}")
            continue

        commands[user_cmd].run()


if __name__ == "__main__":
    main()
