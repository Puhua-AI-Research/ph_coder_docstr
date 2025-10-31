## 思路
- 原则上尽可能不随意打散语义
- 区分不同类型的代码，.py,cpp,c,cu,cuh,jsx,tsx,tx,js,.go
- 遍历项目的所有的代码文件
- 单文件内容拆分
  - 按换行符拆分（这种不排除会把一个函数的内容会被打散）
  - 按函数增则拆分
  - 如果函数序列太长，则再按换行拆分
- 将拆分单元分别拿去大模型解释，得到注释，然后在拆分单元前加上这个注释
  - [def a():...., def b()...]
  - [# 解释\ndef a():...., # 解释\ndef a()def b()...]
  - 再将上述拼接序列合并成完整的序列
- 最后将整个文件的代码交给大模型对功能进行阐述，最后放文件开头
- 每个文件注释完，都会标记完成，避免重试时浪费资源, 最后输出一个json文件
- 大模型使用 openai的sdk，方法如下
```python
from openai import OpenAI
client = OpenAI(api_key="your_api_key")
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"}
    ]
)
print(response.choices[0].message.content)
```
- 由于 请求快了，可能大模型会返回错误，需要重试，重试3次后，如果还失败，则记录错误信息，并跳过该文件
- 当然可以模型用多个模型列表来轮训，这样避免频繁使用同一个模型
- 大模型的地址url，key，models_list 使用环境变量来配置即可
## 总结
- 由于需要得到 全部代码的 20% 以上注释
  - <= 50行代码的，得到一个注释
  - 每个文件的开头都有整个文件的功能上的注释
- 命令行：
```bash
pip install ph_coder_docstr.whl
export OPENAI_API_KEY=your_api_key
export OPENAI_URL=https://api.openai.com/v1
export OPENAI_MODELS_LIST=gpt-4o-mini,gpt-4o
python3 -m ph_coder_docstr --project ./A/
```