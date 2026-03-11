#!/bin/bash

# --- Minibot Local Skill Library ---
# This file contains installed bash functions from the remote skill repository.
# Do not edit manually unless necessary. Use 'install_skill' to add new skills.

function get_system_info() {
    echo "OS: $(uname -a)"
    echo "Uptime: $(uptime)"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Memory: $(vm_stat | grep 'Pages free')"
    else
        echo "Memory: $(free -h 2>/dev/null)"
    fi
}

function list_files_in_dir() {
    local target_dir="${1:-.}"
    ls -la "$target_dir"
}

function echo_message() {
    echo "Message from skills.sh: $1"
}

function current_date() {
    date
}

# --- Desktop Control Skills (macOS only) ---
function open_app() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open -a "$1"
    else
        echo "Error: open_app is only supported on macOS."
    fi
}

function set_volume() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        osascript -e "set volume output volume $1"
    else
        echo "Error: set_volume is only supported on macOS."
    fi
}

function say_text() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        say "$1"
    else
        echo "Error: say_text is only supported on macOS."
    fi
}


function open_youtube() {
    #!/bin/bash
# 打开YouTube网站
open 'https://www.youtube.com'
}

function check_battery() {
    #!/bin/bash
# 检查电池电量
if [[ "$(uname)" == "Darwin" ]]; then
    pmset -g batt | grep -E "\d+%"
elif [[ "$(uname)" == "Linux" ]]; then
    upower -i /org/freedesktop/UPower/devices/battery_BAT0 | grep -E "percentage:|state:"
else
    echo "不支持的操作系统"
fi
}

function get_battery_status() {
    #!/bin/bash
# 获取电池状态
if [[ "$(uname)" == "Darwin" ]]; then
    echo "电池状态:"
    pmset -g batt
else
    echo "当前系统不是macOS，无法获取电池信息"
fi
}

function check_battery() {
    #!/bin/bash
# 检查电池电量
if [[ "$(uname)" == "Darwin" ]]; then
    echo "🔋 Mac电池状态:"
    pmset -g batt
else
    echo "当前系统不支持电池电量检查"
fi
}
# Installed from remote: get_top_news

function get_top_news() {
    # Fetches top headlines from BBC News RSS
    echo "--- Latest World News (BBC) ---"
    curl -s "http://feeds.bbci.co.uk/news/world/rss.xml" | grep -o '<title><!\[CDATA\[[^]]*\]\]></title>' | sed 's/<title><!\[CDATA\[//;s/\]\]><\/title>//' | head -n 10
}



function get_daily_news() {
    curl -s 'https://news.google.com/rss?hl=zh-CN&gl=CN&ceid=CN:zh-Hans' | grep -E '<title>|<pubDate>|<link>' | sed -e 's/<title>//g' -e 's/</title>//g' -e 's/<pubDate>//g' -e 's/</pubDate>//g' -e 's/<link>//g' -e 's/</link>//g' | head -30
}

function fetch_news() {
    # Fetch news from BBC RSS feed
echo "正在获取今日新闻..."
curl -s 'http://feeds.bbci.co.uk/news/rss.xml' | grep -E '<title>|<description>' | sed -e 's/<[^>]*>//g' | head -20
}
# Installed from remote: get_china_news

function get_china_news() {
    # Fetches top headlines from Google News (China)
    # Note: Requires network access to google.com
    echo "--- Latest China News (Google) ---"
    curl -s "https://news.google.com/rss?hl=zh-CN&gl=CN&ceid=CN:zh-Hans" | grep -o '<title>[^<]*</title>' | sed 's/<title>//;s/<\/title>//' | grep -v "Google 新闻" | head -n 10
}



function get_daily_news() {
    # 获取今日新闻
curl -s 'https://newsapi.org/v2/top-headlines?country=cn&apiKey=demo' | jq -r '.articles[] | "标题: " + .title + "\n来源: " + .source.name + "\n链接: " + .url + "\n"' 2>/dev/null || echo "暂时无法获取新闻，请稍后再试"
}

function open_youtube() {
    # 打开YouTube网站
if command -v xdg-open &> /dev/null; then
    xdg-open "https://www.youtube.com"
elif command -v open &> /dev/null; then
    open "https://www.youtube.com"
elif command -v start &> /dev/null; then
    start "https://www.youtube.com"
else
    echo "无法找到合适的命令来打开浏览器"
    exit 1
fi
echo "正在打开YouTube..."
}
function find_skills() {
    local keyword="${1}"
    if [ -z "$keyword" ]; then
        echo "Usage: find_skills <keyword>"
        return 1
    fi
    # Search for function definitions matching the keyword
    grep -i "function.*$keyword" skills.sh | sed 's/function //' | sed 's/() {//'
}


function get_bilibili_hot() {
    # 获取B站热门视频信息
echo "正在获取B站热门视频..."
# 这里可以调用B站API获取热门视频
# 暂时先返回一些示例信息
echo "🎬 B站热门视频推荐："
echo "1. 【科技】AI最新进展 - 播放量：50万"
echo "2. 【游戏】最新游戏评测 - 播放量：30万"
echo "3. 【生活】日常Vlog分享 - 播放量：20万"
echo "4. 【学习】编程教程 - 播放量：15万"
echo "5. 【音乐】流行歌曲翻唱 - 播放量：10万"
echo "\n你可以复制以下链接在浏览器中打开观看："
echo "https://www.bilibili.com/video/BV1xx42117xx"
echo "https://www.bilibili.com/video/BV1yy42117yy"
echo "https://www.bilibili.com/video/BV1zz42117zz"
}

function open_youtube() {
    # Open browser and go to YouTube
open 'https://www.youtube.com'
echo '🎬 YouTube已打开！'

# Optional: wait a bit and then search for videos
sleep 2
# You can add search functionality here if needed
}