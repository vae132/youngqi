import os
import json
import hashlib
import re

# 读取数据并排序
def read_and_sort_data(data_folder):
    articles = []
    # 遍历 data 文件夹下所有子文件夹
    for folder_name in os.listdir(data_folder):
        folder_path = os.path.join(data_folder, folder_name)
        if os.path.isdir(folder_path):
            # 针对 fixed 文件夹，读取其中所有 JSON 文件（该文件夹内无子文件夹）
            if folder_name == "fixed":
                for filename in os.listdir(folder_path):
                    if filename.endswith(".json"):
                        with open(os.path.join(folder_path, filename), 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if "page" not in data:
                                data["page"] = 9999
                            articles.append(data)
            else:
                # 其他子文件夹，例如 "page"
                for filename in os.listdir(folder_path):
                    if filename.endswith(".json"):
                        with open(os.path.join(folder_path, filename), 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            articles.append(data)
    articles.sort(key=lambda x: (x.get("page", 9999), x.get("order", 9999)))
    return articles

# 生成评论唯一ID
def generate_unique_id(article_url, index):
    return hashlib.md5(f"{article_url}-{index}".encode("utf-8")).hexdigest()

# 解析评论并返回 HTML（递归处理回复评论）
def parse_comment(comment, article_url, level=0, selected_color="white", index=0):
    author = comment['author']
    time_str = comment['time']
    content = comment['content']
    highlight = comment.get('highlight', False)
    children = comment.get('children', [])

    if highlight:
        highlight_class = "highlight"
        bg_color = "#fff5cc"
    else:
        highlight_class = "reply"
        bg_color = selected_color

    current_index = index
    comment_id = generate_unique_id(article_url, current_index)
    index = current_index + 1

    html = f'<div class="comment {highlight_class}" style="background-color:{bg_color}" id="{comment_id}" onclick="removeHighlight(this)">'
    html += f'<div class="author">{author}</div>'
    html += f'<div class="time">{time_str}</div>'
    html += f'<div class="comment-text">{content}</div>'

    if children:
        replies_html = ""
        for child in children:
            child_html, index = parse_comment(child, article_url, level + 1, selected_color, index)
            replies_html += child_html
        if replies_html:
            html += f'<div class="replies">{replies_html}</div>'
    html += '</div>'
    return html, index

# 生成完整 HTML 页面
def generate_html(articles, result_file="index.html"):
    articles_data = []
    for article in articles:
        article_url = article["article_url"]
        article_title = article["title"]
        # 文章内容：如果没有 content 字段则提示加载失败
        article_content = article.get("content", "文章内容加载失败")
        # 文章发布时间：从数据字段 "article_time" 中提取（如果没有则显示“未知时间”）
        article_time = article.get("article_time", "未知时间")
        comments = article.get("comments", [])
        all_comments_html = []
        index = 0
        for comment in comments:
            comment_html, index = parse_comment(comment, article_url, selected_color="white", index=index)
            all_comments_html.append(comment_html)
        comments_html = "\n".join(all_comments_html)
        # 生成文章部分 HTML，其中包含文章标题、发布时间、正文，
        # 在正文和评论之间添加分界线和“评论内容”标题
        full_html = (
            f"<div class='article-header'>"
            f"<h2>{article_title}</h2>"
            f"<div class='article-time'>发布时间：{article_time}</div>"
            f"<a href='{article_url}' class='origin-link' target='_blank'>🔗 查看文章原文</a>"
            f"</div>"
            f"<div class='article-content'>{article_content}</div>"
            f"<div class='article-divider'><hr><h3>💬 评论内容</h3></div>"
            + comments_html
        )
        articles_data.append({
            "title": article_title,
            "article_time": article_time,
            "article_url": article_url,
            "comments_html": full_html
        })

    # 生成 JSON 字符串后，将所有的 </ 替换为 <\/ 避免嵌入 <script> 标签时被误判结束标签
    articles_json = json.dumps(articles_data, ensure_ascii=False).replace("</", "<\\/")
    articlesPerPage_value = 10

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>阳气诊所</title>
  <!-- 引入 opencc-js 完整版，实现简繁转换 -->
  <script src="https://cdn.jsdelivr.net/npm/opencc-js@1.0.5/dist/umd/full.js"></script>
  <!-- 引入 Google Fonts -->
  <link href="https://fonts.googleapis.com/css?family=Roboto:400,500,700&display=swap" rel="stylesheet">
  <style>
    /* CSS变量定义 */
    :root {{
      --primary-color: #667eea;
      --secondary-color: #764ba2;
      --text-color: #333333;
      --font-size: 16px;
      --line-height: 1.6;
      --font-family: 'Roboto', sans-serif;
      --background-color: #f4f4f9;
      --heading-size: calc(var(--font-size) * 1.375);
      --btn-bg: #667eea;
      --btn-hover: #556cd6;
    }}
    /* 基础重置 */
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}
    html, body {{
      height: 100%;
    }}
    body {{
      font-family: var(--font-family);
      font-size: var(--font-size);
      line-height: var(--line-height);
      color: var(--text-color);
      background-color: var(--background-color);
      padding-top: 70px;
      transition: background-color 0.3s, color 0.3s;
    }}
    /* 头部样式 */
    header {{
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
      color: white;
      padding: 15px 20px;
      z-index: 1000;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    }}
    /* 暗黑模式下头部样式（基于原始颜色暗调10%） */
    body.dark-mode header {{
      background: linear-gradient(135deg, #5C71D3, #6A4492) !important;
      color: #ddd !important;
    }}
    header h1 {{
      font-size: 20px;
    }}
    /* 优化后的按钮样式 */
    .btn {{
      display: inline-block;
      padding: 10px 20px;
      font-size: 16px;
      border: none;
      border-radius: 12px;
      background-color: var(--btn-bg);
      color: #fff;
      cursor: pointer;
      transition: background-color 0.3s, transform 0.2s, box-shadow 0.2s;
      margin: 5px;
      outline: none;
    }}
    .btn:hover {{
      background-color: var(--btn-hover);
      transform: scale(1.05);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }}
    .btn-header {{
      background: transparent;
      border: 2px solid #fff;
      padding: 8px 16px;
      font-size: 16px;
      margin-left: 10px;
    }}
    .btn-header:hover {{
      background-color: rgba(255, 255, 255, 0.2);
    }}
    .btn-success {{ background-color: #43a047; }}
    .btn-success:hover {{ background-color: #388e3c; }}
    .btn-secondary {{ background-color: #ff9900; }}
    .btn-secondary:hover {{ background-color: #e68a00; }}
    .btn-danger {{ background-color: #ff5555; }}
    .btn-danger:hover {{ background-color: #e04e4e; }}

    /* 让下拉框与其他按钮大小一致，并修复PC端展开时“空白”问题 */
    select.btn-header {{
      -webkit-appearance: none;
      -moz-appearance: none;
      appearance: none;
      background-color: var(--btn-bg); /* 按钮背景色 */
      color: #fff;                    /* 按钮文字色 */
      padding: 12px 20px;             /* 增加内边距，调整尺寸 */
      font-size: 18px;                /* 增大字体 */
      border: 2px solid #fff;
      margin-left: 10px;
      border-radius: 12px;
      cursor: pointer;
    }}
    /* 保持下拉框点击时背景色不变 */
    select.btn-header:focus,
    select.btn-header:active {{
      background-color: var(--btn-bg);
      color: #fff;
      outline: none;
    }}
    select.btn-header option {{
      background-color: #fff;
      color: #333;
    }}
    /* 暗黑模式下，选项也要可见 */
    body.dark-mode select.btn-header option {{
      background-color: #444;
      color: #ddd;
    }}

    /* 搜索区域 */
    .search-controls {{
      margin: 20px auto;
      text-align: center;
      max-width: 800px;
      padding: 0 10px;
    }}
    .search-controls select,
    .search-controls input {{
      padding: 10px;
      font-size: 16px;
      margin: 5px 2px;
      border-radius: 5px;
      border: 1px solid #ccc;
      width: calc(50% - 14px);
      transition: border-color 0.3s;
    }}
    .search-controls input:focus,
    .search-controls select:focus {{
      border-color: var(--primary-color);
      outline: none;
    }}
    .search-controls input::placeholder {{ color: #999; }}
    .search-close-btn {{
      background-color: #ff0000;
      color: white;
      border: none;
      padding: 10px 15px;
      font-size: 14px;
      cursor: pointer;
      display: none;
      border-radius: 5px;
    }}
    /* 新增：搜索结果额外控制按钮区域 */
    #searchExtraControls {{
      text-align: center;
      margin: 10px 0;
      display: none;
    }}
    /* 搜索结果计数样式优化 */
    #searchCount {{
      text-align: center;
      font-size: 20px;
      font-weight: bold;
      color: var(--primary-color);
      margin: 20px 0;
    }}
    #searchCount span {{
      color: var(--btn-bg);
    }}
    /* 文章内容 */
    .article-header {{
      text-align: center;
      margin: 20px auto;
      padding: 10px;
      border-bottom: 1px solid #ccc;
      max-width: 800px;
    }}
    .article-header h2 {{ margin-bottom: 10px; font-size: var(--heading-size); }}
    .article-time {{
      font-size: 0.9em;
      color: #888;
      margin-bottom: 8px;
    }}
    .origin-link {{
      text-decoration: none;
      font-size: var(--font-size);
      color: var(--primary-color);
      border: 1px solid var(--primary-color);
      padding: 5px 10px;
      border-radius: 5px;
      transition: background-color 0.3s, color 0.3s;
    }}
    .origin-link:hover {{
      background-color: var(--primary-color);
      color: white;
    }}
    .article-content {{
      max-width: 800px;
      margin: 20px auto;
      padding: 10px;
      font-size: var(--font-size);
      line-height: var(--line-height);
      word-wrap: break-word;
    }}
    .article-content p {{
      margin: 10px 0;
    }}
    /* 新增：使评论区内的段落也换两行 */
    .comment .comment-text p {{
      margin: 10px 0;
    }}
    .article-content a {{
      word-wrap: break-word;
      text-decoration: none;
      color: var(--primary-color);
    }}
    .article-content a:hover {{
      text-decoration: underline;
    }}
    /* 分界线及标题 */
    .article-divider {{
      max-width: 800px;
      margin: 20px auto;
      text-align: center;
    }}
    .article-divider hr {{
      border: none;
      height: 1px;
      background-color: #ccc;
      margin-bottom: 10px;
    }}
    .article-divider h3 {{
      font-size: 20px;
      color: var(--primary-color);
    }}
    /* 评论样式（默认卡片布局） */
    .comment {{
      padding: 15px;
      margin: 15px auto;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      max-width: 800px;
      transition: background-color 0.3s;
      cursor: pointer;
      background-color: #fff;
    }}
    .comment:hover {{
      background-color: #f9f9f9;
    }}
    .comment.highlight {{
      background-color: #fff5cc;
      border-left: 5px solid #ffdb00;
    }}
    .comment.reply {{
      background-color: #ffffff;
      border-left: 5px solid #66ccff;
    }}
    .comment .author {{
      font-weight: bold;
      margin-bottom: 5px;
    }}
    .comment .time {{
      font-size: 0.9em;
      color: #888;
      margin-bottom: 8px;
    }}
    .comment .comment-text {{
      font-size: var(--font-size);
      word-wrap: break-word;
    }}
    .comment .comment-text a {{
      color: var(--text-color) !important;
      text-decoration: none;
    }}
    body.dark-mode .comment .comment-text a {{
      color: white !important;
    }}
    .replies {{
      margin-top: 15px;
      padding-left: 20px;
      border-left: 2px dashed #ccc;
    }}
    /* 关键字高光 */
    .keyword-highlight {{
      background-color: rgba(255, 255, 0, 0.5);
    }}
    .highlighted-comment, .search-highlight {{
      border: 4px solid #ff8888!important;
      background-color: transparent;
    }}
    /* 新增：文章搜索后标题或内容红框高亮（点击后消失） */
    .article-search-highlight {{
       border: 4px solid #ff8888!important;
       background-color: transparent !important;
    }}
    /* 分页样式 */
    .pagination {{
      text-align: center;
      margin: 20px 0;
    }}
    .pagination div {{ margin: 5px 0; }}
    .pagination input[type="number"] {{
      width: 80px;
      height: 40px;
      font-size: 18px;
      text-align: center;
      margin-left: 10px;
      border-radius: 5px;
      border: 1px solid #ccc;
    }}
    .jump-btn, .nav-btn {{
      padding: 10px 20px;
      font-size: 18px;
      background: var(--primary-color);
      color: white;
      border: none;
      border-radius: 25px;
      cursor: pointer;
      margin: 0 5px;
      transition: background-color 0.3s, transform 0.2s;
    }}
    .jump-btn:hover, .nav-btn:hover {{
      background: var(--btn-hover);
      transform: scale(1.03);
    }}
    /* 搜索结果列表 */
    .search-results {{
      list-style-type: none;
      padding: 0;
      margin: 20px auto;
      max-width: 800px;
    }}
    .search-result-item {{
      background-color: white;
      margin: 10px;
      padding: 15px;
      border-radius: 5px;
      box-shadow: 0 2px 6px rgba(0,0,0,0.1);
      transition: background-color 0.3s, transform 0.2s;
      cursor: pointer;
      word-wrap: break-word;
      overflow-wrap: break-word;
      white-space: normal;
    }}
    /* 黑暗模式下搜索结果列表也变为深色 */
    body.dark-mode .search-result-item {{
      background-color: #2b2b2b;
      color: #ccc;
      border: 1px solid #444;
      box-shadow: 0 2px 4px rgba(0,0,0,0.7);
    }}
    /* 新增：特殊高亮（作者为李宗恩或andy） */
    .special-highlight {{
      background-color: #fff5cc;
    }}
    body.dark-mode .special-highlight {{
      background-color: rgba(255,245,204,0.3);
    }}

    /* 文章评论下拉选择框 */
    #articleDropdown {{
      padding: 12px;
      font-size: 16px;
      border: 1px solid #ccc;
      border-radius: 5px;
      width: 80%;
      max-width: 400px;
      margin: 0 auto;
      display: block;
    }}
    /* 暗黑模式下文章下拉框保持与搜索区域一致 */
    body.dark-mode #articleDropdown {{
      background-color: #444;
      color: #ddd;
      border: 1px solid #555;
      -webkit-appearance: none;
      -moz-appearance: none;
      appearance: none;
    }}
    /* 暗黑模式下下拉框中 option 选项样式也保持一致 */
    body.dark-mode #articleDropdown option {{
      background-color: #444;
      color: #ddd;
    }}
    /* 返回顶部按钮 */
    .back-to-top {{
      position: fixed;
      bottom: 20px;
      right: 20px;
      background-color: var(--primary-color);
      color: white;
      padding: 15px;
      font-size: 18px;
      border-radius: 50%;
      border: none;
      cursor: pointer;
      display: none;
      transition: transform 0.3s, opacity 0.3s;
      z-index: 1000;
    }}
    .back-to-top:hover {{
      background-color: var(--btn-hover);
    }}

    /* ---------------- 暗黑模式 ---------------- */
    body.dark-mode {{
      background-color: #222;
      color: #ccc;
    }}
    body.dark-mode a.origin-link {{
      color: #66aaff;
      border-color: #66aaff;
    }}
    body.dark-mode a.origin-link:hover {{
      background-color: #66aaff;
      color: #fff;
    }}
    body.dark-mode .comment {{
      background-color: #2b2b2b !important;
      color: #ccc !important;
      box-shadow: 0 2px 4px rgba(0,0,0,0.7);
      border: 1px solid #444;
    }}
    body.dark-mode .comment.reply {{
      background-color: #2e2e2e !important;
      border-left: 5px solid #5577aa;
    }}
    body.dark-mode .comment.highlight {{
      background-color: #3a2a2a !important;
      border-left: 5px solid #aa7733;
    }}
    body.dark-mode .search-controls select,
    body.dark-mode .search-controls input {{
      background-color: #444;
      color: #ddd;
      border: 1px solid #555;
    }}
    body.dark-mode .search-controls button {{
      background-color: #555;
    }}
    body.dark-mode input::placeholder {{
      color: #ccc;
    }}
    /* 黑暗模式下设置面板样式 */
    body.dark-mode .modal-content {{
      background-color: #333;
      color: #ccc;
      border: 1px solid #555;
    }}
    /* 新增：暗黑模式下点击搜索结果时添加红色边框高亮 */
    body.dark-mode .highlighted-comment,
    body.dark-mode .search-highlight,
    body.dark-mode .article-search-highlight {{
      border: 4px solid #ff8888!important;
    }}

    /* ---------------- Dark mode：按钮颜色稍暗（基于原始颜色暗调10%） ---------------- */
    body.dark-mode .btn,
    body.dark-mode .jump-btn,
    body.dark-mode .nav-btn,
    body.dark-mode .back-to-top {{
      background-color: #5C71D3 !important;
      color: #fff !important;
      border-color: #5C71D3 !important;
    }}
    body.dark-mode .btn:hover,
    body.dark-mode .jump-btn:hover,
    body.dark-mode .nav-btn:hover,
    body.dark-mode .back-to-top:hover {{
      background-color: #4D61C1 !important;
    }}

    body.dark-mode .btn-success {{
      background-color: #3C9040 !important;
    }}
    body.dark-mode .btn-success:hover {{
      background-color: #328036 !important;
    }}
    body.dark-mode .btn-secondary {{
      background-color: #E68A00 !important;
    }}
    body.dark-mode .btn-secondary:hover {{
      background-color: #CF7C00 !important;
    }}
    body.dark-mode .btn-danger {{
      background-color: #E64D4D !important;
    }}
    body.dark-mode .btn-danger:hover {{
      background-color: #CA4646 !important;
    }}

    body.dark-mode .btn-header,
    body.dark-mode select.btn-header {{
      background-color: rgba(255,255,255,0.1) !important;
      color: #fff !important;
      border-color: rgba(255,255,255,0.7) !important;
    }}
    body.dark-mode .btn-header:hover,
    body.dark-mode select.btn-header:hover {{
      background-color: rgba(255,255,255,0.2) !important;
    }}

    /* ==================== 手机端优化 ==================== */
    @media (max-width: 768px) {{
      header h1 {{ font-size: 18px; }}
      .btn-header,
      select.btn-header {{
        font-size: 12px;
        padding: 5px 8px;
      }}
      .search-controls select,
      .search-controls input {{
        width: 100%;
        margin: 5px 0;
      }}
      .search-controls button {{
        width: 100%;
        margin: 5px 0;
      }}
      .jump-btn, .nav-btn {{
        font-size: 16px;
        padding: 8px 16px;
      }}
      .comment .comment-text {{
        font-size: var(--font-size);
      }}
       /* 手机端优化：增大时间排序和作者过滤下拉框大小 */
      #timeSortDropdown, #filterDropdown {{
         font-size: 14px !important;
         padding: 12px 12px !important;
      }}
    }}

    /* 列表布局：卡片布局与列表布局切换 */
    #articleComments.layout-list .comment {{
      box-shadow: none !important;
      border: none !important;
      margin: 10px 0 !important;
      padding: 10px !important;
      border-bottom: 1px solid #ccc;
      border-radius: 0 !important;
    }}
    @media (min-width: 769px) {{
      #articleComments.layout-list {{
          display: flex;
          flex-direction: column;
          align-items: center;
      }}
      #articleComments.layout-list .comment {{
          margin: 10px auto !important;
          max-width: 800px;
      }}
    }}
    #articleComments.layout-list .comment.highlighted-comment,
    #articleComments.layout-list .comment.search-highlight {{
        border: 4px solid #ff8888!important !important;
    }}
    /* 加载动画 */
    .loading-indicator {{
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      font-size: 24px;
      background: rgba(0, 0, 0, 0.7);
      color: #fff;
      padding: 20px 40px;
      border-radius: 8px;
      z-index: 3000;
      display: none;
    }}
    /* 设置面板（Modal）样式 */
    .modal {{
      display: none;
      position: fixed;
      z-index: 2000;
      left: 0;
      top: 0;
      width: 100%;
      height: 100%;
      overflow: auto;
      background-color: rgba(0,0,0,0.4);
    }}
    .modal-content {{
      background-color: #fefefe;
      margin: 10% auto;
      padding: 20px;
      border: 1px solid #888;
      width: 80%;
      max-width: 400px;
      border-radius: 8px;
    }}
    .modal-content input,
    .modal-content select {{
      width: 100%;
      padding: 8px;
      margin: 8px 0;
      box-sizing: border-box;
    }}
    .modal-content button {{
      padding: 10px 15px;
      margin: 10px 5px 0 5px;
      border: none;
      border-radius: 5px;
      cursor: pointer;
    }}
    img, iframe, embed, object, video {{
      max-width: 100%;
      height: auto;
    }}
  </style>
</head>
<body>
  <header>
    <div style="display:flex; align-items:center;">
      <!-- 使用彩色 emoji 表情替换图标 -->
      <h1>阳气诊所</h1>
      <button class="btn btn-header" onclick="toggleDarkMode()">🌙切换暗黑模式</button>
      <button class="btn btn-header" onclick="openSettings()">⚙️设置</button>
      <!-- 语言切换下拉框 -->
      <select id="languageSelect" onchange="changeLanguage()" class="btn btn-header">
        <option value="original">原内容</option>
        <option value="traditional">繁體</option>
        <option value="simplified">简体</option>
      </select>
    </div>
  </header>
  <div class="search-controls">
    <select id="searchType">
      <option value="comment">💬 根据评论搜索</option>
      <option value="author">👤 根据作者搜索</option>
      <option value="article">📄 根据文章内容搜索</option>
      <option value="siteBing">🌐 全站搜索 (必应, 不翻墙)</option>
      <option value="siteGoogle">🌐 全站搜索 (谷歌, 翻墙)</option>
    </select>
    <input type="text" id="searchKeyword" placeholder="请输入搜索内容..." oninput="toggleSearchButton()">
    <button id="searchButton" class="btn" onclick="searchComments()" disabled>
      🔍 搜索
    </button>
    <button class="btn btn-danger search-close-btn" id="searchCloseButton" onclick="closeSearchResults()">
      ❌ 关闭搜索结果
    </button>
  </div>
  <!-- 新增：搜索结果额外控制区域，下拉框形式 -->
  <div id="searchExtraControls"></div>
  <div id="loadingIndicator" class="loading-indicator">加载中... ⏳</div>
  <div id="searchCount"></div>
  <div id="pagination" class="pagination"></div>
  <ul id="searchResults" class="search-results"></ul>
  <hr>
  <h2 style="text-align:center; margin-top:30px;">文章评论分页显示</h2>
  <div style="text-align:center;">
    <select id="articleDropdown" onchange="changeArticle()"></select>
  </div>
  <div id="articlePagination" class="pagination"></div>
  <div id="articleComments" class="layout-card"></div>
  <div id="articleNav" style="text-align: center; margin: 20px 0;">
    <button id="prevArticleBtn" class="nav-btn" onclick="prevArticle()">
      ⬅️ 上一篇
    </button>
    <button id="nextArticleBtn" class="nav-btn" onclick="nextArticle()">
      下一篇 ➡️
    </button>
  </div>
  <button class="back-to-top" onclick="scrollToTop()">↑</button>
  <!-- 设置面板（Modal） -->
  <div id="settingsModal" class="modal">
    <div class="modal-content">
      <h2>🛠️ 页面设置</h2>
      <!-- 文本颜色设置 -->
      <div style="border-bottom: 1px solid #ccc; margin-bottom: 10px; padding-bottom: 10px;">
        <h3>🎨 文本颜色设置</h3>
        <label for="textColorInput">文本颜色:</label>
        <input type="color" id="textColorInput" value="#333333">
      </div>
      <!-- 字体设置 -->
      <div style="border-bottom: 1px solid #ccc; margin-bottom: 10px; padding-bottom: 10px;">
        <h3>🔠 字体设置</h3>
        <label for="fontSizeInput">字体大小 (px): <span id="fontSizeVal">16</span></label>
        <input type="range" id="fontSizeInput" min="12" max="36" value="16" oninput="document.getElementById('fontSizeVal').innerText=this.value">
        <label for="lineHeightInput">行距 (倍数):</label>
        <input type="number" id="lineHeightInput" min="1" max="3" step="0.1" value="1.6">
        <label for="fontFamilySelect">字体样式:</label>
        <select id="fontFamilySelect">
          <option value="Roboto, sans-serif">Roboto</option>
          <option value="Arial, sans-serif">Arial</option>
          <option value="'Times New Roman', serif">Times New Roman</option>
          <option value="Verdana, sans-serif">Verdana</option>
          <option value="'Courier New', monospace">Courier New</option>
          <option value="Georgia, serif">Georgia</option>
          <option value="'Microsoft YaHei', sans-serif">微软雅黑</option>
          <option value="'SimSun', serif">宋体</option>
          <option value="'SimHei', serif">黑体</option>
          <option value="'FangSong', serif">仿宋</option>
          <option value="'KaiTi', serif">楷体</option>
          <option value="'PingFang SC', sans-serif">苹方</option>
        </select>
      </div>
      <!-- 新增：主题选择（新增“无主题”选项） -->
      <div style="border-bottom: 1px solid #ccc; margin-bottom: 10px; padding-bottom: 10px;">
        <h3>🌈 主题选择</h3>
        <label for="themeSelect">选择主题:</label>
        <select id="themeSelect">
          <option value="none" selected>无主题</option>
          <optgroup label="中国风">
            <option value="chinese1">墨韵山水</option>
            <option value="chinese2">书香古韵</option>
            <option value="chinese3">云水谣</option>
          </optgroup>
          <optgroup label="都市风尚">
            <option value="modern1">清风雅韵</option>
            <option value="modern2">现代简约</option>
            <option value="modern3">经典时光</option>
          </optgroup>
          <optgroup label="新主题">
            <option value="romantic">浪漫粉彩</option>
            <option value="techBlue">科技蓝调</option>
            <option value="dreamPurple">梦幻紫</option>
            <option value="minimalBlackWhite">极简黑白</option>
            <option value="vintage">复古风情</option>
            <option value="japaneseFresh">日系清新</option>
          </optgroup>
        </select>
      </div>
      <!-- 布局风格设置 -->
      <div style="border-bottom: 1px solid #ccc; margin-bottom: 10px; padding-bottom: 10px;">
        <h3>🗂️ 布局风格设置</h3>
        <label for="layoutStyleSelect">选择布局风格:</label>
        <select id="layoutStyleSelect">
          <option value="card" selected>卡片布局</option>
          <option value="list">列表布局</option>
        </select>
      </div>
      <div style="text-align: right; margin-top: 10px;">
        <button class="btn" onclick="applySettings()" style="background-color: var(--primary-color); color: white;">应用</button>
        <button class="btn btn-secondary" onclick="restoreDefaults()">还原默认</button>
        <button class="btn btn-danger" onclick="closeSettings()">关闭</button>
      </div>
    </div>
  </div>
  <script>
    /* ---------------- 简繁转换器初始化 ---------------- */
    var converterCn2Tw = OpenCC.Converter({{ from: 'cn', to: 'tw' }});
    var converterTw2Cn = OpenCC.Converter({{ from: 'tw', to: 'cn' }});

    /* ---------------- 全局变量 ---------------- */
    var currentSearchKeyword = "";
    var currentLanguage = "original"; // "original"、"traditional"、"simplified"
    // 修改：全局控制搜索结果的时间排序及作者过滤状态，初始为默认（不排序）和显示全部
    var currentSortOrder = "default"; // "default", "asc" 或 "desc"
    var filterSpecialAuthors = false; // false：全部结果；true：只显示作者为 "李宗恩" 或 "andy"

    /* ---------------- 辅助函数 ---------------- */
    function escapeRegExp(string) {{
      return string.replace(/[.*+?^{{}}()|[\\]\\\\]/g, '\\\\$&');
    }}

    /* ---------------- 全文语言切换相关函数 ---------------- */
    function initOriginalText(root) {{
      if (root.nodeType === Node.TEXT_NODE) {{
        if (root.textContent.trim() !== "") {{
          if (!root._originalText) {{
            root._originalText = root.textContent;
          }}
        }}
      }} else if (root.nodeType === Node.ELEMENT_NODE && !["SCRIPT", "STYLE", "NOSCRIPT", "IFRAME"].includes(root.tagName)) {{
        for (var i = 0; i < root.childNodes.length; i++) {{
          initOriginalText(root.childNodes[i]);
        }}
      }}
    }}

    function applyLanguageToNode(root) {{
      if (root.nodeType === Node.TEXT_NODE) {{
        if (root._originalText === undefined) {{
          root._originalText = root.textContent;
        }}
        if (currentLanguage === "original") {{
          root.textContent = root._originalText;
        }} else if (currentLanguage === "simplified") {{
          root.textContent = converterTw2Cn(root._originalText);
        }} else if (currentLanguage === "traditional") {{
          root.textContent = converterCn2Tw(root._originalText);
        }}
      }} else if (root.nodeType === Node.ELEMENT_NODE && !["SCRIPT", "STYLE", "NOSCRIPT", "IFRAME"].includes(root.tagName)) {{
        for (var i = 0; i < root.childNodes.length; i++) {{
          applyLanguageToNode(root.childNodes[i]);
        }}
      }}
    }}

    function changeLanguage() {{
      currentLanguage = document.getElementById("languageSelect").value;
      applyLanguageToNode(document.body);
    }}

    /* ---------------- 搜索相关功能 ---------------- */
    let allResults = [];
    let currentPage = 1;
    const resultsPerPage = 5;
    function toggleSearchButton() {{
      const keyword = document.getElementById('searchKeyword').value.trim();
      document.getElementById('searchButton').disabled = (keyword === "");
    }}
    function showLoading() {{
      document.getElementById('loadingIndicator').style.display = 'block';
    }}
    function hideLoading() {{
      document.getElementById('loadingIndicator').style.display = 'none';
    }}
    // 搜索函数，支持根据不同类型（文章、评论、作者）搜索，并为每个结果添加统一的 time 属性
    function searchComments() {{
      showLoading();
      currentPage = 1;
      const keyword = document.getElementById('searchKeyword').value.trim();
      currentSearchKeyword = keyword;
      // 每次搜索重置排序和过滤状态
      currentSortOrder = "default";
      filterSpecialAuthors = false;
      var keywordSimplified = converterTw2Cn(keyword);
      var keywordTraditional = converterCn2Tw(keyword);
      var lowerKeywordSimplified = keywordSimplified.toLowerCase();
      var lowerKeywordTraditional = keywordTraditional.toLowerCase();
      const searchType = document.getElementById('searchType').value;
      if(searchType === 'siteBing') {{
          let searchUrl = "https://www.bing.com/search?q=" + encodeURIComponent("site:andylee.pro " + keyword);
          window.open(searchUrl, '_blank');
          hideLoading();
          return;
      }} else if (searchType === 'siteGoogle') {{
          let searchUrl = "https://www.google.com/search?q=" + encodeURIComponent("site:andylee.pro " + keyword);
          window.open(searchUrl, '_blank');
          hideLoading();
          return;
      }}

      allResults = [];
      if(searchType === 'article') {{
         articlesData.forEach(function(article, articleIndex) {{
             const tempDiv = document.createElement('div');
             tempDiv.innerHTML = article.comments_html;
             const articleHeaderElem = tempDiv.querySelector('.article-header');
             const articleContentElem = tempDiv.querySelector('.article-content');
             let textToSearch = "";
             if (articleHeaderElem) {{
                 textToSearch += articleHeaderElem.innerText + " ";
             }}
             if (articleContentElem) {{
                 textToSearch += articleContentElem.innerText;
             }}
             if (textToSearch.toLowerCase().indexOf(lowerKeywordSimplified) !== -1 || textToSearch.toLowerCase().indexOf(lowerKeywordTraditional) !== -1) {{
                 let foundInHeader = false, foundInContent = false;
                 if(articleHeaderElem && (articleHeaderElem.innerText.toLowerCase().includes(lowerKeywordSimplified) || articleHeaderElem.innerText.toLowerCase().includes(lowerKeywordTraditional))) {{
                     foundInHeader = true;
                 }}
                 if(articleContentElem && (articleContentElem.innerText.toLowerCase().includes(lowerKeywordSimplified) || articleContentElem.innerText.toLowerCase().includes(lowerKeywordTraditional))) {{
                     foundInContent = true;
                 }}
                 const previewText = articleContentElem ? articleContentElem.innerText.slice(0,60) + '...' : "";
                 const articleTime = article.article_time || "未知时间";
                 // 修改：结果文本顺序为：文章标题（加粗） - 发布时间 - 文章内容预览
                 allResults.push({{
                    id: "article-" + articleIndex,
                    articleTitle: article.title,
                    articleTime: articleTime,
                    time: articleTime,
                    text: `<strong>${{article.title}}</strong> - ${{articleTime}} - ${{previewText}}`,
                    articleIndex: articleIndex,
                    foundInHeader: foundInHeader,
                    foundInContent: foundInContent,
                    author: ""
                 }});
             }}
         }});
      }} else {{
         articlesData.forEach(function(article, articleIndex) {{
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = article.comments_html;
            const commentElems = tempDiv.querySelectorAll('.comment');
            commentElems.forEach(function(commentElem) {{
              let textToSearch = "";
              if (searchType === 'comment') {{
                const commentTextElem = commentElem.querySelector('.comment-text');
                if (commentTextElem) {{
                  textToSearch = commentTextElem.innerText.toLowerCase();
                }}
              }} else if (searchType === 'author') {{
                const authorElem = commentElem.querySelector('.author');
                if (authorElem) {{
                  textToSearch = authorElem.innerText.toLowerCase();
                }}
              }}
              if (textToSearch.indexOf(lowerKeywordSimplified) !== -1 || textToSearch.indexOf(lowerKeywordTraditional) !== -1) {{
                const commentTextElem = commentElem.querySelector('.comment-text');
                if (commentTextElem) {{
                  var pattern = '(' + escapeRegExp(keywordSimplified) + '|' + escapeRegExp(keywordTraditional) + ')';
                  const reg = new RegExp(pattern, 'gi');
                  commentTextElem.innerHTML = commentTextElem.innerHTML.replace(reg, '<span class="keyword-highlight">$1</span>');
                }}
                const author = commentElem.querySelector('.author') ? commentElem.querySelector('.author').innerText : "";
                const timeElem = commentElem.querySelector('.time');
                const time = timeElem ? timeElem.innerText : "";
                const commentPreview = commentElem.querySelector('.comment-text') ? commentElem.querySelector('.comment-text').innerText.slice(0, 60) + '...' : "";
                const commentId = commentElem.id;
                // 增加 time 属性便于排序
                allResults.push({{
                  id: commentId,
                  articleTitle: article.title,
                  text: author + " - " + time + " : " + commentPreview,
                  articleIndex: articleIndex,
                  author: author,
                  time: time
                }});
              }}
            }});
         }});
      }}
      hideLoading();
      displayPageResults();
      // 如果搜索结果存在，则显示关闭搜索结果按钮和新增的控制下拉框
      if (allResults.length > 0) {{
          document.getElementById('searchCloseButton').style.display = 'inline-block';
          document.getElementById('searchExtraControls').style.display = 'block';
          // 根据搜索类型构建下拉列表：如果是文章搜索，则只显示时间排序下拉框
          let extraHtml = '<select id="timeSortDropdown" class="btn btn-header" onchange="onTimeSortChange()">' +
                          '<option value="default">默认排序</option>' +
                          '<option value="asc">时间排序：升序</option>' +
                          '<option value="desc">时间排序：降序</option>' +
                          '</select>';
          if(searchType === "comment" || searchType === "author") {{
              extraHtml += '<select id="filterDropdown" class="btn btn-header" onchange="onFilterChange()">' +
                           '<option value="all">全部回复</option>' +
                           '<option value="special">仅看李宗恩/andy回复</option>' +
                           '</select>';
          }}
          document.getElementById('searchExtraControls').innerHTML = extraHtml;
      }} else {{
          document.getElementById('searchCloseButton').style.display = 'none';
          document.getElementById('searchExtraControls').style.display = 'none';
          alert("😢 没有找到匹配的" + (searchType === 'article' ? "文章" : "评论") + "！");
      }}
    }}
    // 新增：时间排序下拉框响应函数
    function onTimeSortChange() {{
      currentSortOrder = document.getElementById("timeSortDropdown").value;
      displayPageResults();
    }}
    // 新增：作者过滤下拉框响应函数
    function onFilterChange() {{
      const value = document.getElementById("filterDropdown").value;
      filterSpecialAuthors = (value === "special");
      displayPageResults();
    }}
    // 显示搜索结果（包含分页、排序及过滤）
    function displayPageResults() {{
      let resultsToDisplay = allResults;
      // 应用过滤：仅显示作者为李宗恩或andy的回复（若开启过滤）
      if(filterSpecialAuthors) {{
        resultsToDisplay = resultsToDisplay.filter(function(result) {{
           return result.author && (result.author.toLowerCase() === "andy" || result.author === "李宗恩");
        }});
      }}
      // 只有当时间排序选项不是默认时才进行排序
      function getSortableTime(t) {{
         return (t === "未知时间") ? "9999" : t;
      }}
      if(currentSortOrder !== "default") {{
         resultsToDisplay.sort(function(a, b) {{
            let timeA = getSortableTime(a.time);
            let timeB = getSortableTime(b.time);
            return (currentSortOrder === "asc") ? timeA.localeCompare(timeB) : timeB.localeCompare(timeA);
         }});
      }}
      const totalResults = resultsToDisplay.length;
      const totalPages = Math.ceil(totalResults / resultsPerPage);
      // 如果当前页码超过过滤后总页数，则重置为最后一页（或无结果时设为1）
      if(currentPage > totalPages) {{
         currentPage = totalPages > 0 ? totalPages : 1;
      }}
      document.getElementById('searchCount').innerHTML = "共找到 <span>" + totalResults + "</span> 条记录";
      displayPagination(totalPages);
      const start = (currentPage - 1) * resultsPerPage;
      const end = start + resultsPerPage;
      const paginatedResults = resultsToDisplay.slice(start, end);
      const resultsContainer = document.getElementById('searchResults');
      resultsContainer.innerHTML = "";
      paginatedResults.forEach(function(result) {{
        const li = document.createElement('li');
        li.classList.add('search-result-item');
        if(result.author && (result.author.toLowerCase() === "andy" || result.author.toLowerCase() === "李宗恩")) {{
            li.classList.add('special-highlight');
        }}
        if(result.id.startsWith("article-")) {{
           li.innerHTML = result.text;
        }} else {{
           li.innerHTML = `<strong>${{result.articleTitle}}</strong> - ${{result.text}}`;
        }}
        initOriginalText(li);
        applyLanguageToNode(li);
        li.onclick = function() {{
          let targetArticleIndex = result.articleIndex;
          let targetArticlePage = Math.floor(targetArticleIndex / articlesPerPage) + 1;
          if(currentArticlePage !== targetArticlePage) {{
            currentArticlePage = targetArticlePage;
            populateArticleDropdown();
            displayArticlePagination();
          }}
          document.getElementById('articleDropdown').value = targetArticleIndex;
          changeArticle();
          setTimeout(function() {{
            if(result.id.startsWith("article-")) {{
              const articleElem = document.getElementById('articleComments');
              const articleHeader = articleElem.querySelector('.article-header');
              const articleContent = articleElem.querySelector('.article-content');
              if(articleHeader) {{
                const headerOffset = 70;
                const elementPosition = articleHeader.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
                window.scrollTo({{ top: offsetPosition, behavior: 'smooth' }});
              }}
              if(result.foundInHeader && articleHeader) {{
                 var pattern = '(' + escapeRegExp(converterTw2Cn(currentSearchKeyword)) + '|' + escapeRegExp(converterCn2Tw(currentSearchKeyword)) + ')';
                 const reg = new RegExp(pattern, 'gi');
                 articleHeader.innerHTML = articleHeader.innerHTML.replace(reg, '<span class="keyword-highlight">$1</span>');
                 articleHeader.classList.add('article-search-highlight');
                 articleHeader.onclick = function() {{ removeArticleHighlight(articleHeader); }};
              }}
              if(result.foundInContent && articleContent) {{
                 var pattern = '(' + escapeRegExp(converterTw2Cn(currentSearchKeyword)) + '|' + escapeRegExp(converterCn2Tw(currentSearchKeyword)) + ')';
                 const reg = new RegExp(pattern, 'gi');
                 articleContent.innerHTML = articleContent.innerHTML.replace(reg, '<span class="keyword-highlight">$1</span>');
                 articleContent.classList.add('article-search-highlight');
                 articleContent.onclick = function() {{ removeArticleHighlight(articleContent); }};
              }}
            }} else {{
              const comment = document.getElementById(result.id);
              if(comment) {{
                const headerOffset = 70;
                const elementPosition = comment.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
                window.scrollTo({{ top: offsetPosition, behavior: 'smooth' }});
                highlightComment(comment);
              }}
            }}
          }}, 200);
        }};
        resultsContainer.appendChild(li);
      }});
    }}
    function displayPagination(totalPages) {{
      const paginationContainer = document.getElementById('pagination');
      paginationContainer.innerHTML = "";
      if(totalPages <= 1) return;
      const topLine = document.createElement('div');
      topLine.style.display = 'flex';
      topLine.style.justifyContent = 'center';
      topLine.style.alignItems = 'center';
      topLine.style.fontSize = '16px';
      const pageInfo = document.createElement('span');
      pageInfo.innerText = `当前页 ${{currentPage}} / ${{totalPages}}`;
      topLine.appendChild(pageInfo);
      const pageInput = document.createElement('input');
      pageInput.type = 'number';
      pageInput.id = 'pageInput';
      pageInput.min = 1;
      pageInput.max = totalPages;
      pageInput.value = currentPage;
      topLine.appendChild(pageInput);
      const jumpBtn = document.createElement('button');
      jumpBtn.innerHTML = '📍 跳转';
      jumpBtn.className = 'jump-btn';
      jumpBtn.onclick = function() {{
        let target = parseInt(document.getElementById('pageInput').value);
        if(target < 1) target = 1;
        if(target > totalPages) target = totalPages;
        currentPage = target;
        displayPageResults();
      }};
      topLine.appendChild(jumpBtn);
      paginationContainer.appendChild(topLine);
      const bottomLine = document.createElement('div');
      bottomLine.style.textAlign = 'center';
      bottomLine.style.marginTop = '10px';
      if(currentPage > 1) {{
        const prevBtn = document.createElement('button');
        prevBtn.innerHTML = '⬅️ 上一页';
        prevBtn.className = 'nav-btn';
        prevBtn.onclick = function() {{
          currentPage--;
          displayPageResults();
        }};
        bottomLine.appendChild(prevBtn);
      }}
      if(currentPage < totalPages) {{
        const nextBtn = document.createElement('button');
        nextBtn.innerHTML = '下一页 ➡️';
        nextBtn.className = 'nav-btn';
        nextBtn.onclick = function() {{
          currentPage++;
          displayPageResults();
        }};
        bottomLine.appendChild(nextBtn);
      }}
      paginationContainer.appendChild(bottomLine);
    }}
    function closeSearchResults() {{
      document.getElementById('searchResults').innerHTML = "";
      document.getElementById('pagination').innerHTML = "";
      document.getElementById('searchCount').innerText = "";
      document.getElementById('searchCloseButton').style.display = 'none';
      document.getElementById('searchExtraControls').style.display = 'none';
    }}
    function highlightComment(comment) {{
      comment.classList.add('highlighted-comment');
      if(currentSearchKeyword) {{
        let commentTextElem = comment.querySelector('.comment-text');
        if(commentTextElem) {{
          var keySim = converterTw2Cn(currentSearchKeyword);
          var keyTrad = converterCn2Tw(currentSearchKeyword);
          var pattern = '(' + escapeRegExp(keySim) + '|' + escapeRegExp(keyTrad) + ')';
          const reg = new RegExp(pattern, 'gi');
          commentTextElem.innerHTML = commentTextElem.innerHTML.replace(reg, '<span class="keyword-highlight">$1</span>');
        }}
      }}
    }}
    function removeArticleHighlight(elem) {{
      elem.classList.remove('article-search-highlight');
      const highlights = elem.querySelectorAll('.keyword-highlight');
      highlights.forEach(function(span) {{
         span.outerHTML = span.innerText;
      }});
      elem.onclick = null;
    }}
    function removeHighlight(commentElem) {{
      commentElem.classList.remove('highlighted-comment');
      const highlights = commentElem.querySelectorAll('.keyword-highlight');
      highlights.forEach(function(span) {{
        span.outerHTML = span.innerText;
      }});
    }}
    window.onscroll = function() {{
      if (document.body.scrollTop > 200 || document.documentElement.scrollTop > 200) {{
        document.querySelector('.back-to-top').style.display = 'block';
      }} else {{
        document.querySelector('.back-to-top').style.display = 'none';
      }}
    }}
    function scrollToTop() {{
      window.scrollTo({{top: 0, behavior: 'smooth'}});
    }}
    /* ---------------- 文章选择及分页 ---------------- */
    const articlesData = {articles_json};
    const articlesPerPage = 10;
    let currentArticlePage = 1;
    function initArticlePage() {{
      displayArticlePagination();
      populateArticleDropdown();
      const savedArticleIndex = localStorage.getItem('savedArticleIndex');
      if(savedArticleIndex !== null) {{
        document.getElementById('articleDropdown').value = savedArticleIndex;
      }} else {{
        document.getElementById('articleDropdown').selectedIndex = 0;
      }}
      changeArticle();
    }}
    function populateArticleDropdown() {{
      const dropdown = document.getElementById('articleDropdown');
      dropdown.innerHTML = "";
      const start = (currentArticlePage - 1) * articlesPerPage;
      const end = start + articlesPerPage;
      const articlesPage = articlesData.slice(start, end);
      articlesPage.forEach(function(article, index) {{
        const option = document.createElement('option');
        option.value = start + index;
        option.text = article.title;
        option._originalText = article.title;
        dropdown.appendChild(option);
      }});
      initOriginalText(dropdown);
      applyLanguageToNode(dropdown);
    }}
    function changeArticle() {{
      const dropdown = document.getElementById('articleDropdown');
      const articleIndex = parseInt(dropdown.value);
      const article = articlesData[articleIndex];
      const articleCommentsElem = document.getElementById('articleComments');
      articleCommentsElem.innerHTML = article.comments_html;
      initOriginalText(articleCommentsElem);
      changeLanguage();
      articleCommentsElem.querySelectorAll('.comment.reply').forEach(function(comment) {{
          comment.style.backgroundColor = currentColor;
      }});
    }}
    function displayArticlePagination() {{
      const paginationContainer = document.getElementById('articlePagination');
      paginationContainer.innerHTML = "";
      const totalPages = Math.ceil(articlesData.length / articlesPerPage);
      if(totalPages <= 1) return;
      const topLine = document.createElement('div');
      topLine.style.display = 'flex';
      topLine.style.justifyContent = 'center';
      topLine.style.alignItems = 'center';
      topLine.style.fontSize = '16px';
      const pageInfo = document.createElement('span');
      pageInfo.innerText = `当前页 ${{currentArticlePage}} / ${{totalPages}}`;
      topLine.appendChild(pageInfo);
      const pageInput = document.createElement('input');
      pageInput.type = 'number';
      pageInput.id = 'articlePageInput';
      pageInput.min = 1;
      pageInput.max = totalPages;
      pageInput.value = currentArticlePage;
      topLine.appendChild(pageInput);
      const jumpBtn = document.createElement('button');
      jumpBtn.innerHTML = '📍 跳转';
      jumpBtn.className = 'jump-btn';
      jumpBtn.onclick = function() {{
        let target = parseInt(document.getElementById('articlePageInput').value);
        if(target < 1) target = 1;
        if(target > totalPages) target = totalPages;
        currentArticlePage = target;
        populateArticleDropdown();
        displayArticlePagination();
        document.getElementById('articleDropdown').selectedIndex = 0;
        changeArticle();
      }};
      topLine.appendChild(jumpBtn);
      paginationContainer.appendChild(topLine);
      const bottomLine = document.createElement('div');
      bottomLine.style.textAlign = 'center';
      bottomLine.style.marginTop = '10px';
      if(currentArticlePage > 1) {{
        const prevBtn = document.createElement('button');
        prevBtn.innerHTML = '⬅️ 上一页';
        prevBtn.className = 'nav-btn';
        prevBtn.onclick = function() {{
          currentArticlePage--;
          populateArticleDropdown();
          displayArticlePagination();
          document.getElementById('articleDropdown').selectedIndex = 0;
          changeArticle();
        }};
        bottomLine.appendChild(prevBtn);
      }}
      if(currentArticlePage < totalPages) {{
        const nextBtn = document.createElement('button');
        nextBtn.innerHTML = '下一页 ➡️';
        nextBtn.className = 'nav-btn';
        nextBtn.onclick = function() {{
          currentArticlePage++;
          populateArticleDropdown();
          displayArticlePagination();
          document.getElementById('articleDropdown').selectedIndex = 0;
          changeArticle();
        }};
        bottomLine.appendChild(nextBtn);
      }}
      paginationContainer.appendChild(bottomLine);
    }}
    function goToArticle(index, autoScroll) {{
      var totalArticles = articlesData.length;
      if(index < 0 || index >= totalArticles) return;
      var newPage = Math.floor(index / articlesPerPage) + 1;
      if(newPage !== currentArticlePage) {{
         currentArticlePage = newPage;
         populateArticleDropdown();
         displayArticlePagination();
      }}
      document.getElementById('articleDropdown').value = index;
      changeArticle();
      if(autoScroll) {{
          setTimeout(function(){{
              var articleHeader = document.querySelector('#articleComments .article-header');
              if(articleHeader) {{
                  var headerOffset = 70;
                  var elementPosition = articleHeader.getBoundingClientRect().top;
                  var offsetPosition = elementPosition + window.pageYOffset - headerOffset;
                  window.scrollTo({{ top: offsetPosition, behavior: 'smooth' }});
              }}
          }}, 100);
      }}
    }}
    function prevArticle() {{
      var currentIndex = parseInt(document.getElementById('articleDropdown').value);
      if(currentIndex > 0) {{
           goToArticle(currentIndex - 1, true);
      }} else {{
           alert("🙈 已经是第一篇文章了");
      }}
    }}
    function nextArticle() {{
      var currentIndex = parseInt(document.getElementById('articleDropdown').value);
      if(currentIndex < articlesData.length - 1) {{
           goToArticle(currentIndex + 1, true);
      }} else {{
           alert("🙉 已经是最后一篇文章了");
      }}
    }}
    /* --------------- 设置面板功能 --------------- */
    function openSettings() {{
      document.getElementById('settingsModal').style.display = 'block';
      const settings = localStorage.getItem('userSettings');
      if(settings) {{
        const obj = JSON.parse(settings);
        document.getElementById('fontSizeInput').value = obj.fontSize;
        document.getElementById('fontSizeVal').innerText = obj.fontSize;
        document.getElementById('lineHeightInput').value = obj.lineHeight;
        document.getElementById('fontFamilySelect').value = obj.fontFamily;
        document.getElementById('textColorInput').value = obj.textColor;
        if(obj.theme) {{
          document.getElementById('themeSelect').value = obj.theme;
        }} else {{
          document.getElementById('themeSelect').value = "none";
        }}
        document.getElementById('layoutStyleSelect').value = obj.layoutStyle || "card";
      }}
    }}
    function closeSettings() {{
      document.getElementById('settingsModal').style.display = 'none';
    }}
    function updateLayoutStyle(style) {{
      var articleCommentsElem = document.getElementById('articleComments');
      if (style === 'list') {{
         articleCommentsElem.classList.remove('layout-card');
         articleCommentsElem.classList.add('layout-list');
      }} else {{
         articleCommentsElem.classList.remove('layout-list');
         articleCommentsElem.classList.add('layout-card');
      }}
    }}
    function applySettings() {{
      const fontSize = document.getElementById('fontSizeInput').value;
      const lineHeight = document.getElementById('lineHeightInput').value;
      const fontFamily = document.getElementById('fontFamilySelect').value;
      const textColor = document.getElementById('textColorInput').value;
      document.documentElement.style.setProperty('--font-size', fontSize + 'px');
      document.documentElement.style.setProperty('--line-height', lineHeight);
      document.documentElement.style.setProperty('--font-family', fontFamily);
      document.documentElement.style.setProperty('--text-color', textColor);
      var headingSize = Math.round(parseFloat(fontSize) * 1.375);
      document.documentElement.style.setProperty('--heading-size', headingSize + 'px');

      currentColor = getComputedStyle(document.documentElement).getPropertyValue('--background-color');
      document.querySelectorAll('.comment.reply').forEach(function(comment) {{
        comment.style.backgroundColor = currentColor;
      }});
      const layoutStyle = document.getElementById('layoutStyleSelect').value;
      updateLayoutStyle(layoutStyle);

      const theme = document.getElementById('themeSelect').value;
const themeSettings = {{
    "chinese1": {{
        "--primary-color": "#2c3e50",
        "--secondary-color": "#7f8c8d",
        "--background-color": "#f8f1e5",
        "--btn-bg": "#2c3e50",
        "--btn-hover": "#7f8c8d"
    }},
    "chinese2": {{
        "--primary-color": "#8d6e63",
        "--secondary-color": "#d7ccc8",
        "--background-color": "#fff8e1",
        "--btn-bg": "#8d6e63",
        "--btn-hover": "#d7ccc8"
    }},
    "chinese3": {{
        "--primary-color": "#00897b",
        "--secondary-color": "#80cbc4",
        "--background-color": "#e0f2f1",
        "--btn-bg": "#00897b",
        "--btn-hover": "#80cbc4"
    }},
    "modern1": {{
        "--primary-color": "#4caf50",
        "--secondary-color": "#81c784",
        "--background-color": "#e8f5e9",
        "--btn-bg": "#4caf50",
        "--btn-hover": "#81c784"
    }},
    "modern2": {{
        "--primary-color": "#2196f3",
        "--secondary-color": "#90caf9",
        "--background-color": "#e3f2fd",
        "--btn-bg": "#2196f3",
        "--btn-hover": "#90caf9"
    }},
    "modern3": {{
        "--primary-color": "#3e2723",
        "--secondary-color": "#5d4037",
        "--background-color": "#f3e0dc",
        "--btn-bg": "#3e2723",
        "--btn-hover": "#5d4037"
    }},
    "romantic": {{         // 浪漫粉彩风格
        "--primary-color": "#FF8DA9",
        "--secondary-color": "#FFB3C1",
        "--background-color": "#FFF0F5",
        "--btn-bg": "#FF8DA9",
        "--btn-hover": "#FF6F91"
    }},
    "techBlue": {{         // 科技蓝调风格
        "--primary-color": "#0077CC",
        "--secondary-color": "#005FA3",
        "--background-color": "#E6F7FF",
        "--btn-bg": "#0077CC",
        "--btn-hover": "#006BB3"
    }},
    "dreamPurple": {{      // 梦幻紫风格
        "--primary-color": "#9C27B0",
        "--secondary-color": "#7B1FA2",
        "--background-color": "#F3E5F5",
        "--btn-bg": "#9C27B0",
        "--btn-hover": "#8E24AA"
    }},
    "minimalBlackWhite": {{ // 极简黑白风格
        "--primary-color": "#000000",
        "--secondary-color": "#333333",
        "--background-color": "#FFFFFF",
        "--btn-bg": "#000000",
        "--btn-hover": "#666666"
    }},
    "vintage": {{          // 复古风情
        "--primary-color": "#8B4513",
        "--secondary-color": "#A0522D",
        "--background-color": "#F5F5DC",
        "--btn-bg": "#8B4513",
        "--btn-hover": "#7B3E0A"
    }},
    "japaneseFresh": {{    // 日系清新风格
        "--primary-color": "#8FBC8F",
        "--secondary-color": "#708090",
        "--background-color": "#FAFAD2",
        "--btn-bg": "#8FBC8F",
        "--btn-hover": "#7AA07A"
    }}
}};
      if(theme !== "none" && themeSettings[theme]) {{
          const t = themeSettings[theme];
          for (const key in t) {{
              document.documentElement.style.setProperty(key, t[key]);
          }}
          if(t["--background-color"]) {{
             currentColor = t["--background-color"];
          }}
          document.querySelectorAll('.comment.reply').forEach(function(comment) {{
              comment.style.backgroundColor = currentColor;
          }});
      }} else {{
          /* 选择无主题时，立即恢复默认样式 */
          document.documentElement.style.setProperty('--primary-color', '#667eea');
          document.documentElement.style.setProperty('--secondary-color', '#764ba2');
          document.documentElement.style.setProperty('--background-color', '#f4f4f9');
          document.documentElement.style.setProperty('--btn-bg', '#667eea');
          document.documentElement.style.setProperty('--btn-hover', '#556cd6');
          currentColor = getComputedStyle(document.documentElement).getPropertyValue('--background-color');
          document.querySelectorAll('.comment.reply').forEach(function(comment) {{
              comment.style.backgroundColor = currentColor;
          }});
      }}
      const settings = {{
        fontSize: fontSize,
        lineHeight: lineHeight,
        fontFamily: fontFamily,
        textColor: textColor,
        layoutStyle: layoutStyle,
        theme: theme
      }};
      localStorage.setItem('userSettings', JSON.stringify(settings));
      closeSettings();
    }}
    function restoreDefaults() {{
      document.getElementById('fontSizeInput').value = 16;
      document.getElementById('fontSizeVal').innerText = 16;
      document.getElementById('lineHeightInput').value = 1.6;
      document.getElementById('fontFamilySelect').value = "Roboto, sans-serif";
      document.getElementById('textColorInput').value = "#333333";
      document.getElementById('layoutStyleSelect').value = "card";
      document.getElementById('themeSelect').value = "none";
      applySettings();
    }}
    window.addEventListener("beforeunload", function() {{
      const articleDropdown = document.getElementById('articleDropdown');
      if(articleDropdown) {{
        localStorage.setItem('savedArticleIndex', articleDropdown.value);
      }}
      localStorage.setItem('savedArticlePage', currentArticlePage);
    }});
    window.onload = function() {{
      initOriginalText(document.body);
      const settings = localStorage.getItem('userSettings');
      if(settings) {{
        const obj = JSON.parse(settings);
        document.getElementById('fontSizeInput').value = obj.fontSize;
        document.getElementById('fontSizeVal').innerText = obj.fontSize;
        document.getElementById('lineHeightInput').value = obj.lineHeight;
        document.getElementById('fontFamilySelect').value = obj.fontFamily;
        document.getElementById('textColorInput').value = obj.textColor;
        document.getElementById('themeSelect').value = obj.theme || "none";
        document.getElementById('layoutStyleSelect').value = obj.layoutStyle || "card";
        // 使上次设置立即生效
        applySettings();
      }}
      const savedArticlePage = localStorage.getItem('savedArticlePage');
      if(savedArticlePage !== null) {{
         currentArticlePage = parseInt(savedArticlePage);
      }}
      initArticlePage();
      document.querySelectorAll('.comment .comment-text a').forEach(function(a) {{
        a.target = '_blank';
      }});
      applyLanguageToNode(document.body);
    }}
    let currentColor = "white";
    function toggleDarkMode() {{
      document.body.classList.toggle('dark-mode');
    }}
  </script>
</body>
</html>
"""

    with open(result_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"已生成文件：{result_file}")

def main():
    data_folder = "data"  # 数据目录中应包含 "page" 和 "fixed" 文件夹
    articles = read_and_sort_data(data_folder)
    generate_html(articles)

if __name__ == "__main__":
    main()
