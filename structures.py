from copy import deepcopy as copy
from match import match
from database import *


class note:
    def __init__(self, name, num, duration=1, volume=100):
        self.name = name
        self.num = num
        self.degree = standard[name] + 12 * num
        self.duration = duration
        self.volume = volume

    def __str__(self):
        return f'{self.name}{self.num}'

    __repr__ = __str__

    def __eq__(self, other):
        return self.name == other.name and self.num == other.num

    def __matmul__(self, other):
        return self.name == other.name

    def setvolume(self, vol):
        self.volume = vol

    def set(self, duration=1, volume=100):
        return note(self.name, self.num, duration, volume)

    def join(self, other, ind, interval):
        if type(other) == str:
            other = toNote(other)
        if type(other) == note:
            return chord([copy(self), copy(other)], interval=interval)
        if type(other) == chord:
            temp = copy(other)
            temp.insert(ind, copy(self))
            temp.interval.insert(ind - 1, interval)
            return temp

    def up(self, unit=1, duration=None, volume=None):
        if duration is None:
            duration = self.duration
        if volume is None:
            volume = self.volume
        return degree_to_note(self.degree + unit, duration, volume)

    def down(self, unit=1, duration=None, volume=None):
        if duration is None:
            duration = self.duration
        if volume is None:
            volume = self.volume
        return degree_to_note(self.degree - unit, duration, volume)


def toNote(notename, duration=1, volume=100):
    num = eval(''.join([x for x in notename if x.isdigit()]))
    name = ''.join([x for x in notename if not x.isdigit()])
    return note(name, num, duration, volume)


def degree_to_note(degree, duration=1, volume=100):
    name = standard_reverse[degree % 12]
    num = degree // 12
    return note(name, num, duration, volume)


class chord:
    ''' This class can contain a chord with many notes played simultaneously and either has intervals, the default interval is 0.'''
    def __init__(self, notes, duration=None, interval=None, rootpitch=5):
        try:
            notes = [x if isinstance(x, note) else toNote(x) for x in notes]
        except:
            if rootpitch is None:
                raise ValueError(
                    'must provide a pitch of root note when use nopitch mode')
            root = note(notes[0], rootpitch)
            notels = [root]
            for i in range(1, len(notes)):
                last = notels[i - 1]
                current = note(notes[i], last.num)
                if standard[current.name] <= standard[last.name]:
                    current = note(current.name, last.num + 1)
                notels.append(current)
            notes = notels
        self.notes = notes
        # interval between each two notes one-by-one
        self.interval = [0 for i in range(len(notes))]
        if interval is not None:
            self.changeInterval(interval)
        if duration is not None:
            if isinstance(duration, int) or isinstance(duration, float):
                for t in self.notes:
                    t.duration = duration
            else:
                for k in range(len(duration)):
                    self.notes[k].duration = duration[k]

    def names(self):
        return [i.name for i in self]

    def addnote(self, newnote):
        if isinstance(newnote, note):
            self.notes.append(newnote)
            self.interval.append(self.interval[-1])
        else:
            self.notes.append(toNote(newnote))
            self.interval.append(self.interval[-1])

    def split(self):
        return self.notes

    def pick(self, alist):
        temp = self.copy()
        temp.notes = [temp.notes[i - 1] for i in alist]
        temp.interval = [temp.interval[x - 1] for x in alist]
        return temp

    def __mod__(self, alist):
        return self.pick(alist)

    def standardize(self):
        temp = self.copy()
        notenames = temp.names()
        intervals = temp.interval
        names_offrep = []
        new_interval = []
        for i in range(len(notenames)):
            current = notenames[i]
            if current not in names_offrep:
                names_offrep.append(current)
                new_interval.append(intervals[i])
        temp.notes = chord(names_offrep, rootpitch=temp[1].num).notes
        temp.interval = new_interval
        return temp

    def sortchord(self):
        temp = self.copy()
        temp.notes.sort(key=lambda x: x.degree)
        return temp

    def set(self, duration=None, interval=None):
        return chord(copy(self.notes), duration, interval)

    def changeInterval(self, newinterval):
        if isinstance(newinterval, int) or isinstance(newinterval, float):
            self.interval = [newinterval for i in range(len(self.notes))]
        else:
            if len(newinterval) == len(self.interval):
                self.interval = newinterval
            else:
                print(
                    'please ensure the intervals between notes has the same numbers of the notes'
                )

    def __str__(self):
        return f'{self.notes} with interval {self.interval}'

    __repr__ = __str__

    def __contains__(self, note1):
        if not isinstance(note1, note):
            note1 = toNote(note1)
        return note1 in self.notes

    def __add__(self, obj):
        temp = copy(self)
        if isinstance(obj, note):
            temp.notes.append(copy(obj))
            temp.interval.append(temp.interval[-1])
        elif isinstance(obj, str):
            return temp.__add__(toNote(obj))
        elif isinstance(obj, chord):
            obj = copy(obj)
            temp.notes += obj.notes
            temp.interval += obj.interval
        return temp

    def pop(self, ind=None):
        if ind is None:
            result = self.notes.pop()
            self.interval.pop()
        else:
            if ind > 0:
                ind -= 1
            result = self.notes.pop(ind)
            self.interval.pop(ind)
        return result

    def __sub__(self, obj):
        if not isinstance(obj, note):
            obj = toNote(obj)
        temp = copy(self)
        if obj in temp:
            ind = temp.notes.index(obj)
            del temp.notes[ind]
            del temp.interval[ind]
        return temp

    def __mul__(self, num):
        temp = copy(self)
        unit = copy(temp)
        for i in range(num - 1):
            temp += unit
        return temp

    def reverse(self, end=None, start=0, cut=False):
        temp = copy(self)
        if end is None:
            temp.notes = temp.notes[::-1]
            temp.interval = temp.interval[::-1]
        else:
            if cut:
                temp.notes = temp.notes[start:end][::-1]
                temp.interval = temp.interval[start:end][::-1]
            else:
                temp.notes = temp.notes[:start] + temp.notes[
                    start:end][::-1] + temp.notes[end:]
                temp.interval = temp.interval[:start] + temp.interval[
                    start:end][::-1] + temp.interval[end:]
        return temp

    def intervalof(self, cummulative=True, translate=False):
        if not cummulative:
            result = [
                self[i].degree - self[i - 1].degree
                for i in range(2,
                               len(self) + 1)
            ]
        else:
            root = self[1].degree
            result = [i.degree - root for i in self[2:]]
        if not translate:
            return result
        return [INTERVAL[x][0] for x in result]

    def add(self, note1=None, interval=None, mode='tail', start=0, duration=1):
        temp = copy(self)
        if type(note1) == int:
            temp += temp[1].up(note1)
            return temp
        if mode == 'tail':
            if interval is not None:
                return temp + degree_to_note(temp.notes[0].degree + interval)
            else:
                return temp + note1
        elif mode == 'head':
            note1 = copy(note1)
            if isinstance(note1, chord):
                inter = note1.interval
            else:
                if isinstance(note1, str):
                    note1 = chord([toNote(note1, duration=duration)])
                elif isinstance(note1, note):
                    note1 = chord([note1])
                if isinstance(interval, int):
                    inter = [interval for i in range(len(note1))]
                else:
                    inter = interval
            # calculate the absolute distances of all of the notes of the chord to add and self,
            # and then sort them, make differences between each two distances
            distance = []
            if start != 0:
                note1.notes.insert(0, temp.notes[0])
                note1.interval.insert(0, start)
            for i in range(len(temp.notes)):
                dis = sum(temp.interval[:i])
                distance.append((dis, temp.notes[i]))
            for j in range(len(note1.notes)):
                dis = sum(inter[:j])
                distance.append((dis, note1.notes[j]))
            distance = sorted(distance, key=lambda x: x[0])
            newinterval = [
                distance[x][0] - distance[x - 1][0]
                for x in range(1, len(distance))
            ] + [distance[-1][1].duration]
            newnotes = [distance[x][1] for x in range(len(distance))]
            return chord(newnotes, interval=newinterval)
        elif mode == 'after':
            times = max(max([x.duration for x in self.notes]),
                        max(self.interval))
            return self.period(times) + note1

    def inversion(self, num=1):
        # chord's zhuan3 wei4 return chord's [first, second, ... (num)] inversion chord
        if num not in range(1, len(self.notes)):
            print(
                'the number of inversion is out of range of the notes in this chord'
            )
        else:
            temp = copy(self)
            notes = temp.notes
            temp2 = [notes[i] for i in range(len(notes)) if i != num]
            root = notes[num]
            while root.degree >= temp2[0].degree:
                root = note(root.name, root.num - 1, root.duration,
                            root.volume)
            return chord([root] + temp2, interval=temp.interval)

    def sort(self, indlist, rootpitch=None):
        names = [self[i].name for i in indlist]
        if rootpitch is None:
            rootpitch = self[indlist[0]].num
        elif rootpitch == 'same':
            rootpitch = self[1].num
        return chord(names, rootpitch=rootpitch)

    def voicing(self, rootpitch=None):
        if rootpitch is None:
            rootpitch = self[1].num
        duration, interval = [i.duration for i in self.notes], self.interval
        notenames = self.names()
        return [
            chord(x, rootpitch=rootpitch).set(duration, interval)
            for x in perm(notenames)
        ]

    def inversion_highest(self, ind):
        if ind in range(1, len(self)):
            temp = self.copy()
            while temp[ind].degree < temp[-1].degree:
                temp[ind] = temp[ind].up(octave)
            temp.notes.append(temp.notes.pop(ind - 1))
            return temp

    def inoctave(self):
        temp = self.copy()
        root = self[1].degree
        for i in range(2, len(temp) + 1):
            while temp[i].degree - root > octave:
                temp[i] = temp[i].down(octave)
        temp.notes.sort(key=lambda x: x.degree)
        return temp

    def on(self, root, duration=1, interval=None, each=0):
        temp = copy(self)
        if each == 0:
            if not isinstance(root, note):
                root = toNote(root)
                root.duration = duration
            temp.notes.insert(0, root)
            if interval is not None:
                temp.interval.insert(0, interval)
            else:
                temp.interval.insert(0, self.interval[0])
            return temp
        else:
            if type(root) == chord:
                root = list(root)
            else:
                root = [toNote(i) for i in root]
            return [self.on(x, duration, interval) for x in root]

    def up(self, unit=1, ind=None, ind2=None):
        temp = copy(self)
        if type(ind) != int and ind is not None:
            temp.notes = [
                temp.notes[i - 1].up(unit) if i in ind else temp.notes[i - 1]
                for i in range(1,
                               len(temp.notes) + 1)
            ]
            return temp
        if ind2 is None:
            if ind is None:
                temp.notes = [
                    degree_to_note(temp[i].degree + unit, temp[i].duration,
                                   temp[i].volume)
                    for i in range(1,
                                   len(temp) + 1)
                ]
            else:
                temp[ind] = degree_to_note(temp[ind].degree + unit,
                                           temp[ind].duration,
                                           temp[ind].volume)
        else:
            temp.notes = [
                degree_to_note(temp[i].degree + unit, temp[i].duration,
                               temp[i].volume) if ind <= i < ind2 else temp[i]
                for i in range(1,
                               len(temp) + 1)
            ]
        return temp

    def down(self, unit=1, ind=None, ind2=None):
        return self.up(-unit, ind, ind2)

    def drop(self, ind, mode=0):
        # if mode is 0, then drop notes by index,
        # if mode is 1, then drop notes by the names of notes,
        # if mode is 2, then drop notes by only name (ignoring pitch)

        if mode == 0:
            if type(ind) == list:
                return self.drop([self[i] for i in ind], mode=1)
            else:
                return self.drop(self[ind], mode=1)
        elif mode == 1:
            temp = copy(self)
            if type(ind) == list:
                ind = [toNote(x) if type(x) != note else x for x in ind]
                for each in ind:
                    if each in temp.notes:
                        current = temp.notes.index(each)
                        del temp.notes[current]
                        del temp.interval[current]
            else:
                if type(ind) != note:
                    ind = toNote(ind)
                if ind in temp.notes:
                    current = temp.notes.index(ind)
                    del temp.notes[current]
                    del temp.interval[current]
        elif mode == 2:
            temp = copy(self)
            if type(ind) == list:
                for each in ind:
                    self_notenames = temp.names()
                    if each in self_notenames:
                        current = self_notenames.index(each)
                        del temp.notes[current]
                        del temp.interval[current]
            else:
                self_notenames = temp.names()
                if ind in self_notenames:
                    current = self_notenames.index(ind)
                    del temp.notes[current]
                    del temp.interval[current]
        return temp

    omit = drop

    def copy(self):
        return copy(self)

    def __setitem__(self, ind, value):
        if type(value) == str:
            value = toNote(value)
        self.notes[ind - 1] = value

    def __delitem__(self, ind):
        del self.notes[ind - 1]

    def index(self, value):
        if type(value) == str:
            value = toNote(value)
        if value not in self:
            return -1
        return self.notes.index(value) + 1

    def remove(self, note1):
        if type(note1) == str:
            note1 = toNote(note1)
        if note1 in self:
            self.notes.remove(note1)

    def append(self, value, interval=None):
        if type(value) == str:
            value = toNote(value)
        self.notes.append(value)
        if interval is None:
            interval = self.interval[-1]
        self.interval.append(interval)

    def delete(self, ind):
        del self[ind]

    def insert(self, ind, value, interval=None):
        if type(value) == str:
            value = toNote(value)
        self.notes.insert(ind - 1, value)
        if interval is None:
            interval = self.interval[-1]
        self.interval.insert(ind - 1, interval)

    def drops(self, ind):
        temp = self.copy()
        dropnote = temp.notes.pop(-ind).down(octave)
        dropinterval = temp.interval.pop(-ind)
        temp.notes.insert(0, dropnote)
        temp.interval.insert(0, dropinterval)
        return temp

    def period(self, length, ind=-1):
        temp = copy(self)
        temp.interval[ind] += length
        return temp

    def modulation(self, old_scale, new_scale):
        # change notes (including both of melody and chords) in the given piece
        # of music from a given scale to another given scale, and return
        # the new changing piece of music.
        temp = copy(self)
        number = len(new_scale.getScale())
        transdict = {
            old_scale[i].name: new_scale[i].name
            for i in range(1, number + 1)
        }
        for k in range(len(temp)):
            if temp[k + 1].name in transdict:
                current = temp.notes[k]
                temp.notes[k] = toNote(
                    f'{transdict[current.name]}{current.num}',
                    current.duration, current.volume)
        return temp

    def __getitem__(self, ind):
        if isinstance(ind, slice):
            start = ind.start if ind.start is None else (
                ind.start - 1 if ind.start > 0 else len(self) + ind.start)
            stop = ind.stop if ind.stop is None else (
                ind.stop - 1 if ind.stop > 0 else len(self) + ind.stop)
            return self.__getslice__(start, stop)
        temp = copy(self)
        if ind != 0:
            if ind > 0:
                ind -= 1
            return temp.notes[ind]

    def __iter__(self):
        for i in self.notes:
            yield i

    def __getslice__(self, i, j):
        temp = copy(self)
        return chord(temp.notes[i:j], interval=temp.interval[i:j])

    def __len__(self):
        return len(self.notes)

    def setvolume(self, ind, vol):
        self.notes[ind - 1].setvolume(vol)

    def move(self, x):
        # x could be a dict or list of (index, move_steps)
        temp = self.copy()
        if type(x) == dict:
            for i in x:
                temp.notes[i - 1] = temp.notes[i - 1].up(x[i])
            return temp
        if type(x) == list:
            for i in x:
                temp.notes[i[0] - 1] = temp.notes[i[0] - 1].up(i[1])
            return temp

    def extend(self,
               distance,
               duration=None,
               intervals=None,
               volume=None,
               modes='tail'):
        # extend a chord with notes has one or multiple given distances
        # with the first note in the chord
        temp = copy(self)
        if duration is None:
            duration = temp[-1].duration
        if intervals is None:
            intervals = temp.interval[-1]
        if volume is None:
            volume = temp[-1].volume
        if isinstance(distance, int):
            temp = temp.add(degree_to_note(temp[1].degree + distance, duration,
                                           volume),
                            mode=modes)
            temp.interval[-1] = intervals
        else:
            if not isinstance(duration, list):
                duration = [duration for x in range(len(distance))]
            if not isinstance(intervals, list):
                intervals = [intervals for y in range(len(distance))]
            if not isinstance(volume, list):
                volume = [volume for y in range(len(distance))]
            for k in range(len(distance)):
                temp = temp.add(degree_to_note(temp[1].degree + distance[k],
                                               duration[k], volume[k]),
                                mode=modes)
                temp.interval[-1] = intervals[k]
        return temp


class scale:
    def __init__(self,
                 start=None,
                 mode=None,
                 interval=None,
                 name=None,
                 notels=None,
                 pitch=5):
        self.interval = interval
        if notels is not None:
            notels = [toNote(i) if type(i) != note else i for i in notels]
            self.notes = notels
            self.start = notels[0]
            self.mode = mode
        else:
            if not isinstance(start, note):
                try:
                    start = toNote(start)
                except:
                    start = note(start, pitch)
            self.start = start
            self.pitch = self.start.num
            if mode is not None:
                self.mode = mode.lower()
            else:
                self.mode = name
            self.notes = self.getScale().notes

        if interval is None:
            self.interval = self.getInterval()

    def set_mode_name(self, name):
        self.mode = name

    def change_interval(self, interval):
        self.interval = interval

    def __str__(self):
        return f'scale name: {self.start} {self.mode} scale\nscale intervals: {self.getInterval()}\nscale notes: {self.getScale().notes}'

    __repr__ = __str__

    def __contains__(self, note1):
        return note1 in self.getScale()

    def __getitem__(self, ind):
        if isinstance(ind, slice):
            return self.getScale()[ind]
        if ind != 0:
            if ind > 0:
                ind -= 1
            return self.notes[ind]

    def __iter__(self):
        for i in self.notes:
            yield i

    def __call__(self, n, num=3, interval=0, step=2, add=None, omit=None):
        return self.pickchord_by_degree(n, interval, num, step, add, omit)

    def getInterval(self):
        if self.mode is None:
            if self.interval is None:
                if self.notes is None:
                    print('a mode or interval or notes list should be settled')
                else:
                    notes = self.notes
                    rootdegree = notes[0].degree
                    return [
                        notes[i].degree - notes[i - 1].degree
                        for i in range(1, len(notes))
                    ]
            else:
                return self.interval
        else:
            if self.interval is not None:
                return self.interval
            mode = self.mode.lower()
            result = scaleTypes[mode]
            if result != 'not found':
                return result
            else:
                return 'could not find this scale'

    def getScale(self, intervals=1, durations=None):
        if self.mode == None:
            if self.interval == None:
                print(
                    'at least one of mode or interval in the scale should be settled'
                )
            else:
                result = [self.start]
                count = self.start.degree
                for t in self.interval:
                    count += t
                    result.append(degree_to_note(count))
                return chord(result, duration=durations, interval=intervals)
        else:
            result = [self.start]
            count = self.start.degree
            interval1 = self.getInterval()
            if type(interval1) == str:
                raise ValueError('cannot find this scale')
            for t in interval1:
                count += t
                result.append(degree_to_note(count))
            return chord(result, duration=durations, interval=intervals)

    def __len__(self):
        return len(self.notes)

    def names(self):
        temp = [x.name for x in self.notes]
        result = []
        for i in temp:
            if i not in result:
                result.append(i)
        return result

    def pickchord_by_degree(self,
                            degree1,
                            interval=0,
                            num=3,
                            step=2,
                            add=None,
                            omit=None,
                            duration=None):
        result = []
        high = False
        if degree1 == 8:
            degree1 = 1
            high = True
        scale_notes = self.notes[:-1]
        for i in range(degree1, degree1 + step * num, step):
            result.append(scale_notes[(i % 7) - 1])
        resultchord = chord(result,
                            rootpitch=self.pitch,
                            interval=interval,
                            duration=duration).standardize()
        if high:
            resultchord = resultchord.up(octave)
        if add is not None:
            resultchord += self[add]
        if omit is not None:
            resultchord -= self[omit]
        return resultchord

    def pickdegree(self, degree1):
        return self[degree1]

    def pattern(self, indlist, interval=0, duration=1, num=3, step=2):
        if type(indlist) == str:
            indlist = [int(i) for i in indlist]
        if type(indlist) == int:
            indlist = [int(i) for i in str(indlist)]
        return [
            self(n, num, step=step).set(duration, interval) for n in indlist
        ]

    def __mod__(self, x):
        if type(x) in [int, str]:
            x = [x]
        return self.pattern(*x)

    def dom(self):
        return self[5]

    def dom_mode(self):
        if self.mode is not None:
            return scale(self[5], mode=self.mode)
        else:
            return scale(self[5], interval=self.getInterval())

    def fifth(self, step=1, inner=False):
        # move the scale on the circle of fifths by number of steps,
        # if the step is > 0, then move clockwise,
        # if the step is < 0, then move counterclockwise,
        # if inner is True: pick the inner scales from the circle of fifths,
        # i.e. those minor scales.
        return circle_of_fifths().rotate_getScale(self[1].name,
                                                  step,
                                                  pitch=self[1].num,
                                                  inner=inner)

    def fourth(self, step=1, inner=False):
        # same as fifth but instead of circle of fourths
        # Maybe someone would notice that circle of fourths is just
        # the reverse of circle of fifths.
        return circle_of_fourths().rotate_getScale(self[1].name,
                                                   step,
                                                   pitch=self[1].num,
                                                   inner=inner)

    def tonic_chord(self):
        return self(1)

    def subdom(self):
        return self[4]

    def subdom_chord(self):
        return self(4)

    def dom_chord(self):
        return self(5)

    def dom7_chord(self):
        return self(5) + self[4].up(12)

    def leading7_chord(self):
        return chord([self[7].down(octave), self[2], self[4], self[6]])

    def scalefrom(self, degree=5, mode=None, interval=None):
        # default is pick the dominant mode of the scale
        if mode is None and interval is None:
            mode, interval = self.mode, self.interval
        return scale(self[degree], mode, interval)

    def secondary_dom(self, degree=5):
        newscale = self.scalefrom(degree, self.mode, self.interval)
        return newscale.dom_chord()

    def secondary_dom7(self, degree=5):
        return self.scalefrom(degree, self.mode, self.interval).dom7_chord()

    def secondary_leading7(self, degree=5):
        return self.scalefrom(degree, self.mode,
                              self.interval).leading7_chord()

    def pickchord_by_index(self, indlist):
        return chord([self[i] for i in indlist])

    def __matmul__(self, indlist):
        return self.pickchord_by_index(indlist)

    def get_allchord(self, interval=0, num=3, step=2):
        return [
            self.pickchord_by_degree(i, interval=interval, num=num, step=step)
            for i in range(1,
                           len(self.getInterval()) + 2)
        ]

    def relative_key(self):
        if self.mode == 'major':
            return scale(self[6], 'minor')
        elif self.mode == 'minor':
            return scale(self[3], 'major')
        else:
            'this function only applies to major and minor scales'

    def parallel_key(self):
        if self.mode == 'major':
            return scale(self[1], 'minor')
        elif self.mode == 'minor':
            return scale(self[1], 'major')
        else:
            return 'this function only applies to major and minor scales'

    def get(self, degree):
        return self[degree]

    def up(self, unit=1, ind=None, ind2=None):
        if ind2 is not None:
            notes = copy(self.notes)
            return scale(notels=[
                notes[i - 1].up(unit) if ind <= i < ind2 else notes[i - 1]
                for i in range(1,
                               len(notes) + 1)
            ])
        if ind is None:
            return scale(self[1].up(unit), self.mode, self.interval)
        else:
            notes = copy(self.notes)
            if type(ind) == int:
                notes[ind - 1] = notes[ind - 1].up(unit)
            else:
                notes = [
                    notes[i - 1].up(unit) if i in ind else notes[i - 1]
                    for i in range(1,
                                   len(notes) + 1)
                ]
            return scale(notels=notes)

    def down(self, unit=1, ind=None, ind2=None):
        return self.up(-unit, ind2)

    def move(self, x):
        notes = copy(self.getScale())
        return scale(notels=notes.move(x))

    def inversion(self, ind, parallel=False, start=None):
        # return the inversion of a scale with the beginning note of a given index
        ind -= 1
        interval1 = self.getInterval()
        new_interval = interval1[ind:] + interval1[:ind]
        if parallel:
            start1 = self.start
        else:
            if start is not None:
                start1 = start
            else:
                start1 = self.getScale().notes[ind]
        return scale(start=start1, interval=new_interval)


class circle_of_fifths:
    outer = ['C', 'G', 'D', 'A', 'E', 'B', 'Gb', 'Db', 'Ab', 'Eb', 'Bb', 'F']
    inner = [
        'Am', 'Em', 'Bm', 'F#m', 'C#m', 'G#m', 'Ebm', 'Bbm', 'Fm', 'Cm', 'Gm',
        'Dm'
    ]

    def __init__(self):
        pass

    def __getitem__(self, ind):
        ind -= 1
        if type(ind) == int:
            if not (0 <= ind < 12):
                ind = ind % 12
            return self.outer[ind]
        elif type(ind) == tuple:
            ind = ind[0]
            if not (0 <= ind < 12):
                ind = ind % 12
            return self.inner[ind]

    def draw(self, inner=False):
        if not inner:
            print(
                '\n         C \n    F         G\n   Bb          D\n  Eb            A\n   Ab          E  \n    Db        B\n         Gb'
            )
        else:
            print(
                '\n            C \n        F   Am   G\n     Bb  Dm    Em   D\n        Gm        Bm  \n    Eb Cm        F#m  A\n      Fm        C#m\n   Ab  Bbm   G#m    E  \n      Db   Ebm   B\n           Gb'
            )

    def get(self, ind, mode=0):
        if mode == 0:
            return self[ind]
        else:
            return self[ind, ]

    def rotate(self, start, step=1, direction='cw', inner=False):
        if direction == 'ccw':
            step = -step
        types = type(start)
        if types == note:
            startind = self.outer.index(start.name)
        elif types == str:
            startind = self.outer.index(start)
        else:
            startind = start
        return self[startind + step] if not inner else self[startind + step, ]

    def rotate_getScale(self,
                        start,
                        step=1,
                        direction='cw',
                        pitch=None,
                        inner=False):
        if not inner:
            return scale(note(self.rotate(start, step, direction), pitch),
                         'major')
        else:
            return scale(
                note(self.rotate(start, step, direction, True)[:-1], pitch),
                'minor')

    def getScale(self, ind, pitch, inner=False):
        return scale(note(self[ind], pitch), 'major') if not inner else scale(
            note(self[ind, ][:-1], pitch), 'minor')

    def __repr__(self):
        return f'circle of fifths\nouter circle: {self.outer}\ninner circle: {self.inner}\ndirection: clockwise'


class circle_of_fourths(circle_of_fifths):
    outer = list(reversed(circle_of_fifths.outer))
    outer.insert(0, outer.pop())
    inner = list(reversed(circle_of_fifths.inner))
    inner.insert(0, inner.pop())

    def __init__(self):
        pass

    def __repr__(self):
        return f'circle of fourths\nouter circle: {self.outer}\ninner circle: {self.inner}\ndirection: clockwise'

    def draw(self, inner=False):
        if not inner:
            print(
                '\n         C \n    G         F\n   D          Bb\n  A            Eb\n   E          Ab  \n    B        Db\n        Gb'
            )
        else:
            print(
                '\n            C \n        G   Am   F\n     D   Em    Dm   Bb\n        Bm       Gm  \n    A  F#m        Cm  Eb\n      C#m        Fm\n   E   G#m    Bbm    Ab  \n      B   Ebm   Db\n           Gb'
            )


def perm(n, k=None):
    # this function returns all of the permutations of the elements in x
    if k is None:
        k = len(n)
    if isinstance(n, int):
        n = list(range(1, n + 1))
    if isinstance(n, str):
        n = list(n)
    return eval(
        f'''[{f"[{', '.join([f'n[a{i}]' for i in range(k)])}]"} {''.join([f'for a{i} in range(len(n)) ' if i == 0 else f"for a{i} in range(len(n)) if a{i} not in [{', '.join([f'a{t}' for t in range(i)])}] " for i in range(k)])}]''',
        locals())