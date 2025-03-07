from openai import OpenAI
import textwrap
import json
from pathlib import Path

class ConfigLoader:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.load_config()
        return cls._instance
    
    def load_config(self, config_path='config.json'):
        """加载配置文件并验证参数"""
        default_config = {
            "openai_config": {
                "api_key": "",
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-3.5-turbo"
            },
            "generation_params": {
                "temperature": 0.5,
                "max_tokens": 1000
            }
        }
        
        try:
            if not Path(config_path).exists():
                raise FileNotFoundError(f"配置文件 {config_path} 不存在")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            
            # 深度合并配置
            self.config = self._deep_merge(default_config, user_config)
            
            # 验证必要参数
            if not self.config['openai_config']['api_key']:
                raise ValueError("API密钥不能为空")
            
        except json.JSONDecodeError:
            raise ValueError("配置文件格式错误，必须是有效的JSON格式")
        except Exception as e:
            raise RuntimeError(f"配置加载失败: {str(e)}")
    
    def _deep_merge(self, base, update):
        """深度合并字典"""
        for key, value in update.items():
            if isinstance(value, dict) and key in base:
                base[key] = self._deep_merge(base.get(key, {}), value)
            else:
                base[key] = value
        return base

def get_openai_client():
    """根据配置创建OpenAI客户端"""
    config = ConfigLoader().config['openai_config']
    return OpenAI(
        api_key=config['api_key'],
        base_url=config['base_url']
    )

def generate_patent_document(title, ideas):
    system_prompt = textwrap.dedent(rf"""\
    你是一个资深专利工程师，需要根据提供的发明名称和创意要点，撰写专业的专利交底书。文档结构应包含以下七个部分，要求技术细节详尽，逻辑严谨：

    1. 专业领域
    - 明确本发明的技术归属领域
    
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
    
    4. 本发明技术详细方案（需包含公式和流程图）
    - 分步骤详细说明技术实现（技术方案不少于1000字），每个细节都需要详细展开说明
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

    config = ConfigLoader().config
    client = get_openai_client()
    
    try:
        response = client.chat.completions.create(
            model=config['openai_config']['model'],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "请按照专利审查指南要求撰写完整的交底书，特别注意技术方案部分需要包含流程图和数学模型。"}
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"API调用失败: {e}")
        return None
