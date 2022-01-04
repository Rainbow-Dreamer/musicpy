class match:
    def __init__(self, keys, values=None):
        # keys and values should both be a list/tuple/set of data,
        # and they should have the same counts
        # if the key itself is given as a dict, then just use it
        if isinstance(keys, dict):
            self.dic = keys
        else:
            self.dic = {totuple(keys[i]): values[i] for i in range(len(keys))}

    def __call__(self, *key, mode=0, index=None):
        # unlike __getitem__, this treat key as a whole to match(mode == 0)
        # when mode == 1, the same as __getitem__,
        # and you can set which index to return in the finding results,
        # if the index is set to None (as default), then return whole results.
        if mode == 0:
            try:
                result = self.dic[key]
                if index is None:
                    return result
                return result[index]
            except:
                return 'not found'
        elif mode == 1:
            result = self[key[0]]
            if result == 'not found' or index is None:
                return result
            return result[index]

    def __getitem__(self, key):
        dic = self.dic
        for i in dic:
            if key in i:
                return dic[i]
        return 'not found'

    def __contains__(self, obj):
        return any(obj in i for i in self.dic)

    def search_all(self, key):
        result = []
        dic = self.dic
        for i in dic:
            if key in i:
                result.append(dic[i])
        return result

    def keys(self):
        return self.dic.keys()

    def values(self):
        return self.dic.values()

    def items(self):
        return self.dic.items()

    def __iter__(self):
        return self.dic.__iter__()

    def keynames(self):
        return [x[0] for x in self.dic.keys()]

    def valuenames(self):
        return [x[0] for x in self.dic.values()]

    def reverse(self):
        dic = self.dic
        return match({((tuple(j), ) if not isinstance(j, tuple) else j): i
                      for i, j in dic.items()})

    def __repr__(self):
        return str(self.dic)

    def update(self, key, value=None):
        if isinstance(key, dict):
            self.dic.update(key)
        elif isinstance(key, match):
            self.dic.update(key.dic)
        else:
            if types not in [list, tuple, set]:
                key = (key, )
            self.dic[tuple(key)] = value

    def delete(self, key):
        for i in self.dic:
            if key in i:
                del self.dic[i]
                return


def totuple(x):
    if isinstance(x, str):
        return (x, )
    try:
        return tuple(x)
    except:
        return (x, )
