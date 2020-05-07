from cryptography.fernet import Fernet
import pymysql
import cryptography
import json
import os

SECURITY_PATH = './security'
SECURITY_KEY_PATH = './security/key.key'
SECURITY_CONFIG_PATH = './security/config.obj'
CONFIG_PATH = './config.json'

def y_n_choice(msg = 'Do you want to continue?'):
    choice = input(msg + ' [Y/n] ')
    return True if (choice == 'Y' or choice == 'y' or choice == '') else False

def setup():

    # Check if the system has been initialized
    if os.path.exists(CONFIG_PATH):
        print('A configuration is detected, are you sure to continue?')
        print('WARNING: DOING SO WILL RESULT IN THE LOST OF ALL ')
        print('         PREVIOUS CONFIGURATION!')
        print('NOTE: You may want to checkout config.json before reinitializing.')
        if not y_n_choice():
            exit()

    # Promopt the adminstrator for db info
    print('\nPlease enter the URL of the database')
    db_url = input('(Default: 127.0.0.1): ') or '127.0.0.1'
    print('\nPlease enter the username of the database')
    db_username = input('(Default: root): ') or 'root'
    print('\nPlease enter the password of the database')
    db_password = input('(Default: None): ') or ''
    print('\nPlease enter the name of the database')
    db_name = input('(Default: mooli):') or 'mooli'

    # Attempt to connect to the database
    try:
        connection = pymysql.connect(db_url, db_username, db_password)
    except:
        # Incorrect db credential or internal error
        print('\nERROR Unable to connect to database.\n')
        exit()

    init_db(connection, db_name)

    if not os.path.exists(SECURITY_PATH):
        os.mkdir(SECURITY_PATH)

    # Generate a random key for config encryption
    key = Fernet.generate_key()
    key_file = open(SECURITY_KEY_PATH, 'wb')
    key_file.write(key)
    key_file.close()

    # Write config for security information
    security_profile = {
        'DB_USERNAME': db_username,
        'DB_PASSWORD': db_password,
        'DB_NAME': db_name,
        'SECRET_KEY': str(Fernet.generate_key())
    }
    with open(SECURITY_CONFIG_PATH, 'wb') as encrypted_profile:
        f = Fernet(key)
        encrypted_profile.write(f.encrypt(json.dumps(security_profile).encode()))

    print('Would you like to enable HTTPS on your server?')
    print('NOTE: You will need a SSL certificate to use HTTPS.')
    print('WARNING: Certain function will be disabled without HTTPS for')
    print('         security concerns.')
    enable_https = y_n_choice('Your choice ')
    if enable_https:
        print('The default configuration for you SSL certificate location is: ')
        print(' - Certificate Path: ./security/cert.pem')
        print(' - Private Key Path: ./security/privkey.pem')
        print('We recommend storing the cetificates outside the project folder')
        print('For more information, please refer to the READEME included.')
    print('\nPlease enter the port the application will be running on')
    port = ''
    if enable_https:
        port = input('(Default: 443): ') or '443'
    else:
        port = input('(Default: 80): ') or '80'
    print('\nWould you like to disable debugging on your server?')
    print('NOTE: Keep it disabled in production mode.')
    debug = not y_n_choice('Your choice ')
    config = {
        'DB_URL': db_url,
        'port': port,
        'enable_https': enable_https,
        'cert_path': './security/cert.pem',
        'private_key_path': './security/privkey.pem',
        'debug': debug
    }

    with open(CONFIG_PATH, 'w') as profile:
        profile.write(json.dumps(config))

    print('\nSetup complted.')

def init_db(connection, db_name):
    cursor = connection.cursor()

    print('\nConnection with database established.\n')

    # Check if the database exists
    cursor.execute("""SHOW DATABASES LIKE %(db_name)s""", {'db_name': db_name})
    if cursor.fetchone() is not None:
        print('The database already exists, are you sure to continue the initialization?')
        print('WARNING: DOING SO WILL RESULT IN THE LOST OF ALL EXISTING DATA!')
        if not y_n_choice():
            return

    # Initialize the database
    cursor.execute('DROP DATABASE IF EXISTS {}'.format(db_name))
    cursor.execute('CREATE DATABASE IF NOT EXISTS {}'.format(db_name))
    cursor.execute('USE {}'.format(db_name))

    # Initialize tables
    init_db_tables(connection)

    connection.close()

def init_db_tables(connection):

    print('Initiaizing database tables...\n')
    cursor = connection.cursor()

    sqls = [
        """CREATE TABLE IF NOT EXISTS permission (permission_name VARCHAR(32), group_name VARCHAR(32))""",
        """CREATE TABLE IF NOT EXISTS staff (
            staff_id INT(5) UNSIGNED AUTO_INCREMENT,
            username VARCHAR(24) NOT NULL,
            password_hash BINARY(60) NOT NULL,
            permission_group_name VARCHAR(32),
            PRIMARY KEY (staff_id),
            UNIQUE (username)
            )
        """,
        """ALTER TABLE staff AUTO_INCREMENT=10000""",
        """CREATE TABLE IF NOT EXISTS customer (
            customer_id INT(8) UNSIGNED AUTO_INCREMENT,
            username VARCHAR(24) NOT NULL,
            email VARCHAR(254) NOT NULL,
            password_hash BINARY(60) NOT NULL,
            first_name VARCHAR(35),
            last_name VARCHAR(35),
            gender BINARY(1),
            phone VARCHAR(32),
            balance DECIMAL(8,2) DEFAULT 0.0,
            PRIMARY KEY (customer_id),
            UNIQUE (username)
            )
        """,
        """ALTER TABLE customer AUTO_INCREMENT=1000000""",
        """CREATE TABLE IF NOT EXISTS category (
            category_id INT UNSIGNED AUTO_INCREMENT,
            category_name VARCHAR(32),
            priority INT,
            PRIMARY KEY (category_id),
            UNIQUE(category_name)
            )
        """,
        """CREATE TABLE IF NOT EXISTS product (
            product_id INT UNSIGNED AUTO_INCREMENT,
            product_name VARCHAR(64) NOT NULL,
            description VARCHAR(140),
            price DECIMAL(8,2) DEFAULT 0.0,
            rating DECIMAL(2,1),
            thumbnail_uuid CHAR(36),
            picture_uuid CHAR(36),
            priority INT NOT NULL,
            PRIMARY KEY (product_id),
            UNIQUE (product_name)
            )
        """,
        """CREATE TABLE IF NOT EXISTS product_category (
            product_id INT UNSIGNED,
            category_id INT UNSIGNED,
            FOREIGN KEY (product_id) REFERENCES product(product_id),
            FOREIGN KEY (category_id) REFERENCES category(category_id)
            )
        """,
        """CREATE TABLE IF NOT EXISTS `order`(
            order_id INT UNSIGNED AUTO_INCREMENT,
            total DECIMAL(8, 2),
            discount DECIMAL(8, 2),
            actual_paid DECIMAL(8, 2),
            status INT,
            purchased_date TIMESTAMP,
            PRIMARY KEY (order_id)
            )
        """,
        """CREATE TABLE IF NOT EXISTS item (
            item_id INT UNSIGNED AUTO_INCREMENT,
            customer_id INT(8) UNSIGNED,
            product_id INT UNSIGNED,
            order_id INT UNSIGNED,
            amount INT,
            PRIMARY KEY (item_id),
            FOREIGN KEY (customer_id) REFERENCES customer(customer_id),
            FOREIGN KEY (product_id) REFERENCES product(product_id),
            FOREIGN KEY (order_id) REFERENCES `order`(order_id)
        )
        """,
        """CREATE TABLE IF NOT EXISTS coupon (
            coupon_code VARCHAR(32),
            amount DECIMAL(8, 2),
            threshold DECIMAL(3, 2),
            percentage DECIMAL (3, 2),
            PRIMARY KEY (coupon_code)
        )
        """,
        """CREATE TABLE IF NOT EXISTS redeem_card (
            redeem_code CHAR(16),
            amount DECIMAL(8, 2),
            PRIMARY KEY (redeem_code)
        )
        """,
        """CREATE TABLE IF NOT EXISTS comment (
            comment_id INT AUTO_INCREMENT,
            customer_id INT(8) UNSIGNED,
            product_id INT UNSIGNED,
            rating DECIMAL(2,1),
            body VARCHAR(140),
            PRIMARY KEY (comment_id),
            FOREIGN KEY (customer_id) REFERENCES customer(customer_id),
            FOREIGN KEY (product_id) REFERENCES product(product_id)
        )
        """,
    ]

    for sql in sqls:
        cursor.execute(sql)

    print('All tables has been correctly initialized.\n')
    connection.commit()

def init_test_db():
    # Codes for performing unit testing

    # Load configuration
    import utils.config_manager as config_manager

    # Change some configuration of the database temporarily
    config_manager.set_security_temp('DB_NAME', config_manager.get_security('DB_NAME') + '_test')
    config_manager.set_security_temp('UNIT_TESTING_MODE', True)

    connection = pymysql.connect(config_manager.get('DB_URL'),
                                config_manager.get_security('DB_USERNAME'),
                                config_manager.get_security('DB_PASSWORD'))

    connection.cursor().execute('DROP DATABASE IF EXISTS {}'.format(config_manager.get_security('DB_NAME')))
    connection.cursor().execute('CREATE DATABASE IF NOT EXISTS {}'.format(config_manager.get_security('DB_NAME')))
    connection.cursor().execute('USE {}'.format(config_manager.get_security('DB_NAME')))
    init_db_tables(connection)
    connection.close()

if __name__ == '__main__':
    setup()
