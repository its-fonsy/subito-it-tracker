from .database import Database
from .subito import MAX_PRICE, SubitoApi, SubitoQuery


class CommandError(Exception):
    """Base for all command exceptions"""


class InvalidIdError(CommandError):
    pass


class UserAbort(CommandError):
    pass


class QueryError(CommandError):
    pass


class ItemError(CommandError):
    pass


class CommandTemplate:
    def __init__(self, api):
        self.help_string: str = ""

    def run(self):
        try:
            self.execute()
        except InvalidIdError as e:
            print(f"Error: {e}")
        except UserAbort:
            print("Aborted.")
        except KeyboardInterrupt:
            print("\nAborted.")
        except QueryError as e:
            print(f"Error: {e}")
        except ItemError as e:
            print(f"Error: {e}")

    def user_confirm(self, question: str) -> bool:
        ans = input(question)
        return ans.lower() in ["y", "yes"]

    def parse_input_id(self, input) -> int:
        try:
            id = int(input)
        except ValueError as e:
            raise InvalidIdError(f"'{input}' is not a valid integer.") from e

        if id == 0:
            raise UserAbort

        return id

    def list_all_queries(self):
        with Database() as db:
            query_id_list = db.get_all_queries_id()

            if not query_id_list:
                raise QueryError("There aren't any queries.")

            print("Queries: ")
            for id in query_id_list:
                query = db.get_query(id)
                if not query:
                    raise QueryError(f"Query '{id}' doesn't exist.")
                print(
                    f"  ({id}) {query.title} [min={query.min_price}, max={query.max_price}]"
                )

    def list_all_tracked_items_of_query(self, query_id: int):
        with Database() as db:
            # Check if query exist
            if not db.get_query(query_id):
                raise QueryError(f"Query '{query_id}' does not exist.")

            # Get tracked items
            items = db.get_tracked_items_of_query(query_id)

            # Return if list is empty
            if not items:
                raise ItemError("There aren't any tracked items.")

            # Print the list
            print("Tracked items:")
            for item in items:
                item_id = db.get_item_id(item, query_id)
                print(f"    ({item_id}) {item}")

    def execute(self) -> None:
        pass


class CommandAddQuery(CommandTemplate):
    def __init__(self, api):
        self.api: SubitoApi = api
        self.help_string = "Add a new query."

    def execute(self) -> None:
        # Ask user query to add
        title = input("Title of the query (CTRL-C to abort): ")
        query = input("Query (CTRL-C to abort): ")
        min_price = int(input("Minimum price (0 to skip): ")) or 0
        max_price = int(input("Maximum price (0 to skip): ")) or MAX_PRICE

        # Set price boundaries
        min_price = max(0, min_price)
        if max_price == 0:
            max_price = MAX_PRICE
        else:
            max_price = min(max_price, MAX_PRICE)

        if self.user_confirm("Confirm (y/N)? "):
            query = SubitoQuery(title, query, min_price, max_price)
            with Database() as db:
                id = db.insert_query(query)
            print(f"Query '{query.title}' added with id {id}")
        else:
            print("Abort.")


class CommandQuit(CommandTemplate):
    def __init__(self):
        self.help_string = "Quit from the program."


class CommandHelp(CommandTemplate):
    def __init__(self):
        self.help_string = "List all available commands."


class CommandRemoveQuery(CommandTemplate):
    def __init__(self):
        self.help_string = "Remove a query from the database."

    def execute(self):

        self.list_all_queries()

        user_input = input("Query to remove (0 to abort): ")
        id = self.parse_input_id(user_input)

        with Database() as db:
            if not db.get_query(id):
                print(f"Query '{id}' does not exist.")
                return

            db.remove_query(id)
            print(f"Query '{id}' removed")


class CommandListQuery(CommandTemplate):
    def __init__(self):
        self.help_string = "List all queries from the database."

    def execute(self):
        self.list_all_queries()


class CommandListTrackedItemsOfQuery(CommandTemplate):
    def __init__(self):
        self.help_string = "List all tracked items of a query."

    def execute(self):
        self.list_all_queries()
        user_input = input("Select query (0 to abort): ")
        query_id = self.parse_input_id(user_input)

        self.list_all_tracked_items_of_query(query_id)


class CommandGetTrackedItemInfo(CommandTemplate):
    def __init__(self):
        self.help_string = "Get all informations of an items."

    def execute(self):

        # Let user select query
        self.list_all_queries()
        user_input = input("Select query (0 to abort): ")
        query_id = self.parse_input_id(user_input)

        # Let user select item
        self.list_all_tracked_items_of_query(query_id)
        user_input = input("Select item (0 to abort): ")
        item_id = self.parse_input_id(user_input)

        # Dump item info
        with Database() as db:
            item = db.get_item(item_id)

            if not item:
                raise ItemError(f"Item '{item_id}' doesn't exist.")

            print(item.dump())


class CommandUpdateAllQueries(CommandTemplate):
    def __init__(self, api):
        self.api: SubitoApi = api
        self.help_string = "Update all queries."

    def execute(self):
        with Database() as db:
            queries = db.get_all_queries_id()

            for query_id in queries:
                query = db.get_query(query_id)

                if not query:
                    continue

                item_to_remove = db.get_all_items_of_query(query_id)

                # Search for ADV
                print(f"Update query '{query.title}'")
                results = self.api.search(query)

                # Remove ADV that doesn't meet requirements
                for item in results:
                    new_entry = db.insert_item(item, query_id)

                    if new_entry:
                        question = (
                            f"  New item: {item.price} EUR '{item.title}' {item.geo}."
                        )
                        question += "\nTrack this item? (y/N) "

                        if self.user_confirm(question):
                            item_id = db.get_item_id(item, query_id)
                            db.set_tracked(item_id, True)

                    else:
                        item_to_remove.remove(item)

                # Remove old/sold items from the db
                for item in item_to_remove:
                    item_id = db.get_item_id(item, query_id)
                    if item.is_tracked():
                        print(f'Item "{item.title}" has been probably sold.')
                    db.remove_item(item_id)
