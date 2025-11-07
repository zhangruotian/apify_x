#!/bin/bash

# 停止所有 classify_flood_relevance 相关进程

echo "🔍 Searching for running classify_flood processes..."

# 查找所有相关进程
PIDS=$(pgrep -f "classify_flood_relevance" 2>/dev/null)

if [ -z "$PIDS" ]; then
    echo "✅ No classify_flood_relevance processes found"
    exit 0
fi

echo "Found processes: $PIDS"

# 先尝试优雅终止（SIGTERM）
for PID in $PIDS; do
    echo "🛑 Sending SIGTERM to process $PID..."
    kill -TERM $PID 2>/dev/null
done

# 等待 2 秒
sleep 2

# 检查是否还有进程在运行
REMAINING=$(pgrep -f "classify_flood_relevance" 2>/dev/null)

if [ ! -z "$REMAINING" ]; then
    echo "⚠️  Some processes still running, force killing..."
    for PID in $REMAINING; do
        echo "💀 Force killing process $PID..."
        kill -9 $PID 2>/dev/null
    done
    sleep 1
fi

# 最终检查
FINAL=$(pgrep -f "classify_flood_relevance" 2>/dev/null)
if [ -z "$FINAL" ]; then
    echo "✅ All classify_flood_relevance processes stopped"
else
    echo "❌ Warning: Some processes may still be running: $FINAL"
fi

