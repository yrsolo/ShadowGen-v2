import os


os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("STATE_BACKEND", "memory")
os.environ.setdefault("QUEUE_BACKEND", "memory")
os.environ.setdefault("STATE_DIR", ".shadowgen-test")
