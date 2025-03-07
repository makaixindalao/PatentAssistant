from openai import OpenAI
import textwrap

# 从 key.txt 文件中读取 API 密钥
with open("key.txt", "r") as file:
    api_key = file.read().strip()

client = OpenAI(
    api_key=api_key,  # 使用从文件中读取的密钥
    base_url="https://aihubmix.com/v1"  # 替换成 aihubmix 的入口地址
)

def call_chatgpt_api(prompt):
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="DeepSeek-R1",
        )
        # 返回 ChatGPT 的回复内容
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"调用 ChatGPT API 时发生错误: {e}")
        return None


def generate_patent_document(title, ideas):
    system_prompt = textwrap.dedent(rf"""\
    你是一个资深专利工程师，需要根据提供的发明名称和创意要点，撰写专业的专利交底书。文档结构应包含以下七个部分，要求技术细节详尽，逻辑严谨：

    1. 专业领域
    - 明确本发明的技术归属领域
    - 使用《国际专利分类表》分类标准
    
    2. 技术背景与现有技术（需包含流程图）
    - 详细说明技术演进过程（不少于300字）
    - 用Mermaid语法绘制现有技术流程图（示例：
        ```mermaid
        graph TD
            A[图像采集] --> B[预处理]
            B --> C[特征提取]
            C --> D[分类识别]
        ```)
    
    3. 现有技术缺点与发明目的
    - 列出至少3项量化缺点（使用数学公式说明，例如：ΔP = ρgh + ½ρv²）
    - 对应提出本发明要解决的技术问题
    
    4. 本发明技术方案（需包含公式和流程图）
    - 分步骤详细说明技术实现（不少于500字）
    - 核心算法用LaTeX公式表示（例如：f(x) = \\sum_{{i=0}}^n \\alpha_i x^i）
    - 用Mermaid语法绘制技术流程图（至少包含5个处理节点）
    
    5. 关键点与保护范围
    - 提炼3-5个核心技术特征
    - 按重要性排序权利要求项
    
    6. 技术优势对比
    - 制作对比表格（参数指标不少于5项）
    - 用具体数据量化优势（例如：处理速度提升30%）
    
    7. 替代实施方案
    - 提供2种以上替代方案
    - 每种方案需说明实施方式和选择条件

    当前发明名称：{title}
    创意要点：{ideas}
    """)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "请按照专利审查指南要求撰写完整的交底书，特别注意技术方案部分需要包含流程图和数学模型。"}
            ],
            temperature=0.3  # 降低随机性保证技术准确性
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"API调用失败: {e}")
        return None
