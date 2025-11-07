# mac_test_image.py
from openai import OpenAI
client = OpenAI(base_url="http://127.0.0.1:8001/v1", api_key="EMPTY")

resp = client.chat.completions.create(
  model="Qwen/Qwen3-VL-30B-A3B-Instruct",
  messages=[{
    "role":"user",
    "content":[
      {"type":"text","text":"请用两句话描述这张图片。"},
      {"type":"image_url","image_url":{"url":"https://i.imgur.com/5y5Fmlp.jpeg"}}
    ]
  }],
  max_tokens=160, temperature=0.2
)
print(resp.choices[0].message.content)
# mac_test_image.py
from openai import OpenAI
client = OpenAI(base_url="http://127.0.0.1:8001/v1", api_key="EMPTY")

resp = client.chat.completions.create(
  model="Qwen/Qwen3-VL-30B-A3B-Instruct",
  messages=[{
    "role":"user",
    "content":[
      {"type":"text","text":"请用两句话描述这张图片。"},
      {"type":"image_url","image_url":{"url":"https://i.imgur.com/5y5Fmlp.jpeg"}}
    ]
  }],
  max_tokens=160, temperature=0.2
)
print(resp.choices[0].message.content)
