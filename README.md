# 叮当同学D1热敏打印机PoC

> ⚠️ 本代码仅供学习交流，请勿用于商业用途。

需求就是远程打小纸条，咕咕机开发者平台好像没了，自己造又太粗糙，所以决定整一个现成的逆向。

商品名`叮当同学D1`，PDD很多，大概都是50左右，200dpi也还算够用，所以就选他了。（给个链接 https://mobile.yangkeduo.com/goods2.html?goods_id=215919711645

## 依赖

```bash
$ pip3 install bleak
```

## Quickstart

```bash
$ python3 scan.py # 扫描你的打印机的MAC地址
$ python3 app.py # 打印
```

## 协议描述

~~看代码去吧~~

有一些膜法还是提一下吧
- `hexlen`就是图像数据转为16进制排好的行数，至于为什么+3我也不知道，实践出真知，少了会在图片末尾打乱码，然后这里发送的时候是小端模式，要倒过来发
- 结束信号应该是`0x1B4A64`，逆向iOS App的结果是应该负载图像payload的后面，但是抓到的包都是新行，所以就新行吧

## 致谢

- 感谢[Lakr](https://github.com/Lakr233)陪我折腾到三点，但就是这个家伙想的馊主意(°ㅂ° ╬)
- 感谢【数据删除】治愈我一天还给了点灵感
- 感谢学校的猫猫出镜
