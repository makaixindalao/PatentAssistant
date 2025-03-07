import ai
import logging


# 设置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', mode='a'),
        logging.StreamHandler()
    ]
)

def main():
    logging.info("开始执行专利生成程序...")
    try:
        # 用户交互输入
        invention_title = input("请输入发明名称（建议包含技术特征和应用领域）：\n➤ ")
        while not invention_title.strip():
            invention_title = input("发明名称不能为空，请重新输入：\n➤ ")
            
        invention_ideas = input("\n请输入技术方案要点（建议包含技术手段和技术效果）：\n➤ ")
        while not invention_ideas.strip():
            invention_ideas = input("技术要点不能为空，请重新输入：\n➤ ")

        # 显示确认信息
        logging.info("\n▌ 正在生成的专利文档：")
        logging.info(f"├─ 发明名称：{invention_title}")
        logging.info(f"└─ 技术要点：{invention_ideas[:50]}...")  # 显示前50字符
        
        # 调用生成函数
        patent_doc = ai.generate_patent_document(invention_title, invention_ideas)
        
        if patent_doc:
            filename = f"{invention_title[:10]}专利文档.md".replace(" ", "_")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(patent_doc)
            logging.info(f"专利文档已保存为 {filename}")
            logging.info(f"\n✅ 文档生成成功！文件保存位置：{filename}")
        
    except KeyboardInterrupt:
        print("\n操作已取消")
    except Exception as e:
        logging.error(f"程序运行异常: {str(e)}")
        print(f"\n❌ 发生错误：{str(e)}")

if __name__ == "__main__":
    main()
