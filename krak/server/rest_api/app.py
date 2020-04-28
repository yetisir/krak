import connexion


def main():
    app = connexion.App(__name__, specification_dir='swagger/')
    app.add_api('my_api.yml')
    app.run(port=8080)
