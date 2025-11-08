# Drippy

Gone are the days where Clippy was your personal assistant. 

Agentic AI is the new kid on the block. 

But while agentic workflows forge straight ahead, into mistakes, prompt injections, and other pitfalls, Drippy gives the user a slow drip of instructions. 

Think of the tutorial for a website, but for any task. Built for the non-technical person in your life. 

Your grandma needs help opening her email? Your parents need help downloading a Youtube video? Drippy is here to help.



```

pip install uv
uv venv --seed --python 3.12
source .venv/bin/activate

uv pip install -e .

uvicorn drippy.api:app --reload --port 8501
visit localhost:8501/docs

frontend go to "my-electron-app"
npm i
npm start
```

python -m src.drippy.overlay 100 100 200 150

