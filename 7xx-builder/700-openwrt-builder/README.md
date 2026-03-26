# openwrt build env

下载lede源码

```
git clone https://github.com/coolsnowwolf/lede
sed -i '$a src-git kenzo https://github.com/kenzok8/openwrt-packages' feeds.conf.default
sed -i '$a src-git small https://github.com/kenzok8/small' feeds.conf.default
```

先按照[文档](https://github.com/linktools-toolkit/linktools/blob/master/linktools-cntr/README.md)安装Docker、Python3等环境，然后按照以下命令部署Docker容器

```
ct-cntr repo add https://github.com/linktools-toolkit/linktools-homelab
ct-cntr add openwrt-builder
ct-cntr up
```
