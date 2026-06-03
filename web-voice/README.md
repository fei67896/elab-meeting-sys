# web-voice（已停用）

> **此独立前端已合并进 `web-meeting`，请勿再启动 `:3001`。**

会议秘书直播界面现位于会议台同一应用内：

| 原地址 | 新地址 |
|--------|--------|
| `https://localhost:3001` | `https://localhost:3000/#/voice` |

## 启动方式

只需启动 **一个** 前端：

```bash
cd web-meeting && npm install && npm run dev
# https://localhost:3000
```

导航栏 **「会议秘书」** 或直达 `#/voice`。

## 代码去向

原 `web-voice/src` 中的 UI 已迁入：

```text
web-meeting/src/views/VoiceHome.vue
web-meeting/src/components/voice/
web-meeting/src/composables/useScheduledMeetings.js
web-meeting/src/composables/useFocusHistory.js
```

本目录保留仅供历史参考，后续可能删除。
