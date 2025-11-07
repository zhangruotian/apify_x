#!/bin/bash

# 批量处理所有 TikTok flood CSV 文件
# 使用 caffeinate 防止 Mac 进入睡眠模式

# 清理函数：在退出时清理所有子进程
cleanup() {
    echo ""
    echo "🛑 收到退出信号，正在清理..."
    
    # 终止所有 Python classify 进程
    PIDS=$(pgrep -f "classify_flood_relevance" 2>/dev/null)
    if [ ! -z "$PIDS" ]; then
        echo "   终止 classify_flood_relevance 进程..."
        kill -TERM $PIDS 2>/dev/null
        sleep 2
        # 强制终止仍在运行的进程
        REMAINING=$(pgrep -f "classify_flood_relevance" 2>/dev/null)
        if [ ! -z "$REMAINING" ]; then
            kill -9 $REMAINING 2>/dev/null
        fi
    fi
    
    # 停止 caffeinate
    if [ ! -z "$CAFFEINATE_PID" ]; then
        kill $CAFFEINATE_PID 2>/dev/null || true
    fi
    
    echo "✅ 清理完成"
    exit 0
}

# 注册清理函数，捕获 SIGINT (Ctrl+C) 和 SIGTERM
trap cleanup SIGINT SIGTERM

# 激活 caffeinate（防止 Mac 睡眠）
# -w: 等待指定进程结束时才允许系统睡眠
# -d: 防止显示器进入睡眠
# -i: 防止系统空闲时进入睡眠
echo "🔋 启动 caffeinate，防止 Mac 进入睡眠模式..."
caffeinate -w $$ -d -i &
CAFFEINATE_PID=$!

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 定义要处理的 CSV 文件列表
CSV_FILES=(
    "tiktok/bangladesh_flood/csvs/tiktok_posts_20240801_to_20241031_with_local_paths.csv"
    "tiktok/kerala_flood/csvs/filtered_kerala_flood_posts_20240715_20241101_with_local_paths.csv"
    "tiktok/pakistan_flood/csvs/filtered_pakistan_flood_posts_20220601_20230101_with_local_paths.csv"
    "tiktok/south_asia_flood/csvs/filtered_south_asia_flood_posts_with_local_paths.csv"
)

# 创建日志文件
LOG_FILE="batch_classify_$(date +%Y%m%d_%H%M%S).log"
echo "📝 日志文件: $LOG_FILE"
echo ""

# 记录开始时间
START_TIME=$(date +%s)
echo "==========================================" | tee -a "$LOG_FILE"
echo "🚀 开始批量处理 TikTok flood CSV 文件" | tee -a "$LOG_FILE"
echo "开始时间: $(date)" | tee -a "$LOG_FILE"
echo "==========================================" | tee -a "$LOG_FILE"
echo ""

# 计数器
TOTAL_FILES=${#CSV_FILES[@]}
CURRENT_FILE=0
SUCCESS_COUNT=0
FAILED_FILES=()

# 循环处理每个 CSV 文件
for csv_file in "${CSV_FILES[@]}"; do
    CURRENT_FILE=$((CURRENT_FILE + 1))
    
    # 检查文件是否存在
    if [ ! -f "$csv_file" ]; then
        echo "⚠️  警告: 文件不存在，跳过: $csv_file"
        FAILED_FILES+=("$csv_file (文件不存在)")
        continue
    fi
    
    echo "==========================================" | tee -a "$LOG_FILE"
    echo "📄 [$CURRENT_FILE/$TOTAL_FILES] 处理文件: $csv_file" | tee -a "$LOG_FILE"
    echo "开始时间: $(date)" | tee -a "$LOG_FILE"
    echo "==========================================" | tee -a "$LOG_FILE"
    
    # 运行分类脚本（同时输出到终端和日志文件）
    # 默认并发数改为2，避免连接错误
    if python3 classify_flood_relevance.py "$csv_file" --start-idx 0 --max-concurrent 2 2>&1 | tee -a "$LOG_FILE"; then
        echo ""
        echo "✅ [$CURRENT_FILE/$TOTAL_FILES] 成功完成: $csv_file"
        echo "完成时间: $(date)"
        echo ""
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo ""
        echo "❌ [$CURRENT_FILE/$TOTAL_FILES] 处理失败: $csv_file"
        echo "失败时间: $(date)"
        echo ""
        FAILED_FILES+=("$csv_file")
        # 继续处理下一个文件，而不是退出
        echo "⚠️  继续处理下一个文件..."
        echo ""
    fi
    
    # 在文件之间稍作停顿
    sleep 2
done

# 计算总耗时
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
HOURS=$((ELAPSED / 3600))
MINUTES=$(((ELAPSED % 3600) / 60))
SECONDS=$((ELAPSED % 60))

echo "==========================================" | tee -a "$LOG_FILE"
echo "📊 批量处理总结" | tee -a "$LOG_FILE"
echo "==========================================" | tee -a "$LOG_FILE"
echo "成功处理: $SUCCESS_COUNT/$TOTAL_FILES 个文件" | tee -a "$LOG_FILE"
if [ ${#FAILED_FILES[@]} -gt 0 ]; then
    echo "" | tee -a "$LOG_FILE"
    echo "⚠️  失败的文件:" | tee -a "$LOG_FILE"
    for failed_file in "${FAILED_FILES[@]}"; do
        echo "   - $failed_file" | tee -a "$LOG_FILE"
    done
fi
echo "" | tee -a "$LOG_FILE"
echo "结束时间: $(date)" | tee -a "$LOG_FILE"
echo "总耗时: ${HOURS}小时 ${MINUTES}分钟 ${SECONDS}秒" | tee -a "$LOG_FILE"
echo "==========================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "📝 完整日志已保存到: $LOG_FILE" | tee -a "$LOG_FILE"

# 停止 caffeinate
if [ ! -z "$CAFFEINATE_PID" ]; then
    kill $CAFFEINATE_PID 2>/dev/null || true
    echo "🔋 已停止 caffeinate"
fi

# 如果有失败的文件，退出码为 1
if [ ${#FAILED_FILES[@]} -gt 0 ]; then
    exit 1
else
    exit 0
fi

