```

pip install uv
uv venv --seed --python 3.12
source .venv/bin/activate

uv pip install -e .

uvicorn drippy.api:app --reload
visit localhost:8000/docs
```


