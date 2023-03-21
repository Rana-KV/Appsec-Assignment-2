import json, sys, os, datetime, base64, hashlib
from binascii import hexlify
from hashlib import sha256
from django.conf import settings
from os import urandom, system
from cryptography.fernet import Fernet,InvalidToken


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

def get_key():
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    for i in range(int(settings.KEYS_INFO['Current_KEY_ID'])):
        key = hashlib.sha256(key).digest()
    return key

def hash_file(file_cnt):
    assert(file_cnt is not None)
    hasher = sha256()
    hasher.update(file_cnt)
    return hasher.hexdigest()

def get_signature(card_file_data):
    print("signature data:", card_file_data)
    key = get_key()
    key = base64.urlsafe_b64encode(key)
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(card_file_data.encode())
    return encrypted_data

def write_card_data(card_file_path, product, price, customer):
    data_dict = {}
    data_dict['merchant_id'] = product.product_name
    data_dict['customer_id'] = customer.username
    data_dict['total_value'] = price
    data_dict['time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    record = {'record_type':'amount_change', "amount_added":2000,}
    # TODO: replace this with a real signature
    record['signature'] = urandom(16).hex()
    data_dict['records'] = [record,]
    card_data = json.dumps(data_dict)
    with open(card_file_path, 'w') as card_file:
        file_cnt = get_signature(card_data).decode('utf-8')
        card_file.write(file_cnt)
        print(file_cnt)
    print(card_data)
    return card_data

def parse_card_data(card_file_data, card_path_name):
    
    try:
        key = get_key()
        key = base64.urlsafe_b64encode(key)
        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(card_file_data).decode()
        print(decrypted_data)
        return decrypted_data
    except InvalidToken:
        pass
    except TypeError:
        print(TypeError)
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
