from random import randint
from sys import exit

with open("nouns.txt","r") as n:
    nouns = [line.rstrip('\n') for line in n]
    
with open("adjectives.txt","r") as a:
    adjectives = [line.rstrip('\n') for line in a]
    
print "Enter a subject for the story."
subject = raw_input(">")

print "How many lines long do you want your story to be?"
while True:
    try:
        lines = int(raw_input("> "))
        break
    except ValueError:
        print "Oops! That wasn't a number I recognize. Try again."

if lines <= 0:
    print "The End"
    exit(0)

for i in range(lines):

    if nouns and adjectives:
    
        noun = nouns[randint(0,len(nouns)-1)]
        nouns.remove(noun)
        
        adj = adjectives[randint(0,len(adjectives)-1)]
        adjectives.remove(adj)
        
        if i < lines - 1:    
            print "That's not my %s. Its %s is too %s." % (subject, noun, adj)
        
        else:
            print "That's my %s! Its %s is so %s." % (subject, noun, adj)

    else:    
        print "I ran out of nouns and adjectives!"
        break