import utils.validation as validator
from models.DAO import DAO
from utils.exception import ValidationError
from models.shared import find_user, find_product, get_archive_index

def create_purchased_item(order_id, product_name, product_price, amount, cursor):
    """The function creates a purchased item if the purchased item does not exist.
    Otherwise, the purchased item will be updated in an "append" manner

    NOTE: A cursor must be provided
    
    Parameters:
    product_name -- the name of the product at the current moment
    product_price -- the price of the product at the current moment
    amount -- the amount of the product
    """
    # Clean the input data
    product_name = str(product_name).strip()
    product_price = str(product_price).strip()
    amount = str(amount).strip()
    order_id = str(order_id).strip()

    # Check is the input valid
    if not product_name:
        raise ValidationError('Product name must not be empty.')
    if not product_price:
        raise ValidationError('Product price must not be empty.')
    if not amount.isdecimal():
        raise ValidationError('Invalid amount.')

    # Insert into purchased_item
    sql = """INSERT INTO purchased_item (
        product_name_snapshot,
        product_price_snapshot,
        amount
    ) VALUES (
        %(product_name_snapshot)s,
        %(product_price_snapshot)s,
        %(amount)s
    )"""
    cursor.execute(sql, {'product_name_snapshot': get_archive_index(product_name),
                        'product_price_snapshot': product_price,
                        'amount': amount})

    cursor.execute('SELECT LAST_INSERT_ID()')
    purchased_item_id = cursor.fetchone()['LAST_INSERT_ID()']

    # Insert into order_purchased_item
    sql = """INSERT INTO order_purchased_item (
        order_id,
        purchased_item_id
    ) VALUES (
        %(order_id)s,
        %(purchased_item_id)s
    )"""
    cursor.execute(sql, {'order_id': order_id,
                        'purchased_item_id': purchased_item_id})
    
    # PLEASE NOTE, THE FUNCTION WON"T COMMIT
    # IT IS UP TO THE PARENT FUNCTION (WHO PASSED IN THE DAO) TO DECIDE
    # WHETHER TO COMMIT OR NOT.
