# Guess What I'm Thinking

# Answers can be submitted in two places: the normal puzzle answer submission,
# and the form on the response page. Responses for both appear on the response
# page.
# response is a function that takes an answer and returns the appropriate
# response text. Use response(answer) for answer submission box and 
# response(answer, False) for response page guesses.
# If using the answer submission box, an incorrect-length submission will return
# None, and should be treated as a normal answer attempt.



import string, re, math

# puzzle main page URL
MAIN = "."

# correct answers
CORRECT = {20: 'WORDOFTENWITHNEITHER',
           21: 'DIRECTIONOPPOSITEWEST',
           22: 'CLOONEYHOSPITALNBCSHOW',
           23: 'JETSTARPACIFICSIATACODE',
           24: 'COMEDIANEDDIEOFTHERICHES'}

SOLVED = {20: False,
          21: False,
          22: False,
          23: False,
          24: False}
          


def response(answer, form=True):
    """
    Returns appropriate formatted response for a given answer string.
    If wrong length and form is True, returns None.
    """
    guess = alphanumeric(answer)
    
        
#    guess = alphabetize(answer)
    length = len(guess)
    if 20 <= length <= 24:
        if re.compile("[0-9]").search(guess):
            return formatresponse(guess, "<font color=darkred>Sorry, there was a problem.</font> You entered something that's the right length, but it contained at least one digit. Please try again with letters only and no digits.", False)
        else:
            return formatresponse(guess, processresponse(length, guess), False)
    else:
        if form:
            return None
        else:
            return formatresponse(guess, "<font color=darkred>Sorry, you entered something that's the wrong length.</font> If you were trying to submit a final answer for this puzzle, please do so <a href=\"%s\">here</a>." % MAIN, True)
    
def processresponse(length, ans):
    """
    Return response for answer of given length.
    """
    cor = CORRECT[length]
    if ans == cor:
        return "<font color=darkgreen>Nice! You correctly guessed one of the things I'm thinking of!</font>"

    response = "<font color=darkred>Sorry, that was not quite right.</font>\n"

    if length == 20:
        ret = monofmt(mastermind(ans, cor))
        response += "This is what your guess brings to mind:<br/><br/>%s<br/><br/>Keep it up and you'll get it!" % ret
    elif length == 21:
        response += morse(ans, cor)
    elif length == 22:
        ret = monofmt(alphabet(ans, cor))
        response += "Here's what I have to say about your guess:<br/><br/>%s<br/><br/>Hang in there!" % ret
    elif length == 23:
        dist = responsefmt(euclidean(ans, cor))
        response += "Your guess is a distance of <br/><br/>%s<br/><br/> away from what I'm thinking of. Keep trying!" % dist
    elif length == 24:
        response += pigpen(ans, cor)
    else:
        return "ERROR: Incorrect length."
    return response

def formatresponse(guess, res, allfive):
    """
    Formats entire response text.
    """
    fmtans = monofmt(guess)
#    if allfive:
    blanktext = "I am thinking of these five things:"
#    else:
#        blanktext = "By the way, I'm also thinking of these four things:"

    length = len(guess)
    blanks = ""
    for i in range(20, 25):
#        if i != length:
        blanks += processblanks(i) + "<br/>\n"

    return "<p>You tried to guess what I'm thinking! This is what you guessed:<br/><br/>%s</p>\n<p>%s</p>\n<p><i>%s</i><br/>%s</p><br/>\n" % (fmtans, res, blanktext, blanks)

def processblanks(n):
    """
    Produces blanks.
    """
    if SOLVED[n]:
        ret = "<b>" + ' '.join(list(CORRECT[n])) + "</b>"
    else:
        ret = '_ '*n
    return "<tt>%s</tt>" % ret


def responsefmt(text):
    """
    Formats big.
    """
    return "<big><b>%s</b></big>" % text

def monofmt(text):
    """
    Formats big in monospace.
    """
    return "<big><b><tt>%s</tt></b></big>" % text


def alphanumeric(text):
    """
    Strips non-alphanumeric characters from text and converts to uppercase.
    """
    pattern = re.compile('[^A-Za-z0-9]')
    return re.sub(pattern, '', text).upper()

def mastermind(ans, cor):
    """
    Handles Mastermind response.
    """
    length = len(ans)
    black = 0
    white = 0

    abank = [0]*26
    cbank = [0]*26
    for i in range(length):
        abank[ord(ans[i])-ord('A')] += 1
        cbank[ord(cor[i])-ord('A')] += 1
        if ans[i] == cor[i]:
            black += 1

    for j in range(26):
        white += min(abank[j], cbank[j])
    
    white -= black

    bsquares = "&#9679; "*black
    wsquares = "&#9675; "*white
    return bsquares+wsquares
    
def morse(ans, cor):
    """
    Handles Morse response.
    """
    length = len(ans)
    morsemap = ['01', '1000', '1010', '100', '0', '0010', '110', '0000', '00', '0111', '101', '0100', '11', '10', '111', '0110', '1101', '010', '000', '1', '001', '0001', '011', '1001', '1011', '1100']
    
    morsecor = ""
    morseans = ""
    for i in range(length):
        morsecor += morsemap[ord(cor[i])-ord('A')]
        morseans += morsemap[ord(ans[i])-ord('A')]
        
    if morsecor == morseans:
        let = None
        for i in range(length):
            if cor[i] != ans[i]:
                let = ans[i]
                break
        res = monofmt(let)
        return "Oh, so close! You have the right sequence, but your letters are off. The first error in your guess is<br/><br/>" + res
    elif len(morsecor) == len(morseans):
        dcor = int(morsecor, 2)
        dans = int(morseans, 2)
        ddiff = dans - dcor
        if ddiff > 0:
            direction = "bigger"
        else:
            direction = "smaller"
        bdiff = bin(abs(ddiff))[2:]
        res = responsefmt(re.sub('0', '&middot; ', re.sub('1', '&ndash; ', bdiff)))
        return "You're getting warmer! Your guess is the right length, but its value is <br/><br/>%s<br/><br/>%s than what I'm thinking." % (res, direction)
    else:
        diff = len(morseans)-len(morsecor)
        if diff > 0:
            direction = "longer"
        else:
            direction = "shorter"

        fmtdif = responsefmt(abs(diff))
        return "The guess you tapped out was <br/><br/>%s<br/><br/> %s than what I'm thinking. Give it another shot." % (fmtdif, direction)
	
def alphabet(ans, cor):
    """
    Handles alphabet position response.
    """
    length = len(ans)
    ret = ""
    for i in range(length):
        diff = cmp(ans[i], cor[i])
        if diff > 0:
            ret += "<font color=#0000c0>&#9632;</font>"
        elif diff < 0:
            ret += "<font color=#c00000>&#9650;</font>"
        else:
            ret += "<font color=#00c000>&#9679;</font>"
    return ret

def euclidean(ans, cor):
    """
    Handles Euclidean distance response.
    """
    length = len(ans)
    sqdist = 0
    for i in range(length):
        diff = ord(ans[i])-ord(cor[i])
        sqdist += diff*diff
    return "%0.12f" % math.sqrt(sqdist)

def pigpen(ans, cor):
    """
    Handles pigpen difference response.
    """
    length = len(ans)
    pigpenmap = ['0A0B00000', '0ABB00000', '0AB000000', 'AA0B00000', 'AABB00000', 'AAB000000', 'A00B00000', 'A0BB00000', 'A0B000000', '0A0B0000E', '0ABB0000E', '0AB00000E', 'AA0B0000E', 'AABB0000E', 'AAB00000E', 'A00B0000E', 'A0BB0000E', 'A0B00000E', '00000C0D0', '00000CD00', '0000C00D0', '0000C0D00', '00000C0DE', '00000CD0E', '0000C00DE', '0000C0D0E']

    ppcor = ""
    ppans = ""
    for i in range(length):
        ppcor += pigpenmap[ord(cor[i])-ord('A')]
        ppans += pigpenmap[ord(ans[i])-ord('A')]
    extra = ""
    missing = ""
    pplen = len(ppcor)
    for i in range(pplen):
        comp = cmp(ppans[i], ppcor[i])
        if comp > 0:
            extra += ppans[i]
        elif comp < 0:
            missing += ppcor[i]
    
    fmtex = responsefmt(pigpentransform(extra))
    fmtmi = responsefmt(pigpentransform(missing))

    ret = ""
    if len(extra) == 0:
        ret += "Your guess is missing the following strokes that are in what I'm thinking of:<br/><br/>" + fmtmi
    elif len(missing) == 0:
        ret += "Your guess has the following extra strokes that aren't in what I'm thinking of:<br/><br/>" + fmtex
    else:
        ret += "Your guess has the following extra strokes that aren't in what I'm thinking of:<br/><br/><small>%s</small><br/><br/>It's also missing the following strokes that <i>are</i> in what I'm thinking of:<br/><br/><small>%s</small>" % (fmtex, fmtmi)
    return ret + "<br/><br/>Please keep guessing!"

def pigpentransform(text):
    """
    Maps pigpen responses into displayed characters.
    """
    ret = text
    ret = re.sub("A", "&#8213; ", ret)
    ret = re.sub("B", "| ", ret)
    ret = re.sub("C", "/ ", ret)
    ret = re.sub("D", "\\ ", ret)
    ret = re.sub("E", "&#8226; ", ret)
    return ret

