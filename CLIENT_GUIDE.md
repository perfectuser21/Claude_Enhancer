
# VibePilot V2 客户端连接指南

## 方法1: SSH隧道 (推荐)
```bash
# 建立SSH隧道
ssh -L 9999:localhost:9999 root@146.190.52.84

# 在新终端访问
open http://localhost:9999
```

## 方法2: 直接访问 (如果网络允许)
```
http://146.190.52.84:9999
```

## 方法3: 通过Nginx代理 (端口80)
```
http://146.190.52.84
```

## 故障排除
1. 如果连接失败，尝试重启VibePilot:
   ```bash
   /usr/local/bin/start_vibepilot.sh
   ```

2. 检查服务状态:
   ```bash
   curl http://localhost:9999/health
   ```

3. 查看日志:
   ```bash
   tail -f /var/log/vibepilot.log
   ```

## 网络诊断
如果仍有问题，运行网络诊断:
```bash
python3 /home/xx/dev/VibePilot_Kit_v2/network_fixer.py --diagnose
```
