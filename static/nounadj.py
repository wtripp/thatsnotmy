with open("nouns.txt") as n:
    nouns = [line.rstrip('\n') for line in n]
    
with open("adjectives.txt") as a:
    adjectives = [line.rstrip('\n') for line in a]
    
with open("words.py","w") as words:
    words.write('nouns = ' + str(nouns) + '\n\n')
    words.write('adjectives = ' + str(adjectives))
