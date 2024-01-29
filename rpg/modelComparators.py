def compareEntry(x, y):
    return compareOrder(x.order, y.order)

def compareOrder(x, y):
    xSplit = [int(n) for n in x.split('.')]
    ySplit = [int(n) for n in y.split('.')]
    size = min(len(xSplit), len(ySplit))
    # look at common part
    for ind in range(0, size):
        if xSplit[ind] > ySplit[ind]:
            return 1
        elif ySplit[ind] > xSplit[ind]:
            return -1
    # look at lenth
    if len(xSplit) > len(ySplit):
        return 1
    elif len(ySplit) > len(xSplit):
        return -1
    else:
        return 0