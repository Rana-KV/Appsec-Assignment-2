import json
from binascii import hexlify
from hashlib import sha256
from django.conf import settings
from os import urandom, system
from cryptography.fernet import Fernet
import sys, os

SEED = settings.RANDOM_SEED

LEGACY_ROOT = os.path.dirname(os.path.abspath(__file__))

if sys.platform == 'win32':
    CARD_PARSER = os.path.join(LEGACY_ROOT, '..', 'bins', 'giftcardreader_win.exe')
elif sys.platform == 'linux':
    CARD_PARSER = os.path.join(LEGACY_ROOT, '..', 'bins', 'giftcardreader_linux')
elif sys.platform == 'darwin':
    CARD_PARSER = os.path.join(LEGACY_ROOT, '..', 'bins', 'giftcardreader_mac')
else:
    raise Exception("Unsupported platform: {}".format(sys.platform))

# KG: Something seems fishy here. Why are we seeding here?
def generate_salt(length, debug=True):
    import random
    random.seed(SEED)
    return hexlify(random.randint(0, 2**length-1).to_bytes(length, byteorder='big'))

def hash_pword(salt, pword):
    assert(salt is not None and pword is not None)
    hasher = sha256()
    hasher.update(salt)
    hasher.update(pword.encode('utf-8'))
    return hasher.hexdigest()

def parse_salt_and_password(user):
    return user.password.split('$')

def check_password(user, password): 
    salt, password_record = parse_salt_and_password(user)
    verify = hash_pword(salt.encode('utf-8'), password)
    if verify == password_record:
        return True
    return False

def get_signature(card_file_data):
    print("signature data:", card_file_data)
    key = settings.SECRET_KEY.encode()
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(card_file_data.encode())
    return encrypted_data

def write_card_data(card_file_path, product, price, customer):
    data_dict = {}
    data_dict['merchant_id'] = product.product_name
    data_dict['customer_id'] = customer.username
    data_dict['total_value'] = price
    cur_time = datetime.now()
    data_dict['time'] = cur_time.strftime("%Y-%m-%d %H:%M:%S")
    record = {'record_type':'amount_change', "amount_added":2000,}
    # TODO: replace this with a real signature
    record['signature'] = urandom(16).hex()
    data_dict['records'] = [record,]
    with open(card_file_path, 'w') as card_file:
        card_file.write(get_signature(json.dumps(data_dict)).decode('utf-8'))

def parse_card_data(card_file_data, card_path_name):
    
    try:
        key = settings.SECRET_KEY.encode()
        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(card_file_data).decode()
        test_json = json.loads(decrypted_data)
        return decrypted_data.encode()
    except (json.JSONDecodeError, UnicodeDecodeError, InvalidToken):
        pass
    ret_val = system(f" > binary;")
    with open('binary', 'wb') as card_file:
        card_file.write(card_file_data)
    # KG: Are you sure you want the user to control that input?
    print(f"running: {CARD_PARSER} 2 binary > binary;")
    ret_val = system(f"{CARD_PARSER} 2 binary > binary;")
    if ret_val != 0:
        return card_file_data
    with open("binary", 'rb') as tmp_file:
        return tmp_file.read()
