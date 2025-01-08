from .models import Item

def get_items():
    # This is a sample function; in a real app, you would query your database here.
    return [
        {'name': 'Item 1', 'description': 'A sample item', 'price': 10.0, 'tax': 1.5}
    ]
