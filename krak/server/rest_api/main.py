from sqlalchemy import event
from sqlalchemy.orm import mapper

from app import connex_app
from app import tables

if __name__ == '__main__':
    event.listen(mapper, 'after_configured', tables.setup_schema)

    connex_app.add_api('swagger.yml')
    connex_app.run(host='0.0.0.0', port=5001, debug=True)
