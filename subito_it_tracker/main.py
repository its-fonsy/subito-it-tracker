import argparse

from .subito import SubitoApi, SubitoQuery
from .database import Database


def user_confirm(question: str):
    ans = input(question)
    if ans.lower() in ["y", "yes"]:
        return True
    else:
        return False


def parse_arguments():
    parser = argparse.ArgumentParser(description="Subito.it item tracker.")
    subparsers = parser.add_subparsers(dest="command")

    # Add
    subparsers.add_parser("add", help="Add a new query")

    # Remove query
    remove_query_parser = subparsers.add_parser(
        "remove", help="Remove a query")
    remove_query_parser.add_argument("id", type=int, nargs="?",
                                     default=None,
                                     help="ID of the query to remove")

    # Update
    subparsers.add_parser("update", help="Update all queries")

    # queries
    subparsers.add_parser("list", help="List all queries")

    # tracked items of query
    tracked_parser = subparsers.add_parser(
        "tracked", help="Show tracked items from a query")
    tracked_parser.add_argument("id", type=int, nargs="?", default=None,
                                help="ID of the query to track")

    # Untrack item
    untrack_item_parser = subparsers.add_parser(
        "untrack", help="Remove an item from the track list")
    untrack_item_parser.add_argument(
        "id", type=int, help="ID of the item to untrack")

    # item dump
    item_parser = subparsers.add_parser(
        "item", help="Show all information about an item")
    item_parser.add_argument(
        "id", type=int, help="ID of the item to dump")

    return parser.parse_args()


def add_query(database: Database, api: SubitoApi):
    # Ask user query to add
    title = input("Title of the query: ")
    query = input("Query: ")
    min_price = int(input("Minimum price (0 = skip): "))
    max_price = int(input("Maximum price (0 = skip): "))

    min_price = min_price if min_price > 0 else None
    max_price = max_price if max_price > 0 else None

    if user_confirm("Confirm (y/N)? "):
        query = SubitoQuery(title, query, min_price, max_price)
        id = database.insert_query(query)
        items = api.search(query)
        for item in items:
            database.insert_item(item, id)
        print(f"Query {query.title} added with id={id}")
    else:
        print("Abort.")


def remove_query(database: Database, id: int):

    if not id:
        id = int(input("ID of the query to remove: "))

    database.remove_query(id)


def list_all_queries(database: Database):
    query_id_list = database.get_all_queries_id()

    if not query_id_list:
        print("There are no queries.")
        return

    for id in query_id_list:
        query = database.get_query(id)
        print(f"({id}) {query.title} [min={
              query.min_price}, max={query.max_price}]")


def list_tracked_items(database: Database, query_id: int):
    queries_id_list = []

    if query_id:
        queries_id_list.append(query_id)
    else:
        queries_id_list = database.get_all_queries_id()

    for qid in queries_id_list:
        query = database.get_query(qid)

        if not query:
            print("Error: Invalid query ID")
            continue

        items = database.get_tracked_items_of_query(qid)
        print(f"Tracked items for ({qid}) \"{query.title}\":")
        for item in items:
            item_id = database.get_item_id(item, qid)
            print(f"    ({item_id}) {item}")


def dump_item(database: Database, item_id: int):
    item = database.get_item(item_id)
    print(item.dump())


def update_all_queries(database: Database, api: SubitoApi):
    queries = database.get_all_queries_id()

    for query_id in queries:
        query = database.get_query(query_id)
        item_to_remove = database.get_all_item_of_query(query_id)

        # Add new items to the databse
        results = api.search(query)
        for item in results:
            new_entry = database.insert_item(item, query_id)
            if new_entry:
                question = f"New item: {item.price} EUR \"{item.title}\" {
                    item.geo}.\nAdd to the list of tracked items? (y/N) "
                if user_confirm(question):
                    item_id = database.get_item_id(item, query_id)
                    database.set_tracked(item_id, True)
            else:
                item_to_remove.remove(item)

        # Remove old/sold items from the database
        for item in item_to_remove:
            item_id = database.get_item_id(item, query_id)
            if item.is_tracked():
                print(f"Item \"{item.title}\" has been probably sold")
            database.remove_item(item_id)


def main():
    args = parse_arguments()
    api = SubitoApi()

    with Database("subito.sqlite3") as db:
        if args.command == "add":
            add_query(db, api)
        elif args.command == "remove":
            remove_query(db, args.id)
        elif args.command == "update":
            update_all_queries(db, api)
        elif args.command == "list":
            list_all_queries(db)
        elif args.command == "tracked":
            list_tracked_items(db, args.id)
        elif args.command == "untrack":
            db.set_tracked(args.id, False)
        elif args.command == "item":
            dump_item(db, args.id)


if __name__ == "__main__":
    main()
