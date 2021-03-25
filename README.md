# ZhiRemote

Generic Remote Control Device for HomeAssistant

基于 `remote` 遥控器的通用 `fan` `cover` `climate` `media_player` 组件。

## 1. 安装准备

把 `zhiremote` 放入 `custom_components`。

_依赖 [Zhi](https://github.com/Yonsm/Zhi)，请一并安装。_

## 2. 配置方法

参见 [我的 Home Assistant 配置](https://github.com/Yonsm/.homeassistant) 中 [configuration.yaml](https://github.com/Yonsm/.homeassistant/blob/main/configuration.yaml)

```yaml
fan:
  - platform: zhiremote
    name: 客厅壁扇
    sender: remote.ke_ting_yao_kong
    command: midea_fan

climate:
  - platform: zhiremote
    name: 书房空调
    sender: remote.shu_fang_yao_kong
    command: mitsubishi_climate
    sensor: sensor.shu_fang_wen_du

cover:
  - platform: zhiremote
    name: 书房窗帘
    sender: remote.shu_fang_yao_kong
    travel: 13
    command: dooya_cover

media_player:
  - platform: zhiremote
    name: 书房投影仪
    sender: remote.shu_fang_yao_kong
    command: viewsonic_projector
```

## 3. 参考

- [Yonsm.NET](https://yonsm.github.io)
- [Yonsm's .homeassistant](https://github.com/Yonsm/.homeassistant)
