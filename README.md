# klue-microservice-async

An extension of klue-microservice seamlessly adding asynchronous task execution
based on celery/Redis.

[klue-microservice](https://github.com/erwan-lemonnier/klue-microservice) is a
Python framework for easily defining, implementing and deploying REST apis onto
amazon Elastic Beanstalk.

## Description

It is considered good behavior for a REST api endpoint to return as quickly as
possible. Any long running task it needs to perform, such as image
manipulation, 3rd party calls whose replies are not immediately needed, logging
or analytics, should be executed after returning the HTTP response to the api
caller.

Unfortunately, this is not trivially done. Except with klue-microservice-async :-)

[klue-microservice-async](https://github.com/erwan-lemonnier/klue-microservice-async)
adds asynchronous execution capability to
[klue-microservice](https://github.com/erwan-lemonnier/klue-microservice)
servers, by spawning in the background a celery worker in which all your api
modules are loaded. The celery worker loads your swagger api files in just the
same way as the [klue-microservice
API](https://github.com/erwan-lemonnier/klue-microservice/blob/master/klue_microservice/__init__.py)
object does, imports all the modules containing your endpoint implementations
and emulates a Flask context including the current user's authentication
details. That way, code executed asynchronously in a klue/celery task sees
exactly the same context as code executing synchronously in the endpoint
method.

## Setup

Install redis in your dev environment:

```shell
apt-get install redis-server
pip install redis
```

Add klue-microservice-async to your klue-microservice project:

```shell
pip install klue-microservice-async
```

Edit 'klue-config.yaml' to contain:

```yaml
with_async: true
```

## Synopsis

And decorate the methods you want to call asynchronously with '@asynctask':

```python
from klue_async import asynctask
from klue.swagger.apipool import ApiPool

# Make send_email into an asynchronously executable method, that can be called
# via celery in a transparent way
@asynctask
def send_email(title, body):
    pass


def do_signup_user():
    do_stuff()

    # Queue up a celery task to execute send_email() with the corresponding
    # arguments. Execution will happen inside the celery worker's process, in a
    # Klue setup and Flask context identical to the one of 'do_signup_user()'
    send_email('Welcome!', 'You now have an account')

    # Return at once, without waiting for 'send_email()' to complete (or even start)
    return ApiPool.myapi.model.Ok()
```

The klue-microservice framework takes care of all the plumbing, so when you do

```
python server.py --port 8080
```

and 'klue-config.yaml' contains 'with_async: true', server.py will auto-magically
spawn a Celery worker.

When deploying the service with 'deploy_pipeline', Celery will be added to the
server image, and started together with the server when running that image in a
container.