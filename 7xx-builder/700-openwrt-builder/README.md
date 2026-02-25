# openwrt build env

下载lede源码

```
git clone https://github.com/coolsnowwolf/lede
sed -i '$a src-git kenzo https://github.com/kenzok8/openwrt-packages' feeds.conf.default
sed -i '$a src-git small https://github.com/kenzok8/small' feeds.conf.default
```

先按照[文档](../../README.md)安装依赖项，然后按照以下命令部署docker容器

```
python3 deploy.py add build-openwrt
python3 deploy.py
```
