from app import connex_app


if __name__ == '__main__':
    connex_app.add_api('swagger.yml')
    connex_app.run(host='0.0.0.0', port=5001, debug=True)
