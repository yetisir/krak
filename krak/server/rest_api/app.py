import connexion


def main():
    app = connexion.App(__name__, specification_dir='./')
    app.add_api('swagger.yml')
    app.run(host='0.0.0.0', port=5000)


if __name__ == '__main__':
    main()
