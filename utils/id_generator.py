import random
import string

def generate_random_id():
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    numbers = ''.join(random.choices(string.digits, k=2))
    combined = list(letters + numbers)
    random.shuffle(combined)
    return ''.join(combined)