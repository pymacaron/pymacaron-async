# klue-microservice-async
Fork and forget a method call inside a Klue Microservice endpoint, using celery


Synopsis


```python

from klue.swagger.apipool import ApiPool
from klue_async import async

# Make send_email into an asynchronously executable method, that can be called
# via celery in a transparent way
@async
def send_email(title, body):
    # Call 3-rd party emailing API
    pass


def do_signup_user():
    create_user_account()

    # Schedule a task sending this email, and go on, not caring for the result
    send_email.fire('Welcome!', 'You now have an account')

    return ApiPool.myapi.model.Ok()
```


TODO: klue-microservice-async


def fire(*args, **kwargs):
    # TODO: prepend token to *args, or None
    # TODO: do apply_async(*args, **kwargs) on underlying celery task



def async(f):

    @wraps
    def wrapped(*args, **kwargs):
        token = args.pop(0)
        # TODO: if token, add it to app_context, else mock app_context
        return call f(*args, **kwrags)

    # TODO generate celery task around f
    return celery.task(wrapped)


# TODO: klue-microservice

# Patch letsgo to spawn celeryd and rabbitmq if starting on cmd line and
#  klue-config.yaml contains with_tasks = True

# Patch docker base image to have rabbitmq & celrery
# Patch docker image to start rabbitq & celery when asyn_mode


