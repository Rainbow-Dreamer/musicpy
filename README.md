musicpy
=======
[中文](https://github.com/Rainbow-Dreamer/musicpy/blob/master/README_cn.md)

Have you ever thought about writing music with codes in a very concise, human-readable syntax?

Musicpy is a music programming language in Python designed to write music in very handy syntax through music theory and algorithms. It is easy to learn and write, easy to read, and incorporates a fully computerized music theory system.

Musicpy can do way more than just writing music. This package can also be used to analyze music through music theory logic, and you can design algorithms to explore the endless possibilities of music, all with musicpy.

With musicpy, you can express notes, chords, melodies, rhythms, volumes and other information of a piece of music with a very concise syntax. It can generate music through music theory logic and perform advanced music theory operations. You can easily output musicpy codes into MIDI file format, and you can also easily load any MIDI files and convert to musicpy's data structures to do a lot of advanced music theory operations. The syntax of musicpy is very concise and flexible, and it makes the codes written in musicpy very human-readable, and musicpy is fully compatible with python, which means you can write python codes to interact with musicpy. Because musicpy is involved with everything in music theory, I recommend using this package after learning at least some fundamentals of music theory so you can use musicpy more clearly and satisfiedly. On the other hand, you should be able to play around with them after having a look at the documentation I wrote if you are already familiar with music theory.

Documentation
-------------
See [musicpy wiki](https://github.com/Rainbow-Dreamer/musicpy/wiki) or [Read the Docs documentation](https://musicpy.readthedocs.io/en/latest/) for complete and detailed tutorials about syntax, data structures and usages of musicpy.  

This wiki is updated frequently, since new functions and abilities are adding to musicpy regularly. The syntax and abilities of this wiki is synchronized with the latest released version of musicpy.

You can click [here](https://www.jianguoyun.com/p/Dapi5bEQhPG0CBijkqYE) to download the entire wiki of musicpy I written in pdf and markdown format, which is updating continuously.

Installation
-------------
Make sure you have installed python (version >= 3.7) in your pc first.
Run the following line in the terminal to install musicpy by pip.

```shell
pip install musicpy
```

**Note 1: On Linux, you need to make sure the installed pygame version is older than 2.0.3, otherwise the play function of musicpy won't work properly, this is due to an existing bug with newer versions of pygame. You can run `pip install pygame==2.0.2` in terminal to install pygame 2.0.2 or any version that is older than 2.0.3. You also need to install freepats to make the play function works on Linux, you can run `sudo apt-get install freepats` (on Ubuntu).**

**Note 2: If you cannot hear any sound when running the play function, this is because some IDE won't wait till the pygame's playback ends, they will stops the whole process after all of the code are executed without waiting for the playback. You can set `wait=True` in the parameter of the play function, which will block the function till the playback ends, so you can hear the sounds.**

In addition, I also wrote a musicpy editor for writing and compiling musicpy code more easily than regular python IDE with real-time automatic compilation and execution, there are some syntactic sugar and you can listen to the music generating from your musicpy code on the fly, it is more convenient and interactive. I strongly recommend to use this musicpy editor to write musicpy code. You can download this musicpy editor at the repository [musicpy_editor](https://github.com/Rainbow-Dreamer/musicpy_editor), the preparation steps are in the README.

Musicpy is all compatible with Windows, macOS and Linux.

Musicpy now also supports reading and writing musicxml files, note that you need to install partitura to use the functionality by `pip install partitura`.

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

Summary
-------------
I started to develop musicpy in October 2019, currently musicpy has a complete set of music theory logic syntax, and there are many composing and arranging functions as well as advanced music theory logic operations. For details, please refer to the wiki. I will continue to update musicpy's video tutorials and wiki.

I'm working on musicpy continuously and updating musicpy very frequently, more and more musical features will be added, so that musicpy can do more with music.

Thank you for your support~

If you are interested in the latest progress and develop thoughts of musicpy, you could take a look at this repository [musicpy_dev](https://github.com/Rainbow-Dreamer/musicpy_dev)

Contact
-------------
Discord: Rainbow Dreamer#7122  

qq: 2180502841  

Bilibili account: Rainbow_Dreamer  

email: 2180502841@qq.com / q1036889495@gmail.com

Discussion group:

[![Join our Discord server!](https://invidget.switchblade.xyz/m4xEzPQ76V)](http://discord.gg/m4xEzPQ76V)

QQ discussion group: 364834221

## Donation

This project is developed by Rainbow Dreamer on his spare time to create an interesting music composition library and a high-level MIDI toolkit. If you feel this project is useful to you and want to support it and it's future development, please consider buy me a coffee, I appreciate any amount.

[![Support via PayPal](https://cdn.rawgit.com/twolfson/paypal-github-button/1.0.0/dist/button.svg)](https://www.paypal.com/donate/?business=7XSUZCQNT4M4Y&no_recurring=0&currency_code=CAD)

Reasons Why I Develop This Language and Keep Working on This Project
-------------

There are two main reasons why I develop this language. Firstly, compared with project files and MIDI files that simply store unitary information such as notes, intensity, tempo, etc., it would be more meaningful to represent how a piece of music is realized from a compositional point of view, in terms of music theory. Most music is extremely regular in music theory, as long as it is not modernist atonal music, and these rules can be greatly simplified by abstracting them into logical statements of music theory. (A MIDI file with 1000 notes, for example, can actually be reduced to a few lines of code from a music theory perspective.) Secondly, the language was developed so that the composing AI could compose with a real understanding of music theory (instead of deep learning and feeding a lot of data), and the language is also an interface that allows the AI to compose with a human-like mind once it understands the syntax of music theory. We can tell AI the rules on music theory, what is good to do and what is not, and these things can still be quantified, so this music theory library can also be used as a music theory interface to communicate music between people and AI. So, for example, if you want AI to learn someone's composing style, you can also quantify that person's style in music theory, and each style corresponds to some different music theory logic rules, which can be written to AI, and after this library, AI can realize imitating that person's style. If it is the AI's own original style, then it is looking for possibilities from various complex composition rules.

I am thinking that without deep learning, neural network, teaching AI music theory and someone's stylized music theory rules, AI may be able to do better than deep learning and big data training. That's why I want to use this library to teach AI human music theory, so that AI can understand music theory in a real sense, so that composing music won't be hard and random. That's why one of my original reasons for writing this library was to avoid the deep learning. But I feel that it is really difficult to abstract the rules of music theory of different musicians, I will cheer up to write this algorithm qwq In addition, in fact, the musician himself can tell the AI how he likes to write his own music theory (that is, his own unique rules of music theory preference), then the AI will imitate it very well, because the AI does know music theory at that time, composition is not likely to have a sense of machine and random. At this point, what the AI is thinking in its head is exactly the same as what the musician is thinking in his head.

The AI does not have to follow the logical rules of music theory that we give it, but we can set a concept of "preference" for the AI. The AI will have a certain degree of preference for a certain style, but in addition, it will have its own unique style found in the rules of "correct music theory", so that the AI can say that it "has been influenced by some musicians to compose its own original style". When this preference is 0, the AI's composition will be exactly the style it found through music theory, just like a person who learns music theory by himself and starts to figure out his own composition style. An AI that knows music theory can easily find its own unique style to compose, and we don't even need to give it data to train, but just teach it music theory.

So how do we teach music theory to an AI? In music, ignoring the category of modernist music for the moment, most music follows some very basic rules of music theory. The rules here refer to how to write music theory OK and how to write music theory mistakes. For example, when writing harmonies, four-part homophony is often to be avoided, especially when writing orchestral parts in arrangements. For example, when writing a chord, if the note inside the chord has a minor second (or minor ninth) it will sound more fighting. For example, when the AI decides to write a piece starting from A major, it should pick chords from the A major scale in steps, possibly off-key, add a few subordinate chords, and after writing the main song part, it may modulate by circle of fifths, or major/minor thirds, modulate in the parallel major and minor keys, etc. What we need to do is to tell the AI how to write the music correctly, and furthermore, how to write it in a way that sounds good, and that the AI will learn music theory well, will not forget it, and will be less likely to make mistakes, so they can write music that is truly their own. They will really know what music is and what music theory is. Because what the language of this library does is to abstract the music theory into logical statements, then every time we give "lessons" to the AI, we are expressing the person's own music theory concepts in the language of this library, and then writing them into the AI's database. In this way, the AI really learns the music theory. Composing AI in this way does not need deep learning, training set, or big data, compared to composing AI trained by deep learning, which actually does not know what music theory is and has no concept of music, but just draws from the huge amount of training data. Another point is that since things can be described by concrete logic, there is no need for machine learning. If it is text recognition, image classification, which is more difficult to use abstract logic to describe things, that is the place where deep learning is useful.

