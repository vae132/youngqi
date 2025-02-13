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
            # 針對 fixed 文件夾，讀取其中所有 JSON 文件（該文件夾內無子文件夾）
            if folder_name == "fixed":
                for filename in os.listdir(folder_path):
                    if filename.endswith(".json"):
                        with open(os.path.join(folder_path, filename), 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if "page" not in data:
                                data["page"] = 9999
                            articles.append(data)
            else:
                # 其他子文件夾，例如 "page"
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
def generate_html(articles, result_file="原版.html"):
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
            f"<a href='{article_url}' class='origin-link' target='_blank'>查看文章原文</a>"
            f"</div>"
            f"<div class='article-content'>{article_content}</div>"
            f"<div class='article-divider'><hr><h3>评论内容</h3></div>"
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
      padding: 8px 16px;
      font-size: 16px;
      border: 2px solid #fff;
      margin-left: 10px;
      border-radius: 12px;
      cursor: pointer;
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
      transition: background-color 0.3s, transform 0.2s;
      cursor: pointer;
      background-color: #fff;
    }}
    .comment:hover {{
      background-color: #f9f9f9;
      transform: translateY(-2px);
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
      border: 4px solid #ff8888;
      background-color: transparent;
    }}
    /* 新增：文章搜索后标题或内容红框高亮（点击后消失） */
    .article-search-highlight {{
      border: 4px solid red;
      background-color: transparent;
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
      /* 防止长英文或网址超出边界 */
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
    /* 暗黑模式 */
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

    /* ==================== 手机端优化 ==================== */
    @media (max-width: 768px) {{
      header h1 {{ font-size: 18px; }}
      /* 让下拉框在手机端和其他按钮一样大小 */
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
    /* 以下规则仅在电脑端生效，使列表布局居中 */
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
    /* 新增：列表布局下高亮效果使用红色边框 */
    #articleComments.layout-list .comment.highlighted-comment,
    #articleComments.layout-list .comment.search-highlight {{
        border: 4px solid #ff8888 !important;
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
    /* 新增：确保图片、iframe、embed、object、video 等媒体资源在手机上不会超出容器宽度 */
    img, iframe, embed, object, video {{
      max-width: 100%;
      height: auto;
    }}
  </style>
</head>
<body>
  <header>
    <div style="display:flex; align-items:center;">
      <h1>阳气诊所</h1>
      <button class="btn btn-header" onclick="toggleDarkMode()">切换暗黑模式</button>
      <button class="btn btn-header" onclick="openSettings()">设置</button>
      <!-- 语言切换下拉框，也使用 btn btn-header，让它和其他按钮在手机端同尺寸 -->
      <select id="languageSelect" onchange="changeLanguage()" class="btn btn-header">
        <option value="original">原内容</option>
        <option value="traditional">繁體</option>
        <option value="simplified">简体</option>
      </select>
    </div>
  </header>
  <div class="search-controls">
    <select id="searchType">
      <option value="comment">根据评论搜索</option>
      <option value="author">根据作者搜索</option>
      <option value="article">根据文章内容搜索</option>
      <option value="siteBing">全站搜索 (必应, 不翻墙)</option>
      <option value="siteGoogle">全站搜索 (谷歌, 翻墙)</option>
    </select>
    <input type="text" id="searchKeyword" placeholder="请输入搜索内容..." oninput="toggleSearchButton()">
    <button id="searchButton" class="btn" onclick="searchComments()" disabled>搜索</button>
    <button class="btn btn-danger search-close-btn" id="searchCloseButton" onclick="closeSearchResults()">关闭搜索结果</button>
  </div>
  <div id="loadingIndicator" class="loading-indicator">Loading...</div>
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
    <button id="prevArticleBtn" class="nav-btn" onclick="prevArticle()">上一篇</button>
    <button id="nextArticleBtn" class="nav-btn" onclick="nextArticle()">下一篇</button>
  </div>
  <button class="back-to-top" onclick="scrollToTop()">↑</button>
  <!-- 设置面板（Modal） -->
  <div id="settingsModal" class="modal">
    <div class="modal-content">
      <h2>页面设置</h2>
      <!-- 文本颜色设置 -->
      <div style="border-bottom: 1px solid #ccc; margin-bottom: 10px; padding-bottom: 10px;">
        <h3>文本颜色设置</h3>
        <label for="textColorInput">文本颜色:</label>
        <input type="color" id="textColorInput" value="#333333">
      </div>
      <!-- 字体设置 -->
      <div style="border-bottom: 1px solid #ccc; margin-bottom: 10px; padding-bottom: 10px;">
        <h3>字体设置</h3>
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
          <!-- 新增中文常用字体 -->
          <option value="'Microsoft YaHei', sans-serif">微软雅黑</option>
          <option value="'SimSun', serif">宋体</option>
          <option value="'SimHei', serif">黑体</option>
          <option value="'FangSong', serif">仿宋</option>
          <option value="'KaiTi', serif">楷体</option>
          <option value="'PingFang SC', sans-serif">苹方</option>
        </select>
      </div>
      <!-- 背景颜色设置 -->
      <div style="border-bottom: 1px solid #ccc; margin-bottom: 10px; padding-bottom: 10px;">
        <h3>背景颜色设置</h3>
        <label for="bgColorSelect">选择背景色:</label>
        <select id="bgColorSelect" onchange="onBgColorSelectChange()">
          <!-- 修改预设颜色为更适合阅读的颜色 -->
          <option value="aliceblue">清晨湛蓝</option>
          <option value="honeydew">蜜意清绿</option>
          <option value="mistyrose">轻纱玫瑰</option>
          <option value="ivory">象牙白</option>
          <option value="lavender">薰衣草紫</option>
          <option value="white" selected>素雪</option>
          <option value="custom">自定义</option>
        </select>
        <div id="customBgColorContainer" style="display: none; margin-top: 10px;">
          <label for="customBgColorInput">自定义颜色:</label>
          <input type="color" id="customBgColorInput" value="#ffffff">
        </div>
      </div>
      <!-- 新增：布局风格设置 -->
      <div style="border-bottom: 1px solid #ccc; margin-bottom: 10px; padding-bottom: 10px;">
        <h3>布局风格设置</h3>
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

    /* ---------------- 辅助函数 ---------------- */
    function escapeRegExp(string) {{
      return string.replace(/[.*+?^{{}}()|[\\]\\\\]/g, '\\\\$&');
    }}

    /* ---------------- 全文语言切换相关函数 ---------------- */
    // 遍历 DOM，记录所有文本节点的原始内容（排除 SCRIPT/STYLE/等）
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

    // 根据 currentLanguage 更新文本节点内容
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

    // 切换语言
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
    function searchComments() {{
      showLoading();
      currentPage = 1;
      const keyword = document.getElementById('searchKeyword').value.trim();
      currentSearchKeyword = keyword;
      // 生成简体和繁体两种关键词
      var keywordSimplified = converterTw2Cn(keyword);
      var keywordTraditional = converterCn2Tw(keyword);
      var lowerKeywordSimplified = keywordSimplified.toLowerCase();
      var lowerKeywordTraditional = keywordTraditional.toLowerCase();
      const searchType = document.getElementById('searchType').value;
      // 针对必应、谷歌全站搜索，直接打开新页面
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

      // 针对文章内容搜索
      if(searchType === 'article') {{
         allResults = [];
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
                 allResults.push({{
                    id: "article-" + articleIndex,
                    articleTitle: article.title,
                    articleTime: articleTime,
                    text: articleTime + " - " + article.title + " - " + previewText,
                    articleIndex: articleIndex,
                    foundInHeader: foundInHeader,
                    foundInContent: foundInContent,
                    author: ""
                 }});
             }}
         }});
         hideLoading();
         displayPageResults();
         if (allResults.length > 0) {{
             document.getElementById('searchCloseButton').style.display = 'inline-block';
         }} else {{
             document.getElementById('searchCloseButton').style.display = 'none';
             alert("没有找到匹配的文章！");
         }}
         return;
      }}

      // 针对评论或作者搜索
      allResults = [];
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
            allResults.push({{
              id: commentId,
              articleTitle: article.title,
              text: author + " - " + time + " : " + commentPreview,
              articleIndex: articleIndex,
              author: author
            }});
          }}
        }});
      }});
      hideLoading();
      displayPageResults();
      if (allResults.length > 0) {{
        document.getElementById('searchCloseButton').style.display = 'inline-block';
      }} else {{
        document.getElementById('searchCloseButton').style.display = 'none';
        alert("没有找到匹配的评论！");
      }}
    }}
    function displayPageResults() {{
      const totalResults = allResults.length;
      const totalPages = Math.ceil(totalResults / resultsPerPage);
      document.getElementById('searchCount').innerText = "共找到 " + totalResults + " 条记录";
      displayPagination(totalPages);
      const start = (currentPage - 1) * resultsPerPage;
      const end = start + resultsPerPage;
      const resultsContainer = document.getElementById('searchResults');
      resultsContainer.innerHTML = "";
      const paginatedResults = allResults.slice(start, end);
      paginatedResults.forEach(function(result) {{
        const li = document.createElement('li');
        li.classList.add('search-result-item');
        if(!document.body.classList.contains('dark-mode')) {{
          if(result.author.toLowerCase() === "andy" || result.author === "李宗恩") {{
            li.style.backgroundColor = "#fff5cc";
          }}
        }}
        // 如果是文章搜索的结果，则直接显示 text（其格式为 时间 - 标题 - 内容预览 ）
        if(result.id.startsWith("article-")) {{
           li.innerHTML = result.text;
        }} else {{
           li.innerHTML = `<strong>${{result.articleTitle}}</strong> - ${{result.text}}`;
        }}
        // 初始化新生成节点的原始文本，并立即应用当前语言转换
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
            // 若是文章搜索结果，则跳转到文章 header，否则定位到具体评论
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
      jumpBtn.innerText = "跳转";
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
        prevBtn.innerText = "上一页";
        prevBtn.className = 'nav-btn';
        prevBtn.onclick = function() {{
          currentPage--;
          displayPageResults();
        }};
        bottomLine.appendChild(prevBtn);
      }}
      if(currentPage < totalPages) {{
        const nextBtn = document.createElement('button');
        nextBtn.innerText = "下一页";
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
    // 新增：点击文章标题或内容后消除红框和黄色高亮
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
        // 保存原始文本，确保语言转换时能更新
        option._originalText = article.title;
        dropdown.appendChild(option);
      }});
      // 更新下拉框内文本，确保语言转换生效
      initOriginalText(dropdown);
      applyLanguageToNode(dropdown);
    }}
    function changeArticle() {{
      const dropdown = document.getElementById('articleDropdown');
      const articleIndex = parseInt(dropdown.value);
      const article = articlesData[articleIndex];
      const articleCommentsElem = document.getElementById('articleComments');
      articleCommentsElem.innerHTML = article.comments_html;
      // 初始化新内容中的原始文本
      initOriginalText(articleCommentsElem);
      // 重新应用全文语言转换，确保当前语言设置生效
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
      jumpBtn.innerText = "跳转";
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
        prevBtn.innerText = "上一页";
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
        nextBtn.innerText = "下一页";
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
    /* ---------- 文章上一篇/下一篇功能 ---------- */
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
           alert("已经是第一篇文章了");
      }}
    }}
    function nextArticle() {{
      var currentIndex = parseInt(document.getElementById('articleDropdown').value);
      if(currentIndex < articlesData.length - 1) {{
           goToArticle(currentIndex + 1, true);
      }} else {{
           alert("已经是最后一篇文章了");
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
        var bg = obj.bgColor || "white";
        var presets = ["aliceblue", "honeydew", "mistyrose", "ivory", "lavender", "white"];
        if (presets.indexOf(bg) !== -1) {{
          document.getElementById('bgColorSelect').value = bg;
          document.getElementById('customBgColorContainer').style.display = 'none';
        }} else {{
          document.getElementById('bgColorSelect').value = "custom";
          document.getElementById('customBgColorContainer').style.display = 'block';
          document.getElementById('customBgColorInput').value = bg;
        }}
        document.getElementById('layoutStyleSelect').value = obj.layoutStyle || "card";
      }}
    }}
    function closeSettings() {{
      document.getElementById('settingsModal').style.display = 'none';
    }}
    function onBgColorSelectChange() {{
      var sel = document.getElementById('bgColorSelect').value;
      document.getElementById('customBgColorContainer').style.display = (sel === "custom") ? 'block' : 'none';
    }}
    // 更新布局风格
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
      var selectedBg = document.getElementById('bgColorSelect').value;
      var bgColor = (selectedBg === "custom") ? document.getElementById('customBgColorInput').value : selectedBg;
      const layoutStyle = document.getElementById('layoutStyleSelect').value;

      document.documentElement.style.setProperty('--font-size', fontSize + 'px');
      document.documentElement.style.setProperty('--line-height', lineHeight);
      document.documentElement.style.setProperty('--font-family', fontFamily);
      document.documentElement.style.setProperty('--text-color', textColor);
      // 更新全屏背景颜色
      document.documentElement.style.setProperty('--background-color', bgColor);
      // 根据字体大小计算标题大小（约1.375倍）
      var headingSize = Math.round(parseFloat(fontSize) * 1.375);
      document.documentElement.style.setProperty('--heading-size', headingSize + 'px');

      currentColor = bgColor;
      document.querySelectorAll('.comment.reply').forEach(function(comment) {{
        comment.style.backgroundColor = currentColor; 
      }});
      // 应用布局风格
      updateLayoutStyle(layoutStyle);

      const settings = {{
        fontSize: fontSize,
        lineHeight: lineHeight,
        fontFamily: fontFamily,
        textColor: textColor,
        bgColor: bgColor,
        layoutStyle: layoutStyle
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
      document.getElementById('bgColorSelect').value = "white";
      document.getElementById('customBgColorContainer').style.display = 'none';
      document.getElementById('layoutStyleSelect').value = "card";
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
      // 初始化全文原始文本存储
      initOriginalText(document.body);
      const settings = localStorage.getItem('userSettings');
      if(settings) {{
        const obj = JSON.parse(settings);
        document.documentElement.style.setProperty('--font-size', obj.fontSize + 'px');
        document.documentElement.style.setProperty('--line-height', obj.lineHeight);
        document.documentElement.style.setProperty('--font-family', obj.fontFamily);
        document.documentElement.style.setProperty('--text-color', obj.textColor);
        document.documentElement.style.setProperty('--background-color', obj.bgColor || "#f4f4f9");
        currentColor = obj.bgColor || "white";
        updateLayoutStyle(obj.layoutStyle || "card");
      }}
      const savedArticlePage = localStorage.getItem('savedArticlePage');
      if(savedArticlePage !== null) {{
         currentArticlePage = parseInt(savedArticlePage);
      }}
      initArticlePage();
      document.querySelectorAll('.comment .comment-text a').forEach(function(a) {{
        a.target = '_blank';
      }});
      // 根据当前语言更新全文显示（默认 original，不转换）
      applyLanguageToNode(document.body);
    }}
    let currentColor = "white";
    /* ---------------- 暗黑模式切换函数（在HTML按钮里调用） ---------------- */
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
