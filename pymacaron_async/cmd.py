def get_celery_cmd(debug=False, keep_alive=False, concurrency=None):
    level = 'debug' if debug else 'info'

    cmd = 'pymasync --level %s' % level

    if keep_alive:
        cmd += ' --keep-alive'

    if concurrency:
        cmd += ' --concurrency %s' % concurrency

    return cmd
