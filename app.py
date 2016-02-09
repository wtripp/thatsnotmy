import web
from random import randint

urls = (
    '/story', 'Index'
)

app = web.application(urls, globals())

render = web.template.render('templates/', base="layout")

class Index(object):
    def GET(self):
        return render.story_form()               
        
    def POST(self):
        form = web.input(subject="", lines="0")

        with open("static/nouns.txt","r") as n:
            nouns = [line.rstrip('\n') for line in n]
    
        with open("static/adjectives.txt","r") as a:
            adjectives = [line.rstrip('\n') for line in a]
        
        try:        
            form.lines = int(form.lines)
        except ValueError:
            return "Number of lines must be integer."        
        
        
        if form.lines <= 0:
            return "The End"
        else:
            story = []
            for i in range(form.lines):

                if nouns and adjectives:
                
                    noun = nouns[randint(0,len(nouns)-1)]
                    nouns.remove(noun)
                    
                    adj = adjectives[randint(0,len(adjectives)-1)]
                    adjectives.remove(adj)
                    
                    if i < form.lines - 1:    
                        story.append("That's not my %s. Its %s is too %s." % (form.subject, noun, adj))
                    
                    else:
                        story.append("That's my %s! Its %s is so %s." % (form.subject, noun, adj))

                else:    
                    story.append("I ran out of nouns and adjectives!")
                    break

        return render.index(story = story)
        
if __name__ == "__main__":
    app.run()