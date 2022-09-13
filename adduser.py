from werkzeug.security import generate_password_hash
import json

def cli():
    import argparse
    parser = argparse.ArgumentParser(description='Host the Docs')
    parser.add_argument('--user', help='Username')
    parser.add_argument('--password', help='Password')
    args = parser.parse_args()
    from hostthedocs import getconfig
    #  Command line script using argparse for adding a user: --user john --password hello
    if args.user and args.password:
        try:
            with open(getconfig.user_db) as f:
                users = json.load(f)
        except FileNotFoundError:
            users = {}
        verb = "Added"
        if args.user in users:
            verb = "Updated"
        users[args.user] = generate_password_hash(args.password)

        print(f"{verb} user: {args.user}")
        with open(getconfig.user_db, 'w') as f:
            json.dump(users, f, indent=4, sort_keys=True)
        return

if __name__ == '__main__':
    cli()
