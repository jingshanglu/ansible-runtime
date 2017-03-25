from runtime.setting import appsetting
BROKER_URL = 'redis://'+appsetting['broker_redis_path']+':'+appsetting['broker_redis_port']+'/'+appsetting['broker_redis_db']
CELERY_RESULT_BACKEND ='redis://'+appsetting['result_redis_path']+':'+appsetting['result_redis_port']+'/'+appsetting['result_redis_db']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT=['json']
CELERY_TIMEZONE = 'Europe/Oslo'
CELERY_ENABLE_UTC = True
