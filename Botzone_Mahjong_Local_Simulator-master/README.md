# BOTZONE MAHJONG LOCAL SIMULATOR

注意，整个操作模式基本和BOTZONE在线平台上相同，但是全部按照**"长时运行"**的方式进行

在运行过程中进行的非法操作会被raise出来。

## 输入Example

这里提供一个Example

```
{"requests":["0 0 0"]}
1 0 0 0 0 W1 W1 W1 W2 W2 W2 W3 W3 W3 W4 W4 W4 W5
```

## Agent

我们可以使用目录下的Agent和./ais/{name}/下的bot进行交互

具体为访问 main.py / main / main.exe 在MacOS/Windows上均可使用

## Example

``` python
env = MahjongEnvironment()
env.reset()
while not env.isEnd():
    states = env.state()
    responses = []
    for x in states:
        responses.append((player[x[1]].make_action(x[0]),x[1]))
    env.step(responses)
```

这里的player你可以使用各种方式进行实现，比如用socket/pipe之类的就可以把player做到单独的文件里面了

这里只提供本地评测的环境（如果你用的python那你就爽了）


### 用到的库

MahjongGB(https://github.com/ailab-pku/Chinese-Standard-Mahjong)
详见requirement.txt

## 注意

只经过少量测试

### contrib

JeremyGuo
Hineven