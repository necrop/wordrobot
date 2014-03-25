
import random
import string

from ..models import UserSubmission

charset = string.ascii_lowercase + string.digits


def store_user_submission(post):
    record = UserSubmission(identifier=random_identifier(6),
                            author=post['author'],
                            title=post['title'],
                            year=post['year'],
                            text=post['text'])
    record.save()
    return record


def random_identifier(length):
    """
    Return a string of random characters, of a given length.
    """
    while 1:
        # Compile the random string
        identifier = ''.join(random.choice(charset) for i in range(length))
        # Check that this does not already exist; we'll loop if it does
        try:
            UserSubmission.objects.get(identifier=identifier)
        except UserSubmission.DoesNotExist:
            break
    return identifier
