musicpy
=======

[English [中文](#musicpy-1)]

#### Have you ever thought about writing music with codes in a very concise, human-readable syntax?
#### Musicpy is a music programming language in Python designed to write music in very handy syntax through music theory and algorithms. It is easy to learn and write, easy to read, and incorporates a fully computerized music theory system.
#### Musicpy can do way more than just writing music. This package can also be used to analyze music through music theory logic, and you can design algorithms to explore the endless possibilities of music, all with musicpy.

I've been developing many python modules and packages on my own in spare time. These python modules and packages are mainly for mathematics, statistics, games and music.

Today I wanna introduce to you a python domain-specific language developed by me that lets you write music with codes in very concise, human-readable syntax: **musicpy**.

This python package allows you to express notes, rhythms, dynamics and other information of a piece of music with a very concise syntax. It can generate music through music theory logic and perform advanced music theory operations. You can easily output musicpy codes into midi file format, and you can also easily input any midi files and convert to musicpy's data structures to do a lot of advanced music theory operations. The syntax of musicpy is very concise and flexible, and it makes the codes written in musicpy very human-readable, and musicpy is fully compatible with python, which means you can write python codes to interact with musicpy. Because musicpy is involved with everything in music theory, I recommend using this package after learning at least some fundamentals of music theory so you can use musicpy more clearly and satisfiedly. On the other hand, you should be able to play around with them after having a look at this [wiki](https://github.com/Rainbow-Dreamer/musicpy/wiki) I wrote if you are already familiar with music theory.

Documentation
-------------
See [musicpy wiki](https://github.com/Rainbow-Dreamer/musicpy/wiki) for complete and detailed tutorials about syntax, data structures and usages of musicpy.  
This wiki is updated frequently, since new functions and abilities are adding to musicpy regularly.  
The syntax and abilities of this wiki is synchronized with the latest released version of musicpy.

[Musicpy introduction and tutorial video part 1](https://www.bilibili.com/video/BV1754y197a9/)

[Musicpy composition examples demonstration and musicpy experimental compositions video](https://www.bilibili.com/video/BV18z4y1r7Pk/)

Musicpy's data sturctures, basic syntax, usage and more details are in this [wiki](https://github.com/Rainbow-Dreamer/musicpy/wiki), I'll try to make sure everything is detailed and clear, and with examples.

you can click [here](https://www.jianguoyun.com/p/DRJrawoQhPG0CBiL2fMD) to download the entire wiki of musicpy I written in pdf and markdown format, which is updating continuously.

Installation
-------------
Make sure you have installed python (version >= 3.7) in your pc first.
Execute the following command in the terminal to install musicpy by pip.

```shell
pip install musicpy
```

In addition, I also wrote a musicpy editor for writing and compiling musicpy code more easily than regular python IDE with real-time automatic compilation and execution,
there are some syntactic sugar and you can listen to the music generating from your musicpy code on the fly, it is more convenient and interactive.  
I strongly recommend to use this musicpy editor to write musicpy code.  
You can download this musicpy editor at the [latest release](https://github.com/Rainbow-Dreamer/musicpy/releases/latest) of musicpy.  
Please be sure to download the musicpy folder from github first ([you can click here](https://github.com/Rainbow-Dreamer/musicpy/archive/master.zip)), and then go to the `musicpy editor` folder, you can go to `English Version` folder if you want to use English version of musicpy editor or `中文版` folder if you want to use Chinese version.  
Put this exe file inside the folder you choose to be able to use this editor.  
You could also run the python file musicpy editor.pyw in the folder you choose, but you need to make sure you have installed python (version >= 3.7) in your computer first.  
For more details including abilities and usages of this musicpy editor, see the [documentation](https://github.com/Rainbow-Dreamer/musicpy/wiki/How-to-use-musicpy#I-wrote-an-efficient-IDE-specifically-for-musicpy-for-everyone-to-use) here.

Musicpy is all compatible with Windows, macOS and Linux, but there are some important notes if you encounter some errors on Linux or macOS.

Note1: If you encounter ```pygame.error: Couldn't open /etc/timidity/freepats.cfg``` errors on Linux, here is the solutions to fix it,
open the terminal and run `sudo apt-get install freepats` and it will fix the errors.

Note2: If you are using macOS, please be sure to use python 3.7.1/3.7.9 to run musicpy, because it seems that on macOS, some of the requirements python modules of musicpy may not be compatible with some of the newer python versions (for example python 3.9). It is tested by my friend that on macOS with python 3.7.1 (and python 3.7.9 tested by me), musicpy could run and play the musicpy codes without any errors, but other versions may not, so please be sure to use python 3.7.1/3.7.9 to run musicpy if you are using macOS.

Note3: On all of Windows, macOS and Linux, you can use pip to install musicpy in cmd/terminal.

Importing
-------------
Place this line at the start of the files you want to have it used in.

```python
from musicpy import *
```
or
```python
import musicpy as mp
```
to avoid possible conflicts with the function names and variable names of other modules.

Composition Examples
-------------
Because musicpy has too many features to introduce, I will just give a simple example code of music programming in musicpy:

```python
# a nylon string guitar plays broken chords on a chord progression

guitar = (C('CM7', 3, 1/4, 1/8)^2 |
          C('G7sus', 2, 1/4, 1/8)^2 |
          C('A7sus', 2, 1/4, 1/8)^2 |
          C('Em7', 2, 1/4, 1/8)^2 | 
          C('FM7', 2, 1/4, 1/8)^2 |
          C('CM7', 3, 1/4, 1/8)@1 |
          C('AbM7', 2, 1/4, 1/8)^2 |
          C('G7sus', 2, 1/4, 1/8)^2) * 2

play(guitar, bpm=100, instrument=25)
```
[Click here to hear what this sounds like (Microsoft GS Wavetable Synth)](https://drive.google.com/file/d/104QnivVmBH395dLaUKnvEXSC5ZBDBt2E/view?usp=sharing)

If you think this is too simple, musicpy could also produce music like [this](https://drive.google.com/file/d/1j66Ux0KYMiOW6yHGBidIhwF9zcbDG5W0/view?usp=sharing) within 30 lines of code (could be even shorter if you don't care about readability). Anyway, this is just an example of a very short piece of electronic dance music, and not for complexity.

For more musicpy composition examples, please refer to the musicpy composition examples chapters in wiki.

Brief Introduction of Data Structures
-------------
`note`, `chord`, `scale` are the basic classes in musicpy that builds up the base of music programming, and there are way more musical classes in musicpy.

Because of musicpy's data structure design, the `note` class is congruent to integers, which means that it can be used as int directly.

The `chord` class is the set of notes, which means that it itself can be seen as a set of integers, a vector, or even a matrix (e.g. a set of chord progressions can be seen as a combination of multiple vectors, which results in a form of matrix with lines and columns indexed)

Because of that, `note`, `chord` and `scale` classes can all be arithmetically used in calculation, with examples of Linear Algebra and Discrete Mathmetics. It is also possible to write an algorithm following music theory logics using musicpy's data structure, or to perform experiments on music with the help of pure mathematics logics.

Many experimental music styles nowadays, like serialism, aleatoric music, postmodern music (like minimalist music), are theoretically possible to make upon the arithmetically performable data structures provided in musicpy. Of course musicpy can be used to write any kind of classical music, jazz, or pop music.

For more detailed descriptions of data structures of musicpy, please refer to wiki.

[Reasons Why I Develop This Language and Keep Working on This Project (feel free to skip this part if you are not interested)](#summary)
-------------
There are two main reasons why I develop this language. Firstly, compared with project files and midi files that simply store unitary information such as notes, intensity, tempo, etc., it would be more meaningful to represent how a piece of music is realized from a compositional point of view, in terms of music theory. Most music is extremely regular in music theory, as long as it is not modernist atonal music, and these rules can be greatly simplified by abstracting them into logical statements of music theory. (A midi file with 1000 notes, for example, can actually be reduced to a few lines of code from a music theory perspective.) Secondly, the language was developed so that the composing AI could compose with a real understanding of music theory (instead of deep learning and feeding a lot of data), and the language is also an interface that allows the AI to compose with a human-like mind once it understands the syntax of music theory. We can tell AI the rules on music theory, what is good to do and what is not, and these things can still be quantified, so this music theory library can also be used as a music theory interface to communicate music between people and AI. So, for example, if you want AI to learn someone's composing style, you can also quantify that person's style in music theory, and each style corresponds to some different music theory logic rules, which can be written to AI, and after this library, AI can realize imitating that person's style. If it is the AI's own original style, then it is looking for possibilities from various complex composition rules.

I am thinking that without deep learning, neural network, teaching AI music theory and someone's stylized music theory rules, AI may be able to do better than deep learning and big data training. That's why I want to use this library to teach AI human music theory, so that AI can understand music theory in a real sense, so that composing music won't be hard and random. That's why one of my original reasons for writing this library was to avoid the deep learning. But I feel that it is really difficult to abstract the rules of music theory of different musicians, I will cheer up to write this algorithm qwq In addition, in fact, the musician himself can tell the AI how he likes to write his own music theory (that is, his own unique rules of music theory preference), then the AI will imitate it very well, because the AI does know music theory at that time, composition is not likely to have a sense of machine and random. At this point, what the AI is thinking in its head is exactly the same as what the musician is thinking in his head.

The AI does not have to follow the logical rules of music theory that we give it, but we can set a concept of "preference" for the AI. The AI will have a certain degree of preference for a certain style, but in addition, it will have its own unique style found in the rules of "correct music theory", so that the AI can say that it "has been influenced by some musicians to compose its own original style". When this preference is 0, the AI's composition will be exactly the style it found through music theory, just like a person who learns music theory by himself and starts to figure out his own composition style. An AI that knows music theory can easily find its own unique style to compose, and we don't even need to give it data to train, but just teach it music theory.

So how do we teach music theory to an AI? In music, ignoring the category of modernist music for the moment, most music follows some very basic rules of music theory. The rules here refer to how to write music theory OK and how to write music theory mistakes. For example, when writing harmonies, four-part homophony is often to be avoided, especially when writing orchestral parts in arrangements. For example, when writing a chord, if the note inside the chord has a minor second (or minor ninth) it will sound more fighting. For example, when the AI decides to write a piece starting from A major, it should pick chords from the A major scale in steps, possibly off-key, add a few subordinate chords, and after writing the main song part, it may modulate by circle of fifths, or major/minor thirds, modulate in the parallel major and minor keys, etc. What we need to do is to tell the AI how to write the music correctly, and furthermore, how to write it in a way that sounds good, and that the AI will learn music theory well, will not forget it, and will be less likely to make mistakes, so they can write music that is truly their own. They will really know what music is and what music theory is. Because what the language of this library does is to abstract the music theory into logical statements, then every time we give "lessons" to the AI, we are expressing the person's own music theory concepts in the language of this library, and then writing them into the AI's database. In this way, the AI really learns the music theory. Composing AI in this way does not need deep learning, training set, or big data, compared to composing AI trained by deep learning, which actually does not know what music theory is and has no concept of music, but just draws from the huge amount of training data. Another point is that since things can be described by concrete logic, there is no need for machine learning. If it is text recognition, image classification, which is more difficult to use abstract logic to describe things, that is the place where deep learning is useful.

Summary
-------------
I started to develop musicpy in October 2019, and now I have a complete set of music theory logic syntax, and there are many composing and arranging functions as well as advanced music theory logic operations. For details, please refer to the wiki. I will continue to update musicpy's video tutorials and wiki.

I'm working on musicpy continuously and updating musicpy very frequently, more and more musical features will be added, so that musicpy can do more with music.

Thank you for your support~

Contact
-------------
qq: 2180502841  
Bilibili account: Rainbow_Dreamer  
email: 2180502841@qq.com

musicpy
=======

[[English](#musicpy) 中文]

#### 你们有想过用代码来写音乐吗？musicpy是一个可以让你用编程写音乐的python领域特定语言，可以让你用非常简洁并且可读性高的语法通过乐理知识和算法写出优美的音乐。
#### musicpy容易学，容易写，可读性也比较强，并且是一个完全计算机化的乐理系统。musicpy除了用来创作音乐之外，还可以从乐理层面上来创作音乐和分析音乐，并且你可以在musicpy的基础上设计乐理算法来探索音乐的可能性。

最近几个月大学的学业繁忙，但是业余时间自己开发了很多python库，内容包括数学统计，各种游戏，还有音乐等等。其实还有试着写AI方面的，但是目前还是初期进度。

今天我想先介绍一下我正在开发中的一个python库：**musicpy**。

这个库可以让你用非常简洁的语法，来表达一段音乐的音符，节奏，力度等等信息，可以通过乐理逻辑来生成曲子，并且进行高级的乐理操作，可以简单地输出成 midi 文件的格式，也可以很简单地输入midi文件并且转换为musicpy的数据结构进行高级乐理的操作。musicpy的语法设计非常地简洁与灵活，因此musicpy的代码的可读性比较强，并且musicpy和python完全兼容，因此你可以写python代码和musicpy进行互动。这个库里面涉及到非常多的乐理知识，所以个人推荐至少要先了解一部分乐理再来使用会比较上手。相对地，如果你是一个对乐理比较了解的人，那么看完我在 [Wiki](https://github.com/Rainbow-Dreamer/musicpy/wiki
) 正在写的教程之后你应该很快就上手了。

使用说明文档
-------------
你可以看[musicpy wiki](https://github.com/Rainbow-Dreamer/musicpy/wiki)，这里有完整并且详细的使用教程，你可以了解并且学习musicpy的语法，数据结构与具体使用。  
这个wiki经常更新，因为musicpy经常在新版本中加入全新的函数和功能。  
wiki里的语法与功能与最新版本的musicpy是同步的。

[musicpy介绍与使用教程视频第一期](https://www.bilibili.com/video/BV1754y197a9/)

[musicpy作曲示例实际演示以及musicpy实验作曲视频](https://www.bilibili.com/video/BV18z4y1r7Pk/)

详细的 musicpy数据结构，基础语法以及使用教程，请看我正在写的 [Wiki](https://github.com/Rainbow-Dreamer/musicpy/wiki)，我会尽量把所有的细节都讲清楚，并且提供示例代码。 

我写的musicpy的wiki的pdf档和markdown档全套可以点击[这里](https://www.jianguoyun.com/p/DRJrawoQhPG0CBiL2fMD)下载，正在不断地更新中。

安装musicpy
-------------
先确定电脑里有安装python，python版本最好是 >= 3.7，
打开电脑的cmd然后输入

```shell
pip install musicpy
```

除此之外，我为musicpy专门写了一个编辑器，你可以在这里写musicpy的代码，这个编辑器可以实时自动编译和运行，比在常规的python IDE里更加方便。这个编辑器有一些语法糖，并且你可以实时地听到你写的musicpy代码生成的音乐，更加地方便与互动。  
我强烈推荐大家使用这个musicpy编辑器来写musicpy代码。  
你可以到muscipy的[最新发布版本](https://github.com/Rainbow-Dreamer/musicpy/releases/latest)下载这个musicpy编辑器。  
请务必先从github下载musicpy文件夹（[你可以点击这里](https://github.com/Rainbow-Dreamer/musicpy/archive/master.zip)），然后进入`musicpy editor`文件夹，如果你想使用英文版的musicpy编辑器，你可以进入`English Version`文件夹，如果你想使用中文版，你可以进入`中文版`文件夹。  
把这个exe文件放在你选择的文件夹里面，就能使用这个编辑器了。  
你也可以在你选择的文件夹中运行python文件musicpy editor.pyw，但你需要确保你的电脑已经安装了python（版本>=3.7）。 
如果想要了解这个musicpy编辑器的更多细节(包括功能和使用说明)，可以看这个[文档](https://github.com/Rainbow-Dreamer/musicpy/wiki/How-to-use-musicpy-%E5%A6%82%E4%BD%95%E4%BD%BF%E7%94%A8musicpy#%E6%88%91%E4%B8%93%E9%97%A8%E4%B8%BAmusicpy%E8%BF%99%E4%B8%AA%E9%A1%B9%E7%9B%AE%E5%86%99%E4%BA%86%E4%B8%80%E4%B8%AA%E9%AB%98%E6%95%88%E7%9A%84IDE%E4%BE%9B%E5%A4%A7%E5%AE%B6%E4%BD%BF%E7%94%A8)。

Musicpy对于Windows, macOS和Linux都是兼容的, 但是这里有一些在Linux或者macOS上可能会遇到的问题的解决方案。

情况1: 如果你在Linux上遇到```pygame.error: Couldn't open /etc/timidity/freepats.cfg``` 的错误, 这里是一个解决办法,
打开终端并且运行`sudo apt-get install freepats`即可解决这个问题。

情况2: 如果你使用的是macOS,请确定使用python 3.7.1/3.7.9来运行musicpy,因为在macOS上有一些musicpy的依赖库貌似和一些更新的python版本不太兼容(比如python 3.9)。  
经过我的朋友测试，在macOS上python 3.7.1运行musicpy不会报错 (还有python 3.7.9，经过我的测试)，但是其他的版本也许不一定，所以如果你使用的是macOS,请确定使用python 3.7.1/3.7.9来运行musicpy。

情况3: 在Windows, macOS和Linux上，你都可以在终端(cmd/terminal)里使用pip安装musicpy。

import这个库
-------------
在你喜欢用的python的IDE里面输入

```python
from musicpy import *
```
或者
```python
import musicpy as mp
```
以避免和其他模块的可能的函数名和变量名的冲突。

作曲示例
-------------
由于musicpy有太多的特性可以介绍，在这里就先写一段用musicpy语言作曲的代码示例:

```python
# 尼龙弦吉他分解和弦演奏一个和弦进行

guitar = (C('CM7', 3, 1/4, 1/8)^2 |
          C('G7sus', 2, 1/4, 1/8)^2 |
          C('A7sus', 2, 1/4, 1/8)^2 |
          C('Em7', 2, 1/4, 1/8)^2 | 
          C('FM7', 2, 1/4, 1/8)^2 |
          C('CM7', 3, 1/4, 1/8)@1 |
          C('AbM7', 2, 1/4, 1/8)^2 |
          C('G7sus', 2, 1/4, 1/8)^2) * 2

play(guitar, bpm=100, instrument=25)
```
[点击这里试听 (Microsoft GS Wavetable Synth)](https://drive.google.com/file/d/104QnivVmBH395dLaUKnvEXSC5ZBDBt2E/view?usp=sharing)

如果你认为这太过于简单，musicpy也可以在不到30行的代码内制作出[这样](https://drive.google.com/file/d/1j66Ux0KYMiOW6yHGBidIhwF9zcbDG5W0/view?usp=sharing)的音乐(如果你不关心可读性，代码还可以更短)。不过，这也只是一个非常短的电子舞曲的例子，并没有写的很复杂。

更多的musicpy的作曲示例可以看wiki的作曲示例章节。

数据结构简述
-------------
在 musicpy里面，几个基本的类是 `note`（音符），`chord`（和弦）和 `scale`（音阶）。这几个类是构成音乐代码的基础。除此之外，musicpy还有很多其他的乐理类型。

在 musicpy这门语言的数据结构设计中，音符类本身是等值为纯数字的，也就是完全可以作为纯数字使用。

和弦类是音符类的集合，也说明和弦类本身等值为一个全部都是数字的集合，也可以作为向量，甚至矩阵来看待（比如多个和弦的连接走向就可以看作多个向量的拼接，因此也就有了行列数，也就是矩阵的形式）。

也因此在这门语言的数据结构设计中，音符类，和弦类，音阶类都是可以进行数学运算的，比如线性代数领域的运算，离散数学领域的运算等等。也可以在这门语言的数据结构的基础上建立一整套乐理逻辑的算法，结合纯数学逻辑来进行多方面的音乐分析研究。

现代音乐领域的很多实验性质的音乐，比如序列主义，偶然音乐，后现代主义音乐（比如极简主义音乐），理论上全部都可以在这门语言的纯数字化的数据结构的基础上进行严格的创作。即使不提实验性质的音乐，这门语言也可以写任何的古典音乐，爵士音乐，流行音乐。

关于更加详细的musicpy的数据结构的描述，请看wiki。

[我开发musicpy的初衷(如果你不感兴趣的话可以跳过这部分内容)](#总结)
-------------
我开发这个语言主要的初衷有两点，第一，比起工程文件和 midi 文件单纯存储音符，力度，速度等单位化的信息，如果能够按照乐理上的角度来表示一段音乐从作曲上的角度是如何实现的，那就更加有表示的意义了。而且只要不是现代主义无调性音乐，大部分的音乐都是极其具有乐理上的规律性的，这些规律抽象成乐理逻辑语句可以大大地精简化。（比如一个 midi 文件 1000 个音符，实际上按照乐理角度可能可以简化到几句代码）。第二，开发这个语言是为了让作曲 AI 能够在真正懂得乐理的情况下来作曲（而不是深度学习，喂大量的数据），这个语言也算是一个接口，AI 只要把乐理的语法搞懂了，那作曲就会拥有和人一样的思维。我们可以把乐理上的规则，做什么好不做什么好告诉 AI，这些东西还是可以量化的，所以这个乐理库也可以作为一个乐理接口，沟通人和 AI 之间的音乐。因此，比如想让 AI 学习某个人的作曲风格，那么在乐理上面也同样可以量化这个人的风格，每种风格对应着一些不同的乐理逻辑规则，这些只要写给 AI，经过我这个库，AI 就可以实现模仿那个人的风格了。如果是 AI 自己原创风格，那就是从各种复杂的作曲规则里寻找可能性。

我在想不用深度学习，神经网络这些东西，直接教给 AI 乐理和某个人的风格化的乐理规则，那么 AI 或许可以做的比深度学习大数据训练出来的更好。因为大数据训练只是给 AI 模仿数据本身而已，这样其实 AI 并没有真正地和人类自己一样理解作曲是什么，乐理是什么，所以我才想通过这个库实现把人的乐理同样教给 AI，让 AI 真正意义上地理解乐理，这样的话，作曲起来就不会生硬了，没有机器和随机的感觉了。所以我写这个库的初衷之一就是避开深度学习那一套。但是感觉抽象出不同音乐人的乐理规则确实很有难度，我会加油写好这个算法的qwq 另外其实也可以音乐人自己告诉 AI 他自己乐理上喜欢怎么写（也就是自己独特的乐理偏好规则），那么 AI 就会模仿的很到位，因为 AI 那时候确实懂得乐理了，作曲不可能会有机器感和随机感，此时 AI 脑子里想的就和音乐人脑子里想的是完全一样的东西。

AI 不必完全按照我们给他的乐理逻辑规则来创作，我们可以设置一个“偏好度”的概念给 AI，AI 在自己作曲时会有一定程度地偏好某种风格，但是除此之外会有自己在“符合正确乐理”的规则里面找到的独特的风格，这样 AI 就可以说“受到了某些音乐人的影响下自己原创的作曲风格了”。当这个偏好度为 0 时，AI 的作曲将会完全是自己通过乐理寻找到的风格，就像一个人自己学习了乐理之后，开始摸索自己的作曲风格一样。一个懂得乐理的 AI 很容易找到自己独特的风格来作曲，我们甚至都不需要给他数据来训练，而只要教给 AI 乐理就行。

那么怎么教给 AI 乐理呢？在音乐上面，暂时不考虑现代主义音乐的范畴，那么绝大部分的音乐都是遵循着一些很基本的乐理规则的。这里的规则指的是，怎么样写乐理上 OK，怎么样写犯了乐理上的错误。比如写和声的时候，四部同向往往是要避免的，尤其是在编曲时写管弦乐的部分。比如写一个和弦，如果和弦里面的音出现小二度（或者小九度）会听着比较打架。比如当 AI 自己决定一首曲子要从 A 大调开始写，那么他应该从 A 大调音阶里按照级数来选取和弦，有可能适当地离调一下，加几个副属和弦，写完主歌部分可能按照五度圈转个调，或者大三度/小三度转调，同主音大小调转调等等。我们需要做的事情就是告诉 AI 作曲的时候怎么写是正确的，更进一步的，怎么写听着比较有水平。AI 学好了乐理，不会忘记，也比较难犯错，因此可以写出真正属于 AI 自己的音乐。他们会真正懂得音乐是什么，乐理是什么。因为这个库的语言做的事情就是把乐理抽象成逻辑语句，那么我们每次给 AI “上课”，就是把人自己的乐理概念用这个库的语言来表述，然后写进 AI 的数据库里。通过这种方式，AI 真正的学习到了乐理。这样的作曲 AI，不需要深度学习，不需要训练集，不需要大数据，而与之相比，那些深度学习训练出来的作曲 AI 实际上根本就不懂乐理是什么，也没有音乐的概念，他们只是从海量的训练数据里面照葫芦画瓢而已。还有一个重点是，既然可以用具体的逻辑来描述的事情，其实是不需要机器学习的。如果是文字识别，图像分类这些比较难以用抽象的逻辑来描述的事情，那才是深度学习的用武之地。

总结
-------------
我从2019年的10月份开始开发musicpy，到现在已经有一套完整的乐理逻辑语法了，还有很多作曲编曲以及高级乐理逻辑操作的功能，详细请看wiki。musicpy的视频教程和wiki我都会持续更新。
musicpy我一直在持续更新中，不断地加入新的乐理功能，让musicpy在音乐上能做到的事情更多。

感谢大家的支持~

联系方式
-------------
qq: 2180502841  
B站账号: Rainbow_Dreamer  
邮箱: 2180502841@qq.com
