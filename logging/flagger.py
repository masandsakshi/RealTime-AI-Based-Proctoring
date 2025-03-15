threshold = 3

maxTime = 3000
focus_sus = 3
key_sus = 2
flag = False
def focus_check(t):
    global focus_sus
    if t >= maxTime:
        focus_sus += 1


def global_check():
    global flag
    flag = focus_sus >= threshold or key_sus >= threshold

def check_log():
    global flag
    with open('./activity.log','r') as f:
        lines = f.readlines()
        print(lines)
        for i in lines:
            data = i.split()
            if data[0] == 'focus':
                focus_check(float(data[1]))
            else:
                pass
            global_check()
            if flag:
                break
    return flag

flagged = check_log()
print("Flagged?",flagged)